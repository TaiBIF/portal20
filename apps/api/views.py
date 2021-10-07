import time
import json
import datetime
import re
import random
import csv
import os
import subprocess
import requests

from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings as conf_settings
from requests.sessions import default_headers


from apps.data.models import (
    Dataset,
    DATA_MAPPING,
    DatasetOrganization,
    Taxon,
    #RawDataOccurrence,
    #SimpleData,
)
from apps.data.helpers.mod_search import (
    OccurrenceSearch,
    DatasetSearch,
    PublisherSearch,
    SpeciesSearch,
    filter_occurrence,
)

from utils.decorators import json_ret
from utils.general import get_cache_or_set
from utils.solr_query import SolrQuery
from utils.map_data import convert_grid_to_coor

from .cached import COUNTRY_ROWS, YEAR_ROWS

from conf.settings import ENV

#----------------- defaul map geojson -----------------#

default_solr = SolrQuery('taibif_occurrence')
default_solr_url = default_solr.generate_solr_url()
facet_pivot_map = 'facet.pivot=grid_x,grid_y'
default_map_url = f'{default_solr_url}&facet=true&fq=grid_x%3A%5B0%20TO%20*%5D&fq=grid_y%3A%5B0%20TO%20*%5D&{facet_pivot_map}&facet.limit=-1'
default_map_url = default_map_url.replace('rows=20','rows=0')
default_r = requests.get(default_map_url)
default_data_c = {}
if default_r.status_code == 200:
    data = default_r.json()
    default_data_c = data['facet_counts']['facet_pivot']['grid_x,grid_y']
default_map_geojson = {"type":"FeatureCollection","features":[]}
for i in default_data_c:
    current_grid_x = i['value']
    for j in i['pivot']:
        current_grid_y = j['value']
        current_count = j['count']
        current_center_x, current_center_y = convert_grid_to_coor(current_grid_x, current_grid_y)
        tmp = [{
            "type": "Feature",
            "geometry":{"type":"Point","coordinates":[current_center_x,current_center_y]},
            "properties": {
                "counts": current_count
            }
        }]
        default_map_geojson['features'] += tmp

#----------------- defaul map geojson -----------------#

def get_map_species(request):
    query_list = []
    for key, values in request.GET.lists():
        if key != 'facet':
            query_list.append((key, values))
    solr = SolrQuery('taibif_occurrence')
    solr_url = solr.generate_solr_url(request.GET.lists())
    map_url = solr_url.replace('rows=20','rows=10')
    r = requests.get(map_url)
    resp = {
        'count' :0
    }
    if r.status_code == 200:
        data = r.json()
        resp.update({'count':data['response']['numFound']})
        resp['results'] = data['response']['docs']
    
    return JsonResponse(resp)


def occurrence_search_v2(request):
    time_start = time.time()

    facet_values = []
    facet_selected = {}
    query_list = []
    for key, values in request.GET.lists():
        if key == 'facet':
            facet_values = values
        else:
            query_list.append((key, values))

    for key, values in request.GET.lists():
        if key in facet_values:
            facet_selected[key] = values

    solr = SolrQuery('taibif_occurrence', facet_values)
    req = solr.request(query_list)
    #response = req['solr_response']
    resp = solr.get_response()
    if not resp:
        return JsonResponse({
            'results': 0,
            'solr_error_msg': solr.solr_error,
            'solr_url': solr.solr_url,
            'solr_tuples': solr.solr_tuples,
        })

    # for frontend menu data sturct
    menus = solr.get_menus()
    new_menus = []
    selected_facet_menu = {}
    if len(facet_selected) >= 1:
        for key, values in facet_selected.items():
            # get each facet, count
            solr_menu = SolrQuery('taibif_occurrence', facet_values)
            tmp_query_list = query_list[:]
            tmp_query_list.remove((key, values))
            solr_menu.request(tmp_query_list)
            selected_facet_menu[key] = solr_menu.get_menus(key)

    # reset menus (prevent too less count will filter out by solr facet default limit)
    for i, v in enumerate(menus):
        key = v['key']
        if key in selected_facet_menu:
            #print ('--------', i, facet_selected[key], selected_facet_menu[key], menus[i])
            tmp_menu = selected_facet_menu[key].copy()
            tmp_menu_add = []
            for selected in facet_selected[key]:
                filtered = list(filter(lambda x: x['key'] == selected, tmp_menu['rows']))
                if len(filtered) == 0 and len(tmp_menu['rows']) > 0:
                    #print(key, selected, tmp_menu)
                    tmp_menu['rows'].pop()
                    count = 0
                    for item in menus[i]['rows']:
                        #print (key, item['key'], selected, item['count'])
                        if str(item['key']) == str(selected):
                            count = item['count']
                            break
                    tmp_menu_add.append((selected, count))
            for x in tmp_menu_add:
                tmp_menu['rows'].append({
                    'key': x[0],
                    'label': x[0],
                    'count': x[1],
                })
            # resort add add fixed menu back
            tmp_menu['rows'] = sorted(tmp_menu['rows'], key=lambda x: x['count'], reverse=True)
            new_menus.append(tmp_menu)
        else:
            new_menus.append(menus[i])

    # month hack
    #print(new_menus)
    for menu in new_menus:
        if menu['key'] == 'month':
            month_rows = []
            for month in range(1, 13):
                count = 0
                for x in menu['rows']:
                    if str(x['key']) == str(month):
                        count = x['count']
                        break
                month_rows.append({
                    'key': str(month),
                    'label': str(month),
                    'count': count
                })
            menu['rows'] = month_rows

    resp['menus'] = new_menus

    # tree
    treeRoot = Taxon.objects.filter(rank='kingdom').all()
    treeData = [{
        'id': x.id,
        'data': {
            'name': x.get_name(),
            'count': x.count,
        },
    } for x in treeRoot]
    resp['tree'] = treeData
    if request.GET.get('debug_solr', ''):
        resp['solr_resp'] = solr.solr_response
        resp['solr_url'] = solr.solr_url,
        resp['solr_tuples'] =  solr.solr_tuples,

    resp['solr_qtime'] = req['solr_response']['responseHeader']['QTime']

    # map
    facet_pivot_map = 'facet.pivot=grid_x,grid_y'
    # print(solr.solr_url)
    if 'grid_x' in solr.solr_url:
        map_url = f'{solr.solr_url}&facet=true&{facet_pivot_map}&facet.limit=-1'
    else:
        map_url = f'{solr.solr_url}&facet=true&fq=grid_x%3A%5B0%20TO%20*%5D&fq=grid_y%3A%5B0%20TO%20*%5D&{facet_pivot_map}&facet.limit=-1'

    map_url = map_url.replace('rows=20','rows=0')
    if query_list:
        r = requests.get(map_url)
        data_c = {}
        if r.status_code == 200:
            data = r.json()
            data_c = data['facet_counts']['facet_pivot']['grid_x,grid_y']

        map_geojson = {"type":"FeatureCollection","features":[]}
        for i in data_c:
            current_grid_x = i['value']
            for j in i['pivot']:
                current_grid_y = j['value']
                current_count = j['count']
                current_center_x, current_center_y = convert_grid_to_coor(current_grid_x, current_grid_y)
                tmp = [{
                    "type": "Feature",
                    "geometry":{"type":"Point","coordinates":[current_center_x,current_center_y]},
                    "properties": {
                        "counts": current_count
                    }
                }]
                map_geojson['features'] += tmp
        resp['map_geojson'] = map_geojson
    else:
        print('yes')
        resp['map_geojson'] = default_map_geojson

    resp['elapsed'] = time.time() - time_start
    return JsonResponse(resp)


