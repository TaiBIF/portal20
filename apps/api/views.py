import time
import json
import datetime
import re
import urllib
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
from urllib.parse import quote


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
from utils.solr_query import (
    SolrQuery,
    get_init_menu,
)
from utils.map_data import convert_grid_to_coor, get_geojson, convert_x_coor_to_grid, convert_y_coor_to_grid


from .cached import COUNTRY_ROWS, YEAR_ROWS

from conf.settings import ENV

#----------------- defaul map geojson -----------------#
default_solr = SolrQuery('taibif_occurrence')
default_solr_url = default_solr.generate_solr_url()
default_map_geojson = get_geojson(default_solr_url)
cache.set('default_map_geojson', default_map_geojson, 2592000)

req = default_solr.request()
resp = default_solr.get_response()
cache.set('default_solr_count', resp['count'] if resp else 0, 2592000)

#----------------- defaul map geojson -----------------#



def search_occurrence_v1_charts(request):
    year_start = 1000
    year_end = 2021
    lat_query, lng_query = '', ''

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
                    solr_q_fq_list.append('{}:"{}"'.format('taibif_dataset_name', '" OR "'.join(values)))
                elif term =='month':
                    solr_q_fq_list.append('{}:{}'.format(term, ' OR '.join(values)))
                elif term =='country':
                    solr_q_fq_list.append('{}:{}'.format(term, ' OR '.join(values)))
                elif term =='publisher':
                    solr_q_fq_list.append('{}:{}'.format(term, ' OR '.join(values)))
                #-----map------#
                elif term == 'lat':
                    coor_list = [ float(c) for c in values]
                    y1 = convert_y_coor_to_grid(min(coor_list))
                    y2 = convert_y_coor_to_grid(max(coor_list))
                    lat_query = "&fq={!frange l=" + str(y1) + " u=" + str(y2) + "}grid_y"
                elif term == 'lng':
                    coor_list = [ float(c) for c in values]
                    x1 = convert_x_coor_to_grid(min(coor_list))
                    x2 = convert_x_coor_to_grid(max(coor_list))
                    lng_query = "&fq={!frange l=" + str(x1) + " u=" + str(x2) + "}grid_x"

        else:
            solr_q_list.append('{}:{}'.format('_text_', ' OR '.join(values)))


    if len(solr_q_list) > 0:
        solr_q = ' AND '.join(solr_q_list)

    if len(solr_q_fq_list) > 0:
        solr_fq = ' AND '.join(solr_q_fq_list)

    charts_year = []
    charts_month = []
    charts_dataset = []

    search_count = 0
    search_offset = 0
    search_results = []
    
    facet_dataset = 'dataset:{type:terms,field:taibif_dataset_name_zh,limit:-1,mincount:0}'
    facet_month = 'month:{type:range,field:month,start:1,end:13,gap:1}'
    facet_year = 'year:{type:terms,field:year,limit:-1,mincount:0}'
    facet_json = 'json.facet={'+facet_dataset + ',' +facet_month+ ',' +facet_year+'}'

    url = f'http://solr:8983/solr/taibif_occurrence/select?facet=true&q.op=AND&q={solr_q}&fq={solr_fq}&{facet_json}{lng_query}{lat_query}'
    r = requests.get(url)

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

def dataset_api(request):
    
    ds_search = DatasetSearch(list(request.GET.lists()))
    result_d =  ds_search.query.values()
    
    rows = [{
        'title' : x['title'] if 'title' in x else None,
        'name' : x['name'],
        'author' : x['author'] if 'author' in x and x['mod_date'] != None else None,
        'pub_date' : x['pub_date'].strftime("%Y-%m-%d") if 'pub_date' in x and x['pub_date'] != None else None,
        'mod_date' : x['mod_date'].strftime("%Y-%m-%d") if 'mod_date' in x and x['mod_date'] != None else None,
        'core' : x['dwc_core_type'] if 'dwc_core_type' in x else None,
        'license' : x['data_license'] if 'data_license' in x and x['data_license'] != None else 'unknown',
        'doi' : x['gbif_doi'] if 'doi' in x and x['gbif_doi'] != None else None,
        'organization_id' : x['organization_uuid'] if 'organization_uuid' in x and x['organization_uuid'] != None else None,
        'organization_name' : x['organization_name'] if 'organization_name' in x and x['organization_name'] != None else None,
        'num_record' : x['num_record'] if 'num_record' in x and x['num_record'] != None else None,
        'gbif_dataset_id' : x['guid'] if 'guid' in x and x['guid'] != None else None,
        # 'citation' : x['citation'] if 'citation' in x else None,
        # 'resource' : x['resource'] if 'resource' in x else None,
    } for x in result_d ]
    
    return HttpResponse(json.dumps(rows), content_type="application/json")
    
    

