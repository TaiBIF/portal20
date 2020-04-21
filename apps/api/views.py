import time
import json
import datetime
import re
import random

from django.shortcuts import render
from django.db.models import Count, Q
from django.http import HttpResponse

from apps.data.models import Dataset, DATA_MAPPING, DatasetOrganization, Taxon
from apps.data.models import RawDataOccurrence
from apps.data.models import SimpleData
from apps.data.helpers.mod_search import (
    OccurrenceSearch,
    DatasetSearch,
    PublisherSearch,
    SpeciesSearch,
)

from utils.decorators import json_ret

from .cached import COUNTRY_ROWS, YEAR_ROWS


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

#@json_ret
def search_occurrence(request):
    has_menu = True if request.GET.get('menu', '') else False
    menu_list = []
    if has_menu:
        # cache
        '''query = RawDataOccurrence.objects\
                             .values('countrycode')\
                             .exclude(countrycode__isnull=True)\
                             .annotate(count=Count('countrycode'))\
                             .order_by('-count')'''

        '''year_rows = [
        {
            'label': str(year),
            'key': str(year),
            'count': 0,
        } for year in range(1909, 2021)
    ]
    year_rows_update = []
    for i in year_rows:
        r = RawDataOccurrence.objects .values('year').exclude(year__isnull=True).filter(year__icontains=i['key']).annotate(count=Count('year'))
        if len(r):
            year_rows_update.append({'label': i['key'], 'key': i['key'], 'count': r[0]['count']})
            print (i, r)
    import json
        s = json.dumps(year_rows_update)'''
        dataset_query = Dataset.objects.exclude(status='Private').values('name', 'title')
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
                'rows': [{'label': x['label'], 'count': x['count'], 'key': x['label'] } for x in COUNTRY_ROWS]
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
                'rows': [{'label': x['title'], 'key': x['name']} for x in dataset_query]
            },
            {
                'key':'publisher',
                'label': '發布者',
                'rows': publisher_rows
            }
        ]

    # search
    occur_search = OccurrenceSearch(list(request.GET.lists()), using='')
    res = occur_search.get_results()

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

    if has_menu:
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
        rights_query = Dataset.objects\
                              .values('data_license')\
                              .exclude(data_license__exact='')\
                              .annotate(count=Count('data_license'))\
                              .order_by('-count')
        rights_rows = [{
            'key': DATA_MAPPING['rights'][x['data_license']],
            'label':x['data_license'],
            'count': x['count']
        } for x in rights_query]
        country_query = Dataset.objects\
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
    ds_search = DatasetSearch(list(request.GET.lists()))
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
        #print (country_list)
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

    has_menu = True if request.GET.get('menu', '') else False
    menu_list = []
    if has_menu:
        menus = [
            {
                'key': 'rank',
                'label': '分類位階',
                'rows': [{
                    'key': x['key'],
                    'label': x['label'],
                    'count': x['count']
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
    species_search = SpeciesSearch(list(request.GET.lists()))
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