def taxon_tree_node(request, pk):
    taxon = Taxon.objects.get(pk=pk)
    children = [{
        'id':x.id,
        'data': {
            'name': x.get_name(),
            'count': x.count,
            'rank': x.rank,
        }
    } for x in taxon.children]

    data = {
        'rank': taxon.rank,
        'id': taxon.id,
        'data': {
            'name': taxon.get_name(),
            'count': taxon.count,
            'rank': taxon.rank,
        },
        'children': children,
    }
    return HttpResponse(json.dumps(data), content_type="application/json")

# DEPRICATED
#@json_ret
def search_occurrence(request, cat=''):
    has_menu = True if request.GET.get('menu', '') else False

    has_filter, q = SimpleData.public_objects.filter_by_key_values(list(request.GET.lists()))
    menu_list = []
    if has_menu:
        # TODO, normalize country data?
        #country_code_list = [x['country'] for x in q.exclude(country__isnull=True).annotate(count=Count('country')).order_by('-count')]
        #year_list = [x['year'] for x in q.exclude(year__isnull=True).annotate(count=Count('year')).all()]
        #print (country_code_list)
        #print (year_list)
        #print (q.exclude(year__isnull=True).annotate(count=Count('year')).query)
        ## year
        #q = SimpleData.objects.values('year').exclude(year__isnull=True).annotate(count=Count('year')).order_by('-count')

        dataset_menu = []
        if has_filter:
            #q_by_dataset = q.group_by_dataset(request.GET)
            q_by_dataset = q.values('taibif_dataset_name').\
                exclude(taibif_dataset_name__isnull=True).\
                annotate(count=Count('taibif_dataset_name')).\
                order_by('-count')
            dataset_menu = [{
                'label': x['taibif_dataset_name'],
                'key': x['taibif_dataset_name'],
                'count': x['count']
            } for x in q_by_dataset.all()]
        else:
            ds_list = Dataset.public_objects.values('name', 'title', 'num_occurrence').all()
            dataset_menu = [{
                'label': x['title'],
                'key': x['name'],
                'count': x['num_occurrence']
            } for x in ds_list]

        publisher_query = Dataset.objects\
                                 .values('organization','organization_verbatim')\
                                 .exclude(organization__isnull=True)\
                                 .annotate(count=Count('organization'))\
                                 .order_by('-count')
        publisher_rows = [{
            'key':x['organization'],
            'label':x['organization_verbatim'],
            'count': x['count']
        } for x in publisher_query]

        menu_list = [
            {
            'key': 'countrycode',
                'label': '國家/區域',
                'rows': [{'label': x['label'], 'key': x['label'] } for x in COUNTRY_ROWS]
            },
            {
                'key': 'year',
                'label': '年份',
                'rows': YEAR_ROWS
            },
            {
                'key': 'month',
                'label': '月份',
                'rows': [{'label': '{}月'.format(x),'key': x} for x in range(1, 13)]
            },
            {
                'key': 'dataset',
                'label': '資料集',
                'rows': dataset_menu,
            },
            {
                'key':'publisher',
                'label': '發布者',
                'rows': publisher_rows
            }
        ]

    # search
    occur_search = OccurrenceSearch(list(request.GET.lists()), using='')
    res = {}

    if cat in ['search', 'download']:
        res = occur_search.get_results()
    elif cat == 'taxonomy':
        taxon_num_list = []
        def _get_taxon_num(q):
            rank_list = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']
            data = []
            for r in rank_list:
                field_name = 'taxon_{}_id'.format(r)
                # TODO: exclude is null
                num = q.values(field_name).exclude().annotate(count=Count(field_name)).count()
                #print (r, num)
                data.append(num)
            return data

        if not has_filter:
            key = 'occurrence_all_taxonomy'
            if value:= cache.get(key):
                taxon_num_list = value
            else:
               taxon_num_list = _get_taxon_num(q)
               cache.set(key, taxon_num_list, 2592000)
               #taxon_num_list = get_cache_or_set(, ) # 無效 why?
        else:
            taxon_num_list = _get_taxon_num(q)

        res['taxon_num_list'] = taxon_num_list

    elif cat == 'gallery':
        pass
        #taibif_ids = q.values('taibif_id').all()
        #RawOccurrenceData.public_objects.values('associatedmedia').filter(id__in=taibif_ids).all()
    elif cat == 'charts':
        #occur_search.limit = 1 #
        #res = occur_search.get_results()
        chart = request.GET.get('chart', '')
        data = []
        #print (chart, has_filter)
        if chart == 'year':
            def _group_by_year(q):
                q_by_cat = q.values('year') \
                            .exclude(year__isnull=True) \
                            .annotate(count=Count('year')) \
                            .order_by('-year')
                return list(q_by_cat.all())

            if not has_filter:
                #data = get_cache_or_set('occurrence_all_by_year', _group_by_year(q))
                key = 'occurrence_all_by_year'
                if value:= cache.get(key):
                    data = value
                else:
                    data = _group_by_year(q)
                    cache.set(key, data, 2592000)
            else:
                data = _group_by_year(q)

            res = [
                [i['year'] for i in data],
                [i['count'] for i in data]
            ]
        elif chart == 'month':
            def _group_by_month(q):
                q_by_cat = q.values('month') \
                            .filter(month__in=list(range(1,13))) \
                            .exclude(year__isnull=True) \
                            .annotate(count=Count('month')) \
                            .order_by('month')
                return list(q_by_cat.all())

            if not has_filter:
                #data = get_cache_or_set('occurrence_all_by_month', _group_by_month(q))
                key = 'occurrence_all_by_month'
                if value:= cache.get(key):
                    data = value
                else:
                    data = _group_by_month(q)
                    cache.set(key, data, 2592000)
            else:
                data = _group_by_month(q)

            res = [
                [i['month'] for i in data],
                [i['count'] for i in data]
            ]

        elif chart == 'dataset':
            if not has_filter:
                data = Dataset.public_objects.values('title', 'num_occurrence').order_by('-num_occurrence').all()[0:10]
                res = list(data)

            else:
                #if cached := cache.get('occurrence_all_by_dataset'):
                #    res = cached
                #else:
                q_by_cat = q.values('taibif_dataset_name') \
                            .annotate(count=Count('taibif_dataset_name')) \
                            .order_by('-count')
                dataset = Dataset.public_objects.values('title', 'name').all()
                dataset_map = {i['name']: i['title']for i in dataset}
                data = list(q_by_cat.all()[0:10])
                print (q_by_cat.query)
                res = [{
                    'title': dataset_map[i['taibif_dataset_name']],
                    'num_occurrence': i['count']} for i in data]
                #cache.set('occurrence_all_by_dataset', res)

    #elif cat == 'taxonomy':
    #    occur_taxonomy = OccurrenceSearch(list(request.GET.lists()), using='')
        #occur_taxonomy.limit = 200
        #q = occur_taxonomy.query
        #q = q.values('year').annotate(count=Count('year')).order_by('year')
        #print (len(q.all()))
        #q = q.values('month').annotate(count=Count('month')).order_by('month')
        #print (q.all())
        #res = occur_taxonomy.get_results()
    data = {
        'search': res,
    }

    if has_menu:
        data['menus'] = menu_list
        # tree
        treeRoot = Taxon.objects.filter(rank='kingdom').all()
        treeData = [{
            'id': x.id,
            'data': {
                'name': x.get_name(),
                'count': x.count,
            },
        } for x in treeRoot]
        data['tree'] = treeData

    #return {'data': data}
    return HttpResponse(json.dumps(data), content_type="application/json")