def for_basic_occ(request):
    query_list = []
    start_date = "*"
    end_date = "*"
    solr_error = ''
    solr_response = ''
    rows=10
    offset=0
    fq_query=''
    
    if request.GET.get('start_date'):
        start_date = datetime.datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').isoformat() + 'Z'
    if request.GET.get('end_date'):
        end_date = datetime.datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').isoformat() + 'Z'
        
    query_list.append(('q', f'mod_date:[{start_date} TO {end_date}]'))
    
    for key, values in request.GET.lists():
        if key == "start_date" or key == "end_date":
            continue
        elif key == "rows":
            rows = values[0]
            if int(rows)<=300:
                query_list.append((key, values[0]))
            else : 
                rows = 300
                query_list.append((key, 300))
        elif key == "offset":
            offset = values[0]
            query_list.append(('start', values[0]))
    
    
    if request.GET.get("datasetFullName"):
        fq_query = 'fq=taibif_dataset_name_zh:'+ str(request.GET.get('datasetFullName'))
    
    if request.GET.get("datasetFullName") and request.GET.get("dataset_name") :
        fq_query = fq_query + '&fq=taibif_dataset_name:'+ str(request.GET.get('dataset_name'))
    
    if not request.GET.get("datasetFullName") and request.GET.get("dataset_name") :
        fq_query = 'fq=taibif_dataset_name:'+ str(request.GET.get('dataset_name'))
    
    
    
    solr_q = urllib.parse.urlencode(query_list,quote_via=urllib.parse.quote)
    if fq_query:
        url = f'http://solr:8983/solr/taibif_occurrence/select?q.op=AND&{solr_q}&{fq_query}'
    else:
        url = f'http://solr:8983/solr/taibif_occurrence/select?q.op=AND&{solr_q}'
    
    try: 
        resp =urllib.request.urlopen(url)
        resp_dict = resp.read().decode()
        solr_response = json.loads(resp_dict)
    except urllib.request.HTTPError as e:
        solr_error = str(e)
        
    if not solr_response['response']['docs']: 
        return JsonResponse({
            'results': 0,
            'query_list': query_list,
            'error_url': url,
            'error_msg': solr_error,
        })
    res={}
    res_list=[] 
    for i in solr_response['response']['docs']:
        res_list.append({
            'occurrenceID':i['occurrenceID'],
            'scientificName': i['taibif_scientificName'] if 'taibif_scientificName' in i else (i['scientificName'] if 'scientificName' in i else ''),
            'isPreferredName': i['taibif_vernacularName'] if 'taibif_vernacularName' in i else (i['vernacularName'] if 'vernacularName' in i else ''),
            # 'sensitiveCategory':,
            # 'taxonRank':,
            'eventDate':i['taibif_event_date'][0] if 'taibif_event_date' in i else (i['eventDate'] if 'eventDate' in i else ''),
            'longitude':str(i['taibif_longitude'][0]) if 'taibif_longitude' in i  else '',
            'latitude':str(i['taibif_longitude'][0]) if 'taibif_latitude' in i  else '',
            'geodeticDatum':i['taibif_geodeticDatum'] if 'taibif_geodeticDatum' in i else '',
            # 'verbatimSRS':i['verbatimSRS'] if 'verbatimSRS' in i else '',
            'coordinateUncertaintyInMeters':i['coordinateUncertaintyInMeters'] if 'coordinateUncertaintyInMeters' in i else '',
            'dataGeneralizations':i['taibif_dataGeneralizations'] if 'taibif_dataGeneralizations' in i else (i['dataGeneralizations']  if 'dataGeneralizations' in i else ''),
            'coordinatePrecision':i['taibif_coordinatePrecision'] if 'taibif_coordinatePrecision' in i else (i['coordinatePrecision'] if 'coordinatePrecision' in i else ''),
            'locality':i['taibif_locality'] if 'taibif_locality' in i  else (i['locality'] if 'locality' in i else ''),
            'organismQuantity':i['taibif_organismQuantity'] if 'taibif_organismQuantity' in i else (i['organismQuantity'] if 'organismQuantity' in i else ''),
            'organismQuantityType':i['taibif_organismQuantityType'] if 'taibif_organismQuantityType' in i else (i['organismQuantityType'] if 'organismQuantityType' in i else ''),
            'recordedBy':i['taibif_recordedBy'] if 'taibif_recordedBy' in i else (i['recordedBy'] if 'recordedBy' in i else ''),
            # 'taxonID':,
            # 'scientificNameID':,
            'basisOfRecord':i['basisOfRecord'] if 'basisOfRecord' in i else '',
            'datasetFullName':i['taibif_dataset_name_zh'] if 'taibif_dataset_name_zh' in i else '',
            'datasetName':i['taibif_dataset_name'] if 'taibif_dataset_name' in i else '',
            # 'resourceContacts':
            # 'references':
            'license':i['taibif_license'] if 'taibif_license' in i else (i['license'] if 'license' in i else ''),
            # 'created':,
            # 'modified':,
            'mod_date':i['mod_date'][0]
        })

    res['count'] = solr_response['response']['numFound']
    res['offset'] = int(offset)
    res['rows'] = int(rows)
    res['results'] = res_list

    return JsonResponse(res)