#@json_ret
def search_dataset(request):
    has_menu = True if request.GET.get('menu', '') else False
    menu_list = []

    ds_search = DatasetSearch(list(request.GET.lists()))
    if has_menu:

        #publisher_query = Dataset.objects\
        publisher_query = ds_search.query\
            .values('organization','organization_name')\
            .exclude(organization__isnull=True)\
            .annotate(count=Count('organization'))\
            .order_by('-count')
        #publisher_query = publisher_query.filter()
        #publisher_query = ds_search.query.values('organization','organization_verbatim')\
        #                                 .exclude(organization__isnull=True)\
        #                                 .annotate(count=Count('organization'))\
        #                                 .order_by('-count')
        # 
        #print (publisher_query)    
        #for x in publisher_query : 
        #    print('===========',x)
        publisher_rows = [{
            'key':x['organization'],
            'label':x['organization_name'],
            'count': x['count']
        } for x in publisher_query]


        rights_query = ds_search.query\
            .values('data_license')\
            .exclude(data_license__exact='')\
            .annotate(count=Count('data_license'))\
            .order_by('-count')
        rights_rows = [{
            'key': DATA_MAPPING['rights'][x['data_license']],
            'label':DATA_MAPPING['rights'][x['data_license']],
            'count': x['count']
        } for x in rights_query]


        country_query = ds_search.query\
            .values('country')\
            .exclude(country__exact='')\
            .annotate(count=Count('country'))\
            .order_by('-count')
        country_rows = [{
            'key':x['country'],
            'label':DATA_MAPPING['country'][x['country']],
            'count': x['count']
        } for x in country_query]

        menu_list = [
            {
                'key':'publisher',
                'label': '發布者',
                'rows': publisher_rows
            },
            {
                'key': 'country',
                'label': '分布地區/國家',
                'rows': country_rows
            },
            {
                'key': 'rights',
                'label': '授權狀態',
                'rows': rights_rows
            }
        ]

    # search
    res = ds_search.get_results()

    data = {
        'search': res,
    }
    if has_menu:
        data['menus'] = menu_list
    #return {'data': data}
    return HttpResponse(json.dumps(data), content_type="application/json")

#@json_ret
def search_publisher(request):
    has_menu = True if request.GET.get('menu', '') else False
    menu_list = []

    if has_menu:
        country_list = DatasetOrganization.objects\
                                          .values('country_code')\
                                          .exclude(country_code__isnull=True)\
                                          .annotate(count=Count('country_code'))\
                                          .order_by('-count').all()
        menu_list = [
            {
                'key': 'countrycode',
                'label': '國家/區域',
                'rows': [{'label': DATA_MAPPING['country'][x['country_code']], 'count': x['count'], 'key': x['country_code'] } for x in country_list]
            },
        ]

        menus = [
            {
                'key': 'country_code',
                'label': '國家/區域',
                'rows': [{'label': DATA_MAPPING['country'][x['country_code']], 'key': x['country_code'], 'count': x['count']} for x in country_list]
            },
        ]

    # search
    publisher_search = PublisherSearch(list(request.GET.lists()))
    res = publisher_search.get_results()

    data = {
        'search': res,
    }

    if has_menu:
        data['menus'] = menu_list

    #return {'data': data }
    return HttpResponse(json.dumps(data), content_type="application/json")

#@json_ret
def search_species(request):
    status = request.GET.get('status', '')
    rank = request.GET.get('rank', '')
    print (status)

    species_search = SpeciesSearch(list(request.GET.lists()))
    #species_ids = list(species_search.query.values('id').all())
    #print (species_ids, len(species_ids))
    has_menu = True if request.GET.get('menu', '') else False
    menu_list = []
    if has_menu:
        menus = [
            # {
            #     'key': 'highertaxon',
            #     'label': '高階分類群',
            #     'rows': [{
            #         'key': x.id,
            #         'label': x.get_name(),
            #     } for x in Taxon.objects.filter(rank='kingdom')],
            # },
            {
                'key': 'rank',
                'label': '分類位階',
                'rows': [{
                    'key': x['key'],
                    'label': x['label'],
                } for x in Taxon.get_tree(rank=rank, status=status)]
            },
            {
                'key': 'status',
                'label': '狀態',
                'rows': [
                    {'label': '有效的', 'key': 'accepted'},
                    {'label': '同物異名', 'key': 'synonym'}
                ]
            },
            
        ]

    # search
    res = species_search.get_results()
    data = {
        'search': res,
    }
    if has_menu:
        data['menus'] = menus

    #return {'data': data }
    return HttpResponse(json.dumps(data), content_type="application/json")

def data_stats(request):
    '''for D3 charts'''
    is_most = request.GET.get('most', '')
    current_year = datetime.datetime.now().year

    query = Dataset.objects
    if is_most:
        query = query.filter(is_most_project=True)
    rows = query.all()

    hdata = {}
    current_year_data = {
        'dataset': [{'x': '{}月'.format(x), 'y': 0} for x in range(1, 13)],
        'occurrence': [{'x': '{}月'.format(x), 'y': 0} for x in range(1, 13)]
    }
    history_data = {
        'dataset': [],
        'occurrence': []
    }
    for i in rows:
        if not i.pub_date:
            continue

        y = str(i.pub_date.year)
        if str(current_year) == y:
            m = i.pub_date.month
            current_year_data['dataset'][m-1]['y'] += 1
            current_year_data['occurrence'][m-1]['y'] += i.num_occurrence
        if y not in hdata:
            hdata[y] = {
                'dataset': 0,
                'occurrence': 0
            }
        else:
            hdata[y]['dataset'] += 1
            hdata[y]['occurrence'] += i.num_occurrence

    #print (hdata)
    sorted_year = sorted(hdata)
    accu_ds = 0
    accu_occur = 0
    for y in sorted_year:
        accu_occur += hdata[y]['occurrence']
        accu_ds += hdata[y]['dataset']
        history_data['dataset'].append({
            'year': int(y),
            'y1': hdata[y]['dataset'],
            'y2': accu_ds
        })
        history_data['occurrence'].append({
            'year': int(y),
            'y1': hdata[y]['occurrence'],
            'y2': accu_occur
        })
    data = {
        'current_year': current_year_data,
        'history': history_data,
    }

    return HttpResponse(json.dumps(data), content_type="application/json")


@json_ret
def species_detail(request, pk):
    taxon = Taxon.objects.get(pk=pk)
    #rows = RawDataOccurrence.objects.values('taibif_dataset_name', 'decimallatitude', 'decimallongitude').filter(scientificname=taxon.name).all()
    scname = '{} {}'.format(taxon.parent.name, taxon.name)
    return {'data': {} }




## Kuan-Yu added for API occurence record

###example
filt1 = 'speices'
filt2 = 'database'
pk1 = 'Rana latouchii'
pk2 = 'manager_17_15'
pk3 = 'Rana longicrus'
pk4 = 'e10100001_4_10'



def ChartYear(request):

    if filt1 == 'hi':
        species = SimpleData.objects.filter(Q(scientific_name=pk1) | Q(scientific_name=pk3))
        sp_year = species.values('year') \
            .exclude(year__isnull=True) \
            .annotate(count=Count('year')) \
            .order_by('-year')

        chart_year = [
            {
                "page": 1,
                "pages": 1,
                "per_page": "50",
                "total": 1
            },
            [
                {
                    'year': x['year'],
                    'count': x['count']
                } for x in sp_year
            ]
        ]

    if filt2 == 'you':

        dataset = SimpleData.objects.filter(Q(taibif_dataset_name=pk2) | Q(taibif_dataset_name=pk4))
        data_year = dataset.values( 'year') \
            .exclude(year__isnull=True) \
            .annotate(count=Count('year')) \
            .order_by('-year')
        chart_year = [
            {
                "page": 1,
                "pages": 1,
                "per_page": "50",
                "total": 1
            },
            [
                {
                    'year': x['year'],
                    'count': x['count']
                } for x in data_year
            ]
        ]

    if (filt2 == filt2 and filt1 == filt1):

        data_sp = SimpleData.objects.filter(Q(scientific_name=pk1) | Q(scientific_name=pk3)) \
            .filter(Q(taibif_dataset_name=pk2) | Q(taibif_dataset_name=pk4))

        data_sp_month = data_sp.values('year') \
            .exclude(year__isnull=True) \
            .annotate(count=Count('year')) \
            .order_by('-year')

        chart_year = [
            {
                "page": 1,
                "pages": 1,
                "per_page": "50",
                "total": 1
            },
            [
                {
                    'year': x['year'],
                    'count': x['count']
                } for x in data_sp_month
            ]
        ]


    return HttpResponse(json.dumps(chart_year), content_type="application/json")