def occurrence_search_v2(request):
    time_start = time.time()
    facet_values = []
    facet_selected = {}
    query_list = []
    is_chart = False
    if re.search("^/api/v1/occurrence/charts.*", str(request.get_full_path())) :
        is_chart = True
    
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

    # get full menu if no facet return
    if len(menus) == 0:
        menus = get_init_menu(facet_values)

    new_menus = []
    selected_facet_menu = {}
    if len(facet_selected) >= 1:
        for key, values in facet_selected.items():
            # get each facet, count
            solr_menu = SolrQuery('taibif_occurrence', facet_values)
            tmp_query_list = query_list[:]
            tmp_query_list.remove((key, values))
            solr_menu.request(tmp_query_list)
            if submenu := solr_menu.get_menus(key):
                selected_facet_menu[key] = submenu
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

                month_rows.append({
                    'key': str(month),
                    'label': str(month),
                    'count': count
                })
            menu['rows'] = month_rows

    # year hack
    #print(new_menus)
    for menu in new_menus:
        if menu['key'] == 'year':
            if is_chart != True :
                menu['rows'] = [{'key': 'fake_year_range', 'label': 'fake_year_range', 'count': 0}]
    
    # HACK, for menu items all zero:
    for menu in new_menus:
        menu_default = None
        if menu['key'] not in['month', 'year']:
            #print(menu['key'], sum([x.get('count', 0) for x in menu['rows']]))
            total = sum([x.get('count', 0) for x in menu['rows']])
            if total == 0:
                if not menu_default:
                    menu_default = get_init_menu(facet_values)
                    found = filter(lambda x: x['key'] == menu['key'], menu_default)
                    if submenu := list(found):
                        # replace submenu !!
                        menu['rows'] = submenu[0]['rows']
    #chart api return month/year/datasey facet 
    if is_chart :
        charts_year=[]
        charts_month=[]
        charts_dataset=[]
        menus = solr.get_menus()
        for menu in menus:
            if menu['key'] == 'month':
                for month in range(1, 13):
                    count = 0
                    for x in menu['rows']:
                        if str(x['key']) == str(month):
                            count = x['count']

                    charts_month.append({
                        'key': str(month),
                        'label': str(month),
                        'count': count
                    })
            if menu['key'] == 'year':
                for x in menu['rows']:
                    if int(x['key']) > 1784:
                        charts_year.append({
                        'key': x['key'],
                        'label': x['label'],
                        'count': x['count']
                    })
            if menu['key'] == 'dataset':
                for x in menu['rows']:
                    charts_dataset.append({
                        'key': x['key'],
                        'label': x['label'],
                        'count': x['count']
                    })

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

    resp['menus'] = new_menus


    # TODO, init taxon_key
    req_dict = dict(request.GET)
    taxon_key = ''
    if tkey := req_dict.get('taxon_key', ''):
        taxon_key = tkey
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
    # TODO, init taxon_key
    #resp['taxon_checked'] = tkey
    if request.GET.get('debug_solr', ''):
        resp['solr_resp'] = solr.solr_response
        resp['solr_url'] = solr.solr_url
        resp['solr_tuples'] =  solr.solr_tuples

    resp['solr_qtime'] = req['solr_response']['responseHeader']['QTime']

    #--------------- map ---------------#
    # check if solr data has been updated
    solr_updated = False if cache.get('default_solr_count') == resp['count'] else True
    if query_list: # 如果有帶篩選條件
        resp['map_geojson'] = get_geojson(solr.solr_url)
    elif solr_updated or not cache.get('default_map_geojson'):
        # 如果沒有篩選條件且solr資料有更新 或 如果沒有篩選條件且cache沒有default_map_geojson
        resp['map_geojson'] = get_geojson(solr.solr_url)
        cache.set('default_map_geojson', resp['map_geojson'])
        cache.set('default_solr_count', resp['count'])
    else: # 如果沒有篩選條件且solr沒更新且cache有default_map_geojson
        resp['map_geojson'] = default_map_geojson
    resp['elapsed'] = time.time() - time_start
    #print('final', time.time() - time_start)
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
                'label': '國家/區域 Country or Area',
                'rows': [{'label': x['label'], 'key': x['label'] } for x in COUNTRY_ROWS]
            },
            {
                'key': 'year',
                'label': '年份 Year',
                'rows': YEAR_ROWS
            },
            {
                'key': 'month',
                'label': '月份 Month',
                'rows': [{'label': '{}月'.format(x),'key': x} for x in range(1, 13)]
            },
            {
                'key': 'dataset',
                'label': '資料集 Dataset',
                'rows': dataset_menu,
            },
            {
                'key':'publisher',
                'label': '發布單位 Publisher',
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
    # content search
    ds_search = DatasetSearch(list(request.GET.lists()))
    # menu item
    ds_menu = DatasetSearch([]) 

    if has_menu:
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
            'count': x['count'],
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
                'label': '發布單位 Publisher',
                'rows': publisher_rows
            },
            {
                'key': 'country',
                'label': '分布地區/國家 Publishing Country or Area',
                'rows': country_rows
            },
            {
                'key': 'rights',
                'label': '授權類型 Licence',
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
                'label': '國家/區域 Country or Area',
                'rows': [{'label': DATA_MAPPING['country'][x['country_code']], 'count': x['count'], 'key': x['country_code'] } for x in country_list]
            },
        ]

        menus = [
            {
                'key': 'country_code',
                'label': '國家/區域 Country or Area',
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
                'label': '分類位階 Rank',
                'rows': [{
                    'key': x['key'],
                    'label': x['label'],
                } for x in Taxon.get_tree(rank=rank, status=status)]
            },
            {
                'key': 'status',
                'label': '學名狀態 Status',
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
        
    rows = query.filter(status__contains='PUBLIC')
    hdata = {}
    current_year_data = {
        'dataset': [{'x': '{}'.format(x), 'y': 0} for x in range(1, 13)],
        'occurrence': [{'x': '{}'.format(x), 'y': 0} for x in range(1, 13)]
    }
    history_data = {
        'dataset': [],
        'occurrence': []
    }
    for i in rows:
        if not i.created:
            continue
        
        y = str(i.created.year)
        if str(current_year) == y:
            m = i.created.month
            current_year_data['dataset'][m-1]['y'] += 1
            current_year_data['occurrence'][m-1]['y'] += i.num_record
        if y not in hdata:
            hdata[y] = {
                'dataset': 1,
                'occurrence': i.num_record
            } 
        else:
            hdata[y]['dataset'] += 1
            hdata[y]['occurrence'] += i.num_record
            
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
    r = requests.get(f'http://solr:8983/solr/taibif_occurrence/select?facet=true&q.op=AND&rows={search_limit}&q={solr_q}&fq={solr_fq}&{facet_json}')

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
                'label': '發布單位',
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
    solr = SolrQuery('taibif_occurrence')
    solr_url = solr.generate_solr_url(request.GET.lists())
    generateCSV(solr_url,request)

    return JsonResponse({"status":'success'}, safe=False)

def generateCSV(solr_url,request):
    #directory = os.path.abspath(os.path.join(os.path.curdir))
    #taibifVolumesPath = '/taibif-volumes/media/'
    #csvFolder = directory+taibifVolumesPath
    CSV_MEDIA_FOLDER = 'csv'
    csvFolder = os.path.join(conf_settings.MEDIA_ROOT, CSV_MEDIA_FOLDER)
    timestramp = str(int(time.time()))
    type = request.GET['type']
    filename = f'{type}_{timestramp}.csv'
    tempFilename = f'{timestramp}_temp.csv'
    downloadURL = '没有任何資料'
    csvFileTempPath = os.path.join(csvFolder, tempFilename)
    csvFilePath = os.path.join(csvFolder, filename)
    dataPolicyURL = "https://"+request.META['HTTP_HOST']+'/data-policy'
    if not os.path.exists(csvFolder):
        os.makedirs(csvFolder)

    if len(solr_url) > 0:
        downloadURL = "https://"+request.META['HTTP_HOST']+conf_settings.MEDIA_URL+os.path.join(CSV_MEDIA_FOLDER, filename)

        if type == 'species' :
            commands = 'curl "'+solr_url+'" >  '+csvFileTempPath+'  &&  ( head -1 '+csvFileTempPath+' && tail -n+2 '+csvFileTempPath+'  | awk \'BEGIN{FS=OFS=","}NF=(NF-1)\'  | awk -F , \'{a[$0]++; next}END {for (i in a) print i", "a[i]}\'| awk -F , \'!seen[$1]++\' ) > '+csvFilePath+' && rm -rf '+csvFileTempPath

        else :
            commands = f'curl "{solr_url}"  > {csvFilePath} '

        print(commands)
        process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      
    sendMail(downloadURL,request,dataPolicyURL)

def sendMail(downloadURL,request,dataPolicyURL):
    license = 'CC-BY-NC 4.0'
    datasets = request.GET.getlist('dataset')
    facet_dataset = 'dataset:{type:terms,field:taibif_dataset_name_zh}'
    facet_license = 'dataset:{type:terms,field:license}'
    facet_json = 'json.facet={'+facet_dataset + ',' +facet_license+'}'

    for dataset in datasets:
        r = requests.get(f'http://solr:8983/solr/taibif_occurrence/select?fl=license&fq=taibif_dataset_name:({quote(dataset)})&q.op=OR&q=*%3A*&rows=1')

        if r.status_code == 200:
            data = r.json()
            print(data)
            search_count = data['response']['numFound']
            if search_count != 0:
                datasetLicense = data['response']['docs'][0]['license']
                if datasetLicense == 'CC-BY-NC 4.0':
                    license = datasetLicense
                else :
                    license = '未明確授權'

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

授權條款： {license}

<br/><br/>

使用條款：<a href="{dataPolicyURL}">{dataPolicyURL}</a>

<br/><br/>
下載連結：<a href="{downloadURL}">{downloadURL}</a>

<br/><br/>
若有問題再麻煩您回覆至

<br/><br/>
<a href='mailto:taibif.brcas@gmail.com'>taibif.brcas@gmail.com</a>

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