def ChartMonth(request):

    if filt1 == 'hi':

        species = SimpleData.objects.filter(Q(scientific_name=pk1) | Q(scientific_name=pk3))
        sp_month = species.values( 'month') \
            .exclude(month__isnull=True) \
            .annotate(count=Count('month')) \
            .order_by('-month')


        chart_month = [
            {
                "page": 1,
                "pages": 1,
                "per_page": "50",
                "total": 1
            },
            [
                {
                    'month': x['month'],
                    'count': x['count']
                } for x in sp_month
            ]
        ]



    if filt2 == 'you':

        dataset = SimpleData.objects.filter(Q(taibif_dataset_name=pk2) | Q(taibif_dataset_name=pk4))

        data_month = dataset.values('month') \
            .exclude(month__isnull=True) \
            .annotate(count=Count('month')) \
            .order_by('-month')

        chart_month = [
            {
                "page": 1,
                "pages": 1,
                "per_page": "50",
                "total": 1
            },
            [
                {
                    'month': x['month'],
                    'count': x['count']
                } for x in data_month
            ]
        ]

    if (filt2 == filt2 and filt1 == filt1):

        data_sp = SimpleData.objects.filter(Q(scientific_name=pk1) | Q(scientific_name=pk3)) \
            .filter(Q(taibif_dataset_name=pk2) | Q(taibif_dataset_name=pk4))

        data_sp_month = data_sp.values('month') \
            .exclude(month__isnull=True) \
            .annotate(count=Count('month')) \
            .order_by('-month')

        chart_month = [
            {
                "page": 1,
                "pages": 1,
                "per_page": "50",
                "total": 1
            },
            [
                {
                    'month': x['month'],
                    'count': x['count']
                } for x in data_sp_month
            ]
        ]



    return HttpResponse(json.dumps(chart_month), content_type="application/json")


def taxon_bar(request):

    ## Use species find
    if filt1 == 'hi':

        species = SimpleData.objects.filter(Q(scientific_name=pk1)).values('taxon_genus_id','taxon_species_id')
        sp_id = species.annotate(sp_c=Count('taxon_species_id')) \
            .aggregate(Sum('sp_c')).get('sp_c__sum')
        sp_none = species.exclude(Q(taxon_genus_id__isnull=True) | Q(taxon_species_id__isnull=True))[:1]
        ss = {'count': sp_id}



        genus = SimpleData.objects.filter(Q(taxon_genus_id=sp_none[0]['taxon_genus_id'])).values('taxon_family_id','taxon_genus_id')
        ge_id = genus.annotate(genus_c=Count('taxon_genus_id')) \
            .aggregate(Sum('genus_c')).get('genus_c__sum')
        ge_none = genus.exclude(Q(taxon_genus_id__isnull=True) | Q(taxon_family_id__isnull=True))[:1]
        gg = {'count':ge_id}



        family = SimpleData.objects.filter(Q(taxon_family_id=ge_none[0]['taxon_family_id'])).values('taxon_order_id','taxon_family_id')
        fam_id = family.annotate(fam_c=Count('taxon_family_id')) \
            .aggregate(Sum('fam_c')).get('fam_c__sum')
        fam_none = family.exclude(Q(taxon_order_id__isnull=True) | Q(taxon_family_id__isnull=True))[:1]
        ff = {'count': fam_id}


        order = SimpleData.objects.filter(Q(taxon_order_id=fam_none[0]['taxon_order_id'])).values('taxon_class_id', 'taxon_order_id')
        ord_id = order.annotate(ord_c=Count('taxon_order_id')) \
            .aggregate(Sum('ord_c')).get('ord_c__sum')
        ord_none = order.exclude(Q(taxon_order_id__isnull=True) | Q(taxon_class_id__isnull=True))[:1]
        oo = {'count': ord_id}


        clas = SimpleData.objects.filter(Q(taxon_class_id=ord_none[0]['taxon_class_id'])).values( 'taxon_phylum_id', 'taxon_class_id')
        clas_id = clas.annotate(clas_c=Count('taxon_class_id')) \
            .aggregate(Sum('clas_c')).get('clas_c__sum')
        clas_none = clas.exclude(Q(taxon_order_id__isnull=True) | Q(taxon_phylum_id__isnull=True))[:1]

        cc = {'count': clas_id}


        phylum = SimpleData.objects.filter(Q(taxon_phylum_id=clas_none[0]['taxon_phylum_id'])).values('taxon_kingdom_id', 'taxon_phylum_id')
        phy_id = phylum.annotate(phyl_c=Count('taxon_phylum_id')) \
            .aggregate(Sum('phyl_c')).get('phyl_c__sum')
        phy_none = phylum.exclude(Q(taxon_kingdom_id__isnull=True) | Q(taxon_phylum_id__isnull=True))[:1]

        pp = {'count': phy_id}


        king = SimpleData.objects.filter(Q(taxon_kingdom_id=phy_none[0]['taxon_kingdom_id'])).values('taxon_kingdom_id')
        king_id = king.annotate(king_c=Count('taxon_kingdom_id')) \
            .aggregate(Sum('king_c')).get('king_c__sum')
        kk = {'count': king_id}

    ## Ude dataset and species search
    if (filt2 == filt2 and filt1 == filt1):

        species = SimpleData.objects.filter(Q(scientific_name=pk1) | Q(taibif_dataset_name=pk2)).values('taxon_genus_id','taxon_species_id')
        sp_id = species.annotate(sp_c=Count('taxon_species_id')) \
            .aggregate(Sum('sp_c')).get('sp_c__sum')
        sp_none = species.exclude(Q(taxon_genus_id__isnull=True) | Q(taxon_species_id__isnull=True))[:1]
        ss = {'count': sp_id}

        genus = SimpleData.objects.filter(Q(taxon_genus_id=sp_none[0]['taxon_genus_id']) | Q(taibif_dataset_name=pk2)).values('taxon_family_id',
                                                                                                 'taxon_genus_id')
        ge_id = genus.annotate(genus_c=Count('taxon_genus_id')) \
            .aggregate(Sum('genus_c')).get('genus_c__sum')
        ge_none = genus.exclude(Q(taxon_genus_id__isnull=True) | Q(taxon_family_id__isnull=True))[:1]
        gg = {'count': ge_id}

        family = SimpleData.objects.filter(Q(taxon_family_id=ge_none[0]['taxon_family_id']) | Q(taibif_dataset_name=pk2)).values('taxon_order_id',
                                                                                                    'taxon_family_id')
        fam_id = family.annotate(fam_c=Count('taxon_family_id')) \
            .aggregate(Sum('fam_c')).get('fam_c__sum')
        fam_none = family.exclude(Q(taxon_order_id__isnull=True) | Q(taxon_family_id__isnull=True))[:1]
        ff = {'count': fam_id}

        order = SimpleData.objects.filter(Q(taxon_order_id=fam_none[0]['taxon_order_id']) | Q(taibif_dataset_name=pk2)).values('taxon_class_id',
                                                                                                  'taxon_order_id')
        ord_id = order.annotate(ord_c=Count('taxon_order_id')) \
            .aggregate(Sum('ord_c')).get('ord_c__sum')
        ord_none = order.exclude(Q(taxon_order_id__isnull=True) | Q(taxon_class_id__isnull=True))[:1]
        oo = {'count': ord_id}

        clas = SimpleData.objects.filter(Q(taxon_class_id=ord_none[0]['taxon_class_id']) | Q(taibif_dataset_name=pk2)).values('taxon_phylum_id',
                                                                                                 'taxon_class_id')
        clas_id = clas.annotate(clas_c=Count('taxon_class_id')) \
            .aggregate(Sum('clas_c')).get('clas_c__sum')
        clas_none = clas.exclude(Q(taxon_order_id__isnull=True) | Q(taxon_phylum_id__isnull=True))[:1]

        cc = {'count': clas_id}

        phylum = SimpleData.objects.filter(Q(taxon_phylum_id=clas_none[0]['taxon_phylum_id']) | Q(taibif_dataset_name=pk2)).values(
            'taxon_kingdom_id', 'taxon_phylum_id')
        phy_id = phylum.annotate(phyl_c=Count('taxon_phylum_id')) \
            .aggregate(Sum('phyl_c')).get('phyl_c__sum')
        phy_none = phylum.exclude(Q(taxon_kingdom_id__isnull=True) | Q(taxon_phylum_id__isnull=True))[:1]

        pp = {'count': phy_id}

        king = SimpleData.objects.filter(Q(taxon_kingdom_id=phy_none[0]['taxon_kingdom_id']) | Q(taibif_dataset_name=pk2)).values('taxon_kingdom_id')
        king_id = king.annotate(king_c=Count('taxon_kingdom_id')) \
            .aggregate(Sum('king_c')).get('king_c__sum')
        kk = {'count': king_id}




    data = [
            {
                "page": 1,
                "pages": 1,
                "per_page": "50",
                "total": 1
            },
            [
                ss,gg,ff,oo,cc,pp,kk
            ]
        ]



    return HttpResponse(json.dumps(data), content_type="application/json")

#------- DEPRECATED ------#

def search_occurrence_v1_charts(request):
    year_start = 1000
    year_end = 2021

    solr_q_fq_list=[]
    solr_fq = ''
    solr_q_list = []
    solr_q = '*:*'
    # print (list(request.GET.lists()))
    for term, values in list(request.GET.lists()):
        if term !='q' :
            if term != 'menu':
                if term =='year':
                    val = values[0].replace(",", " TO ")
                    solr_q_fq_list.append('{}:[{}]'.format(term,val))
                    year_start =values[0].split(',',1)
                    year_end =values[0].split(',',2)
                elif term =='dataset':
                    solr_q_fq_list.append('{}:"{}"'.format('taibif_dataset_name_zh', '" OR "'.join(values)))
                elif term =='month':
                    solr_q_fq_list.append('{}:{}'.format(term, ' OR '.join(values)))
                elif term =='country':
                    solr_q_fq_list.append('{}:{}'.format(term, ' OR '.join(values)))
                elif term =='publisher':
                    solr_q_fq_list.append('{}:{}'.format(term, ' OR '.join(values)))

        else:
            solr_q_list.append('{}:{}'.format('_text_', ' OR '.join(values)))


    if len(solr_q_list) > 0:
        solr_q = ' AND '.join(solr_q_list)

    if len(solr_q_fq_list) > 0:
        solr_fq = ' AND '.join(solr_q_fq_list)
    print(solr_fq)

    charts_year = []
    charts_month = []
    charts_dataset = []

    search_count = 0
    search_offset = 0
    search_results = []
    

    time_start = time.time()  
    facet_dataset = 'dataset:{type:terms,field:taibif_dataset_name_zh,limit:-1,mincount:0}'
    facet_month = 'month:{type:range,field:month,start:1,end:13,gap:1}'
    facet_year = 'year:{type:terms,field:year,limit:-1,mincount:0}'
    facet_json = 'json.facet={'+facet_dataset + ',' +facet_month+ ',' +facet_year+'}'
    r = requests.get(f'http://solr:8983/solr/taibif_occurrence/select?facet=true&q.op=OR&q={solr_q}&fq={solr_fq}&{facet_json}')

    if r.status_code == 200:
        data = r.json()


        search_count = data['response']['numFound']
        
        if search_count != 0:
            search_offset = data['response']['start']
            search_results = data['response']['docs']

            charts_year =[{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['facets']['year']['buckets']]
            charts_month = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['facets']['month']['buckets']]
            charts_dataset = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['facets']['dataset']['buckets']]
        else:
            charts_year = [{'key': 0, 'label': 0, 'count': 0}]
            charts_month = [{'key': 0, 'label': 0, 'count': 0}]
            charts_dataset = [{'key': 0, 'label': 0, 'count': 0}]



    ret = {
        'charts': [
            {
                'key': 'year',
                'label': '年份',
                'rows': charts_year,
            },
            {
                'key': 'month',
                'label': '月份',
                'rows': charts_month,
            },
            {
                'key': 'dataset',
                'label': '資料集',
                'rows': charts_dataset,
            },
        ],
    }
    return JsonResponse(ret)






def search_occurrence_v1(request):
    year_start = 1000
    year_end = 2021

    solr_q_fq_list=[]
    solr_fq = ''
    solr_q_list = []
    solr_q = '*:*'
    for term, values in list(request.GET.lists()):
        if term !='q' :
            if term != 'menu':
                if term =='year':
                    val = values[0].replace(",", " TO ")
                    solr_q_fq_list.append('{}:[{}]'.format(term,val))
                    year_start =values[0].split(',',1)
                    year_end =values[0].split(',',2)
                elif term =='dataset':
                    solr_q_fq_list.append('{}:"{}"'.format('taibif_dataset_name_zh', '" OR "'.join(values)))
                elif term =='month':
                    solr_q_fq_list.append('{}:{}'.format(term, ' OR '.join(values)))

        else:
            solr_q_list.append('{}:{}'.format('_text_', ' OR '.join(values)))


    if len(solr_q_list) > 0:
        solr_q = ' OR '.join(solr_q_list)

    if len(solr_q_fq_list) > 0:
        solr_fq = ' OR '.join(solr_q_fq_list)

    menu_year = []
    menu_month = []
    menu_dataset = []
    menu_country = []
    menu_publisher = []

    search_count = 0
    search_limit = 20
    search_offset = 0
    search_results = []
    #publisher_query = Dataset.objects\
    #                         .values('organization','organization_verbatim')\
    #                         .exclude(organization__isnull=True)\
    #                         .annotate(count=Count('organization'))\
    #                         .order_by('-count')
    #menu_publisher = [{
    #    'key':x['organization'],
    #    'label':x['organization_verbatim'],
    #    'count': x['count']
    #} for x in publisher_query]
    
    

    time_start = time.time()  
    facet_dataset = 'dataset:{type:terms,field:taibif_dataset_name_zh}'
    facet_month = 'month:{type:range,field:month,start:1,end:13,gap:1}'
    facet_country = 'country:{type:terms,field:country,mincount:0,limit:-1}'
    facet_publisher = 'publisher:{type:terms,field:publisher}'
    facet_json = 'json.facet={'+facet_dataset + ',' +facet_month+ ',' +facet_country+','+facet_publisher+'}'
    r = requests.get(f'http://solr:8983/solr/taibif_occurrence/select?facet=true&q.op=OR&rows={search_limit}&q={solr_q}&fq={solr_fq}&{facet_json}')

    if r.status_code == 200:
        data = r.json()
        search_count = data['response']['numFound']
        if search_count != 0:
            search_offset = data['response']['start']
            search_results = data['response']['docs']
            for i, v in enumerate(search_results):
            ## copy fields
                date = '{}-{}-{}'.format(v['year'] if v.get('year', '') else '',
                                        v['month'] if v.get('month', '') else '',
                                        v['day'] if v.get('day', '') else '')
                search_results[i]['vernacular_name'] = v.get('vernacularName', '')
                search_results[i]['scientific_name'] = v.get('scientificName', '')
                search_results[i]['dataset'] = v['taibif_dataset_name']
                search_results[i]['date'] = date
                search_results[i]['taibif_id'] = '{}__{}'.format(v['taibif_dataset_name'], v['_version_'])
                search_results[i]['kingdom'] = v.get('kingdom_zh', '')
                search_results[i]['phylum'] = v.get('phylum_zh', '')
                search_results[i]['class'] = v.get('class_zh', '')
                search_results[i]['order'] = v.get('order_zh', '')
                search_results[i]['family'] = v.get('family_zh', '')
                search_results[i]['genus'] = v.get('genus_zh', '')
                search_results[i]['species'] = v.get('species_zh', '')

            menu_year = [{'key': 0, 'label': 0, 'count': 0,'year_start':year_start,'year_end':year_end}]
            menu_month = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['facets']['month']['buckets']]
            menu_dataset = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['facets']['dataset']['buckets']]
            menu_country = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['facets']['country']['buckets']]
            menu_publisher = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['facets']['publisher']['buckets']]
        else:
            menu_year = [{'key': 0, 'label': 0, 'count': 0,'year_start':year_start,'year_end':year_end}]
            menu_month = [{'key': x, 'label': x, 'count': 0} for x in range(12)]
            menu_dataset = [{'key': 0, 'label': 0, 'count': 0}]
            menu_country = [{'key': 0, 'label': 0, 'count': 0}]
            menu_publisher = [{'key': 0, 'label': 0, 'count': 0}]
        

        #search_limit = 20
        
    ret = {
        'menus': [
            {
                'key': 'country', #'countrycode',
                'label': '國家/區域',
                'rows': menu_country,
            },
            {
                'key': 'year',
                'label': '年份',
                'rows': menu_year,
            },
            {
                'key': 'month',
                'label': '月份',
                'rows': menu_month,
            },
            {
                'key': 'dataset',
                'label': '資料集',
                'rows': menu_dataset,
            },
            {
                'key':'publisher',
                'label': '發布者',
                'rows': menu_publisher,
            }
        ],
        'search': {
            'elapsed': time.time() - time_start,
            'results': search_results,
            'offset': search_offset,
            'limit': search_limit,
            'count': search_count,
            'has_more': True
        },
    }

    # tree
    treeRoot = Taxon.objects.filter(rank='kingdom').all()
    treeData = [{
        'id': x.id,
        'data': {
            'name': x.get_name(),
            'count': x.count,
        },
    } for x in treeRoot]
    ret['tree'] = treeData
    return JsonResponse(ret)

def export(request):
    search_count = 0
    solr = SolrQuery('taibif_occurrence')
    solr_url = solr.generate_solr_url(request.GET.lists())
    
    if len(solr_url) > 0:
        generateCSV(solr_url,request)

    return JsonResponse({"status":search_count}, safe=False)

def generateCSV(solr_url,request):

    #directory = os.path.abspath(os.path.join(os.path.curdir))
    #taibifVolumesPath = '/taibif-volumes/media/'
    #csvFolder = directory+taibifVolumesPath
    CSV_MEDIA_FOLDER = 'csv'
    csvFolder = os.path.join(conf_settings.MEDIA_ROOT, CSV_MEDIA_FOLDER)
    timestramp = str(int(time.time()))
    filename = timestramp +'.csv'
    downloadURL = '没有任何資料'
    csvFilePath = os.path.join(csvFolder, filename)

    if not os.path.exists(csvFolder):
        os.makedirs(csvFolder)

    if len(solr_url) > 0:

        downloadURL = request.scheme+"://"+request.META['HTTP_HOST']+conf_settings.MEDIA_URL+os.path.join(CSV_MEDIA_FOLDER, filename)
        #print("curl "+f'"{solr_url}"'+" > "+csvFolder+filename)

        result = subprocess.Popen("curl "+f'"{solr_url}"'+" > "+csvFilePath, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    sendMail(downloadURL,request)

def sendMail(downloadURL,request):
    subject = '出現紀錄搜尋'


    currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    searchCondition = request.GET["search_condition"]

    html = f"""\
<html>
  <head></head>
  <body style='text-align:left'>
您好，
<br/><br/>
您在TaiBIF上查詢的檔案已夾帶於附件中，

<br/><br/>
檔案相關的詳細說明為：

<br/><br/>
搜尋條件：{searchCondition}


<br/>
搜尋時間：{currentTime}

<br/><br/>
檔案類型：CSV

<br/><br/>
授權條款：授權條款有兩個來源<br/>
資料集（postgre : dataset.data_license）<br/>
資料集內部的單筆資料(solr : license)<br/>
授權有四個要素 BY, SA, ND, DC<br/>
因此，要確認這兩個欄位的有哪些要素，有的話就需要顯示，若都沒有先以「未明確授權」顯示<br/>
https://zh.wikipedia.org/wiki/%E7%9F%A5%E8%AF%86%E5%85%B1%E4%BA%AB%E8%AE%B8%E5%8F%AF%E5%8D%8F%E8%AE%AE

<br/><br/>
使用條款：

<br/><br/>
下載鏈結：<a href="{downloadURL}">{downloadURL}</a>

<br/><br/>
若有問題再麻煩您回覆至

<br/><br/>
taibif.brcas@gmail.com

<br/><br/>
TaiBIF團隊 敬上
  </body>
</html>
"""

    send_mail(
        subject,
        None,
        conf_settings.TAIBIF_SERVICE_EMAIL,
        [request.GET["email"]],
        html_message=html)


# def search_occurrence_v2_map(request):
#     time_start = time.time()
#     facet_values = []
#     query_list = []
#     for key, values in request.GET.lists():
#         if key == 'facet':
#             facet_values = values
#         else:
#             query_list.append((key, values))
#     solr = SolrQuery('taibif_occurrence')
#     req = solr.request(query_list)
#     #response = req['solr_response']
#     resp = solr.get_response()
#     if not resp:
#         return JsonResponse({
#             'results': 0,
#             'solr_error_msg': solr.solr_error,
#             'solr_url': solr.solr_url,
#             'solr_tuples': solr.solr_tuples,
#         })

#     solr_menu = SolrQuery('taibif_occurrence', facet_values)
#     solr_menu.request()
#     resp_menu = solr_menu.get_response()

#     # for frontend menu data sturctt
#     menus = []
#     if resp_menu['facets']:
#         if data := resp_menu['facets'].get('country', ''):
#             rows = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['buckets']]
#             menus.append({
#                 'key': 'country', #'countrycode',
#                 'label': '國家/區域',
#                 'rows': rows,
#             })
#         if data := resp_menu['facets'].get('year', ''):
#             #menu_year = [{'key': 0, 'label': 0, 'count': 0,'year_start':1990,'year_end':2021}]
#             # TODO
#             menus.append({
#                 'key': 'year',
#                 'label': '年份',
#                 'rows': ['FAKE_FOR_SPACE',],
#             })
#         if data := resp_menu['facets'].get('month', ''):
#             rows = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in sorted(data['buckets'], key=lambda x: x['val'])]
#             menus.append({
#                 'key': 'month',
#                 'label': '月份',
#                 'rows': rows,
#             })
#         if data := resp_menu['facets'].get('dataset', ''):
#             rows = menu_dataset = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['buckets']]
#             menus.append({
#                 'key': 'dataset',
#                 'label': '資料集',
#                 'rows': rows,
#             })
#         if data := resp_menu['facets'].get('publisher', ''):
#             rows = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['buckets']]
#             menus.append({
#                 'key':'publisher',
#                 'label': '發布者',
#                 'rows': rows,
#             })

#     resp['menus'] = menus

#     # tree
#     treeRoot = Taxon.objects.filter(rank='kingdom').all()
#     treeData = [{
#         'id': x.id,
#         'data': {
#             'name': x.get_name(),
#             'count': x.count,
#         },
#     } for x in treeRoot]
#     resp['tree'] = treeData
#     if request.GET.get('debug_solr', ''):
#         resp['solr_resp'] = solr.solr_response
#         resp['solr_url'] = solr.solr_url,
#         resp['solr_tuples'] =  solr.solr_tuples,

#     resp['solr_qtime'] = req['solr_response']['responseHeader']['QTime']
#     resp['elapsed'] = time.time() - time_start

#     # map
#     facet_pivot_map = 'facet.pivot=grid_x,grid_y'
#     # print(solr.solr_url)
#     if 'grid_x' in solr.solr_url:
#         map_url = f'{solr.solr_url}&facet=true&{facet_pivot_map}&facet.limit=-1'
#     else:
#         map_url = f'{solr.solr_url}&facet=true&fq=grid_x%3A%5B0%20TO%20*%5D&fq=grid_y%3A%5B0%20TO%20*%5D&{facet_pivot_map}&facet.limit=-1'

#     map_url = map_url.replace('rows=20','rows=0')
#     r = requests.get(map_url)
#     data_c = {}
#     if r.status_code == 200:
#         data = r.json()
#         data_c = data['facet_counts']['facet_pivot']['grid_x,grid_y']

#     map_geojson = {"type":"FeatureCollection","features":[]}
#     for i in data_c:
#         current_grid_x = i['value']
#         for j in i['pivot']:
#             current_grid_y = j['value']
#             current_count = j['count']
#             current_center_x, current_center_y = convert_grid_to_coor(current_grid_x, current_grid_y)
#             tmp = [{
#                 "type": "Feature",
#                 "geometry":{"type":"Point","coordinates":[current_center_x,current_center_y]},
#                 "properties": {
#                     "counts": current_count
#                 }
#             }]
#             map_geojson['features'] += tmp
#     resp['map_geojson'] = map_geojson

#     return JsonResponse(resp)