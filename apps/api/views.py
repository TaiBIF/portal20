import time
import json
import datetime
import re
import urllib
import csv
import os
import subprocess
import requests
from django.core import serializers

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
        'datasetName' : x['title'] if 'title' in x else None,
        'taibifDatasetID' : str(x['taibif_dataset_id']) if 'taibif_dataset_id' in x else None,
        'publisherID' : x['organization_uuid'] if 'organization_uuid' in x and x['organization_uuid'] != None else None,
        'publisherName' : x['organization_name'] if 'organization_name' in x and x['organization_name'] != None else None,
        'author' : x['author'] if 'author' in x and x['mod_date'] != None else None,
        'datasetShortName' : x['name'],
        'publicationDate' : x['pub_date'].strftime("%Y-%m-%d") if 'pub_date' in x and x['pub_date'] != None else None,
        'datasetModifiedDate' : x['mod_date'].strftime("%Y-%m-%d") if 'mod_date' in x and x['mod_date'] != None else None,
        'gbifDatasetID' : x['guid'] if 'guid' in x and x['guid'] != None else None,
        'core' : x['dwc_core_type'] if 'dwc_core_type' in x else None,
        'license' : x['data_license'] if 'data_license' in x and x['data_license'] != None else 'unknown',
        'doi' : x['gbif_doi'] if 'gbif_doi' in x and x['gbif_doi'] != None else 'test',
        'numberRecord' : x['num_record'] if 'num_record' in x and x['num_record'] != None else None,
        'numberOccurrence' : x['num_occurrence'] if 'num_occurrence' in x and x['num_occurrence'] != None else None,
        'source' : x['source'] if 'source' in x else None,
        # 'citation' : x['citation'] if 'citation' in x else None,
        # 'resource' : x['resource'] if 'resource' in x else None,
    } for x in result_d ]
    
    return HttpResponse(json.dumps(rows), content_type="application/json")
    
# def taxon_api(request):
    
#     ds_search = SpeciesSearch(list(request.GET.lists())).result_map
#     result_d = ds_search.query.values()
    
#     rows = [{
#         'title' : x['title'] if 'title' in x else None,
#         'name' : x['name'],
#         'author' : x['author'] if 'author' in x and x['mod_date'] != None else None,
#         'pub_date' : x['pub_date'].strftime("%Y-%m-%d") if 'pub_date' in x and x['pub_date'] != None else None,
#         'mod_date' : x['mod_date'].strftime("%Y-%m-%d") if 'mod_date' in x and x['mod_date'] != None else None,
#         'core' : x['dwc_core_type'] if 'dwc_core_type' in x else None,
#         'license' : x['data_license'] if 'data_license' in x and x['data_license'] != None else 'unknown',
#         'doi' : x['gbif_doi'] if 'doi' in x and x['gbif_doi'] != None else None,
#         'organization_id' : x['organization_uuid'] if 'organization_uuid' in x and x['organization_uuid'] != None else None,
#         'organization_name' : x['organization_name'] if 'organization_name' in x and x['organization_name'] != None else None,
#         'num_record' : x['num_record'] if 'num_record' in x and x['num_record'] != None else None,
#         'gbif_dataset_id' : x['guid'] if 'guid' in x and x['guid'] != None else None,
#         # 'citation' : x['citation'] if 'citation' in x else None,
#         # 'resource' : x['resource'] if 'resource' in x else None,
#     } for x in result_d ]
    
#     return HttpResponse(json.dumps(rows), content_type="application/json")


def publisher_api(request):
    dataset = []

    ds_search = PublisherSearch(list(request.GET.lists()))
    result_d =  ds_search.query.values()
        
    rows = [{
        'publisherID' : x['organization_gbif_uuid'] if 'organization_gbif_uuid' in x else None,
        # 'id' : x['id'] if 'id' in x else None,
        'publisherName' : x['name'],
        'countryCode' : x['country_code'] if 'country_code' in x else None,
        'description' : x['description'] if 'description' in x else None,
        'administrativeContact' : x['administrative_contact'] if 'administrative_contact' in x else None,
        'countryOrArea' : x['country_or_area'] if 'country_or_area' in x else None,
        'installations' : x['installations'] if 'installations' in x else None,
        'technicalContact' : x['technical_contact'] if 'technical_contact' in x else None,
    } for x in result_d ]
    
    return HttpResponse(json.dumps(rows), content_type="application/json")


def publisher_dataset_api(request,pk):
    dataset = []
    org = DatasetOrganization.objects.get(id=pk)
    
    rows = {
        'name' : org.name ,
        'description' : org.description,
        'administrative_contact' : org.administrative_contact,
        'technical_contact' : org.technical_contact,
        'country_code' : org.country_code,
        'country_or_area' :org.country_or_area,
        'installations' : org.installations,
        'organization_gbif_uuid' : org.organization_gbif_uuid,
    }
    
    for x in Dataset.objects.filter(organization=pk).all():
        dataset.append({
            'name': x.name,
            'name_zh': x.title,
            'core_type':  DATA_MAPPING['publisher_dwc'][x.dwc_core_type],
            'gbif_dataset_uuid':  x.organization_uuid,
        })

    rows['dataset'] = dataset

    return HttpResponse(json.dumps(rows), content_type="application/json")

'''
for_basic_occ 2023-10 棄用，和 occurrence_api 合併 by JJJ
'''
# def for_basic_occ(request):
#     # rows, offset, taibifModDate
#     query_list = []
#     solr_error = ''
#     rows=100
#     offset=0
#     fq_query=''
#     fq_list = []
#     generate_list = []
#     q_list = []
#     if request.GET.get('q'): 
#         q_list.append(('q', request.GET.get('q')))
#     else:
#         q_list.append(('q', '{}:{}'.format('*', '*')))
    
#     for key, values in request.GET.lists():
#         if key == 'fl':
#             generate_list.append(('fl', values[0]))
#         elif key == 'wt':
#             generate_list.remove(('wt', 'json'))
#             generate_list.append(('wt', values[0]))
#         elif key == "rows":
#             rows = int(values[0])
#             if rows <=3000:
#                 generate_list.append((key, values[0]))
#             else : 
#                 rows = 3000
#                 generate_list.append((key, 3000))
#         elif key == "offset":
#             offset = values[0]
#             generate_list.append(('start', values[0]))
        
#         elif key == "occurrenceID":
#             fq_list.append(('fq', '{}:"{}"'.format('occurrenceID', values[0])))
#         elif key == "taibifOccurrenceID":
#             fq_list.append(('fq', '{}:"{}"'.format('taibif_occ_id', values[0])))
#         elif key == "basisOfRecord":
#             if ',' in values[0]:
#                 vlist = values[0].split(',')
#                 vlistString = '" OR "'.join(vlist)
#                 fq_list.append(('fq', f'taibif_basisOfRecord:"{vlistString}"'))
#             else: 
#                 fq_list.append(('fq', '{}:{}'.format('taibif_basisOfRecord', values[0])))
#         elif key == "datasetName":
#             fq_list.append(('fq', '{}:{}'.format('taibif_dataset_name_zh', values[0])))
            
#         elif key == "taibifDatasetID":
#             fq_list.append(('fq', '{}:"{}"'.format('taibifDatasetID', values[0])))
        
#         elif key == "taxonRank":
#             fq_list.append(('fq', '{}:"{}"'.format('taxon_rank', values[0])))
                
#         elif key == "scientificName":
#             fq_list.append(('fq', '{}:{}'.format('taibif_scientificname', values[0])))
#         elif key == "typeStatus":
#             fq_list.append(('fq', '{}:{} -typeStatus:*voucher*'.format('typeStatus', '*'+values[0]+'*')))
            
#         # range query
#         elif key == "taibifModifiedDate":
#             if ',' in values[0]:
#                 vlist = values[0].split(',')
#                 fq_list.append(('fq', f'mod_date:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]'))
#             else:
#                 fq_list.append(('fq', f'mod_date:"{values[0]}T00:00:00Z"'))
#         elif key == "eventDate":
#             if ',' in values[0]:
#                 vlist = values[0].split(',')
#                 fq_list.append(('fq', f'taibif_event_date:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]'))
#             else:
#                 fq_list.append(('fq', f'taibif_event_date:{values[0]}'))
#         elif key == "coordinateUncertaintyInMeters":
#             if ',' in values[0]:
#                 vlist = values[0].split(',')
#                 fq_list.append(('fq', f'taibif_coordinateUncertaintyInMeters:[{vlist[0]} TO {vlist[1]}]'))
#             else:
#                 fq_list.append(('fq', '{}:{}'.format('taibif_coordinateUncertaintyInMeters', values[0])))
#         elif key == 'license':
#             litype = ''
#             if values[0] == 'CC-BY':
#                 litype = 'Creative Commons Attribution (CC-BY) 4.0 License'
#             elif values[0] == 'CC-BY-NC':
#                 litype = 'Creative Commons Attribution Non Commercial (CC-BY-NC) 4.0 License'
#             elif values[0] == 'CC0':
#                 litype = 'Public Domain (CC0 1.0)'
#             elif values[0] == 'NA':
#                 litype = 'unknown'
#                 # fq_list.append(('fq', '-license:[* TO *]'))
#                 # continue
#             fq_list.append(('fq', '{}:"{}"'.format('license', litype)))
        
#         elif key == 'selfProduced':
#             fq_list.append(('fq', '{}:{}'.format('selfProduced', values[0])))
#         else:
#             return JsonResponse({
#                 'results': 0,
#                 'query_column': key,
#                 'error_msg':"the column can't be search in this mode.",
#             })
    
#     if "rows" not in generate_list:
#         generate_list.append(("rows", 100))
        
#     solr = SolrQuery('taibif_occurrence')
#     fq_query = urllib.parse.urlencode(fq_list)
#     q_query = urllib.parse.urlencode(q_list)
#     generate_query = urllib.parse.urlencode(generate_list)

#     solr.solr_url = f'http://solr:8983/solr/{solr.core}/select?indent=true&q.op=OR'
#     if generate_query:
#         solr.solr_url = solr.solr_url+f'&{generate_query}'
#     if q_query:
#         solr.solr_url = solr.solr_url+f'&{q_query}'
#     if fq_query:
#         solr.solr_url = solr.solr_url+f'&{fq_query}'
#     try: 
#         resp =urllib.request.urlopen(solr.solr_url)
#         resp_dict = resp.read().decode()
#         solr.solr_response = json.loads(resp_dict)
#     except urllib.request.HTTPError as e:
#         solr_error = str(e)
    
#     if not solr.solr_response['response']['docs']: 
#         if solr_error:
#             return JsonResponse({
#                 'results': 0,
#                 'query_list': fq_list,
#                 'error_url': solr.solr_url,
#                 'error_msg': solr_error,
#             })    
        
#         if solr.solr_response['response']['numFound'] == 0:
#             res={}
#             res_list=[] 
#             res['count'] = solr.solr_response['response']['numFound']
#             res['offset'] = int(offset)
#             res['rows'] = int(rows)
#             res['results'] = res_list
#             return JsonResponse(res)
   
#     res={}
#     res_list=[] 
#     for i in solr.solr_response['response']['docs']:
#         backbone = i['taxon_backbone']if 'taxon_backbone' in i else None
#         mediaLicense = i['mediaLicense'] if 'mediaLicense' in i else None
#         group = i['taibif_taxonGroup'][0] if 'taibif_taxonGroup' in i else None
#         if 'orderzh' in i :
#             if i['orderzh'] in ['Accipitriformes','Anseriformes','Apodiformes','Bucerotiformes','Caprimulgiformes','Charadriiformes','Ciconiiformes','Columbiformes','Coraciiformes','Cuculiformes','Falconiformes','Galliformes','Gaviiformes','Gruiformes','Passeriformes','Pelecaniformes','Phaethontiformes','Phoenicopteriformes','Piciformes','Podicipediformes','Procellariiformes','Psittaciformes','Strigiformes','Suliformes','Struthioniformes',]:
#                 group = 'Birds'
#         res_list.append({
#             'occurrenceID':i['occurrenceID'] if 'occurrenceID' in i else None,
#             'taibifOccurrenceID':i['taibif_occ_id'],
#             'basisOfRecord':i['taibif_basisOfRecord'] if 'taibif_basisOfRecord' in i else None,
#             # 'modifiedDate':i['modified'] if 'modified' in i else None,
#             'taibifModifiedDate':i['mod_date'][0],
#             'datasetName':i['taibif_dataset_name_zh'] if 'taibif_dataset_name_zh' in i else None,
#             'occurrenceStatus':i['taibif_occurrenceStatus'] if 'taibif_occurrenceStatus' in i else None,
#             'scientificName': i['taibif_scientificname'] if 'taibif_scientificname' in i else None,
#             'taibifDatasetID': i['taibifDatasetID'],
#             'taxonRank':i['taxon_rank'] if 'taxon_rank' in i else None,
#             'taicolTaxonID': i['taibif_accepted_namecode']  if backbone == "TaiCOL" else  None,
#             'kingdom':i['kingdomzh'] if 'kingdomzh' in i else None,
#             'phylum':i['phylumzh'] if 'phylumzh' in i else None,
#             'class':i['classzh'] if 'classzh' in i else None,
#             'order':i['orderzh'] if 'orderzh' in i else None,
#             'family':i['familyzh'] if 'familyzh' in i else None,
#             'genus':i['genuszh'] if 'genuszh' in i else None,
#             'taxonGroup':group,
#             'eventDate':i['taibif_event_date'] if 'taibif_event_date' in i else None,
#             'year':i['taibif_year'][0] if 'taibif_year' in i else None,
#             'month':i['taibif_month'][0] if 'taibif_month' in i else None,
#             'decimalLatitude':str(i['taibif_latitude'][0]) if 'taibif_latitude' in i  else None,
#             'decimalLongitude':str(i['taibif_longitude'][0]) if 'taibif_longitude' in i  else None,
#             'coordinateUncertaintyInMeters':i['taibif_coordinateUncertaintyInMeters'][0] if 'taibif_coordinateUncertaintyInMeters' in i else None,
#             'country':i['taibif_country'] if 'taibif_country' in i else None,
#             'county':i['taibif_county'] if 'taibif_county' in i else None,
#             'license':i['license'] if 'license' in i and i['license']!= 'unknown' else 'NA',
#             'selfProduced':i['selfProduced'][0],
            
#             'taibifCreatedDate':i['mod_date'][0],
#             'datasetShortName':i['taibif_dataset_name'] if 'taibif_dataset_name' in i else None,
#             'isPreferredName': i['taibif_vernacular_name'] if 'taibif_vernacular_name' in i else None,
#             'gbifAcceptedID':int(float(i['taibif_accepted_namecode']))  if backbone == "GBIF" else  None ,
#             'scientificNameID':i['taibif_namecode'] if 'taibif_namecode' in i else  None,
#             'taxonBackbone':backbone,
#             'day':i['taibif_day'][0] if 'taibif_day' in i else None,
#             'geodeticDatum':i['taibif_geodeticDatum'] if 'taibif_geodeticDatum' in i else None, #對到verbatimCoordinateSystem
#             'verbatimSRS':i['taibif_crs'] if 'taibif_crs' in i else None, # verbatimSRS
#             'dataGeneralizations':i['dataGeneralizations'] if 'dataGeneralizations' in i else None,
#             'coordinatePrecision':i['coordinatePrecision'] if 'coordinatePrecision' in i else None,
#             'locality':i['locality'] if 'locality' in i  else None,
#             'habitatReserve':i['forestN'][0] if 'forestN' in i else None,
#             'wildlifeReserve':i['wildlifeN'][0] if 'wildlifeN' in i else None,
#             'countryCode':i['taibif_countryCode'] if 'taibif_countryCode' in i else None,
#             'typeStatus':i['typeStatus'] if 'typeStatus' in i else None,
#             'preservation':i['preservation'] if 'preservation' in i else None,
#             'collectionID':i['collectionID'] if 'collectionID' in i else None,
#             'recordedBy':i['recordedBy'] if 'recordedBy' in i else None,
#             'recordNumber':i['recordNumber'] if 'recordNumber' in i else None,
#             'organismQuantity':i['organismQuantity'] if 'organismQuantity' in i else None,
#             'organismQuantityType':i['organismQuantityType'] if 'organismQuantityType' in i else None,
#             'associatedMedia':i['associatedMedia']  if 'associatedMedia' else  None,
#             'mediaLicense':mediaLicense,
            
#         })

#     res['url'] = solr.solr_url
#     res['count'] = solr.solr_response['response']['numFound']
#     res['offset'] = int(offset)
#     res['rows'] = int(rows)
#     res['results'] = res_list

#     return JsonResponse(res)

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
    treeRoot = Taxon.objects.filter(rank='Kingdom').all()
    treeData = [{
        'id': x.taicol_taxon_id,
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

def taxon_tree_node(request, taicol_taxon_id):
    linnaean = request.GET.get('linnaean', 'no')
    
    if linnaean == 'yes':
        taxon = Taxon.objects.filter(parent_taxon_id_linnaean=taicol_taxon_id).all()
        children = []
        for taxa in taxon:
            children.append({
                'id': taxa.taicol_taxon_id,
                'data': {
                    'name': taxa.get_name(),
                    'count': taxa.count,
                    'rank': taxa.rank
                }
            })
        children.sort(key=lambda x: (x['data']['rank'], x['data']['name']))
        parent = Taxon.objects.get(taicol_taxon_id=taicol_taxon_id)
        data = {
            'rank': parent.rank,
            'id': parent.taicol_taxon_id,
            'data': {
                'name': parent.get_name(),
                'count': parent.count,
                'rank': parent.rank,
            },
            'children': children,
        }
    else:
        taxon = Taxon.objects.get(taicol_taxon_id=taicol_taxon_id)
        children = sorted(
            [
                {
                    'id': x.taicol_taxon_id,
                    'data': {
                        'name': x.get_name(),
                        'count': x.count,
                        'rank': x.rank,
                    }
                }
                for x in taxon.children
            ],
            key=lambda x: x['data']['rank']  
        )

        data = {
            'rank': taxon.rank,
            'id': taxon.taicol_taxon_id,
            'data': {
                'name': taxon.get_name(),
                'count': taxon.count,
                'rank': taxon.rank,
            },
            'children': children,
        }
    # return HttpResponse(json.dumps(data), content_type="application/json")
    return HttpResponse(json.dumps(data), content_type="application/json")

def occurrence_api(request):
    solr_error = ''
    rows=100
    offset=0
    fq_query=''
    fq_list = []
    generate_list = []
    q_list = []
    map_query = ''
    
    if request.GET.get('q'): 
        q_list.append(('q', request.GET.get('q')))
    else:
        q_list.append(('q', '{}:{}'.format('*', '*')))
    
    for key, values in request.GET.lists():
        if key == "start_date" or key == "end_date":
            continue
        
        # generate search
        elif key == 'fl':
            generate_list.append(('fl', values[0]))
        elif key == 'wt':
            generate_list.remove(('wt', 'json'))
            generate_list.append(('wt', values[0]))
        elif key == "rows":
            rows = int(values[0])
            if rows <=3000:
                generate_list.append((key, values[0]))
            else : 
                rows = 3000
                generate_list.append((key, 3000))
        elif key == "offset":
            offset = values[0]
            generate_list.append(('start', values[0]))
        
        # fq query 
        elif key == "occurrenceID":
            fq_list.append(('fq', '{}:"{}"'.format('occurrenceID', values[0])))
        elif key == "gbifID":
            fq_list.append(('fq', '{}:"{}"'.format('gbifID', values[0])))
        elif key == "taibifOccurrenceID":
            fq_list.append(('fq', '{}:"{}"'.format('taibif_occ_id', values[0])))
        elif key == "basisOfRecord":
            if ',' in values[0]:
                vlist = values[0].split(',')
                vlistString = '" OR "'.join(vlist)
                fq_list.append(('fq', f'taibif_basisOfRecord:"{vlistString}"'))
            else: 
                fq_list.append(('fq', '{}:{}'.format('taibif_basisOfRecord', values[0])))
        elif key == "datasetName":
            fq_list.append(('fq', '{}:{}'.format('taibif_dataset_name_zh', values[0].replace(":", "\:"))))
        elif key == "occurrenceStatus":
            fq_list.append(('fq', '{}:"{}"'.format('taibif_occurrenceStatus', values[0])))
        elif key == "scientificName":
            fq_list.append(('fq', '(taibif_scientificName:"{}" OR taibif_scientificname:"{}")'.format(values[0], values[0])))
        elif key == "taxonRank":
            fq_list.append(('fq', '(taibif_taxonRank:"{}" OR taxon_rank:"{}")'.format(values[0], values[0])))
        elif key == "taicolTaxonId":
            fq_list.append(('fq', '(taibif_taicolTaxonID:"{}" OR taicol_taxon_id:"{}")'.format(values[0], values[0])))
        elif key == "kingdom":
            fq_list.append(('fq', '{}:"{}"'.format('kingdomzh', values[0])))
        elif key == "phylum":
            fq_list.append(('fq', '{}:"{}"'.format('phylumzh', values[0])))
        elif key == "class":
            fq_list.append(('fq', '{}:"{}"'.format('classzh', values[0])))
        elif key == "order":
            fq_list.append(('fq', '{}:"{}"'.format('orderzh', values[0])))
        elif key == "family":
            fq_list.append(('fq', '{}:"{}"'.format('familyzh', values[0])))
        elif key == "genus":
            fq_list.append(('fq', '{}:"{}"'.format('genuszh', values[0])))
        elif key == "taxonGroup":
            if str(values[0]) == 'birds':
                fq_list.append(('fq', '{}:{}'.format('taibif_taxonGroup', 'Accipitriformes Anseriformes Apodiformes Bucerotiformes Caprimulgiformes Charadriiformes Ciconiiformes Columbiformes Coraciiformes Cuculiformes Falconiformes Galliformes Gaviiformes Gruiformes Passeriformes Pelecaniformes Phaethontiformes Phoenicopteriformes Piciformes Podicipediformes Procellariiformes Psittaciformes Strigiformes Suliformes Struthioniformes')))
            else:
                fq_list.append(('fq', '{}:"{}"'.format('taibif_taxonGroup', values[0])))
        elif key == "country":
            if ',' in values[0]:
                vlist = values[0].split(',')
                vlistString = '" OR "'.join(vlist)
                fq_list.append(('fq', f'taibif_country:"{vlistString}"'))
            else: 
                fq_list.append(('fq', '{}:{}'.format('taibif_country', values[0])))
        elif key == "county":
            if ',' in values[0]:
                vlist = values[0].split(',')
                vlistString = '" OR "'.join(vlist)
                fq_list.append(('fq', f'taibif_county:"{vlistString}"'))
            else: 
                fq_list.append(('fq', '{}:"{}"'.format('taibif_county', values[0])))
        elif key == "issue":
            if str(values[0]) == 'Taxon Match None':
                fq_list.append(('fq', '{}:"{}"'.format('TaxonMatchNone', 'true')))
            if str(values[0]) == 'Recorded Date Invalid':
                fq_list.append(('fq', '{}:"{}"'.format('RecordedDateInvalid', 'true')))
            if str(values[0]) == 'Coordinate Invalid':
                fq_list.append(('fq', '{}:"{}"'.format('CoordinateInvalid', 'true')))
                
        elif key == "typeStatus":
            fq_list.append(('fq', '{}:{} -typeStatus:*voucher*'.format('typeStatus', '*'+values[0]+'*')))
        # range query
        elif key == "modifiedDate":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'modifiedDate:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]'))
            else:
                fq_list.append(('fq', f'modifiedDate:"{values[0]}T00:00:00Z"'))
        elif key == "taibifModifiedDate":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'mod_date:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]'))
            else:
                fq_list.append(('fq', f'mod_date:"{values[0]}T00:00:00Z"'))
        elif key == 'gbifDatasetID':
            if values[0]:
                fq_list.append(('fq', '(taibif_datasetKey:"{}" OR gbif_dataset_uuid:"{}")'.format(values[0], values[0])))
            else: 
                fq_list.append(('fq', '{}:{}'.format('gbif_dataset_uuid', '*')))
        elif key == "eventDate":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'taibif_event_date:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]'))
            else:
                fq_list.append(('fq', f'taibif_event_date:{values[0]}'))
        elif key == "year":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'taibif_year:[{vlist[0]} TO {vlist[1]}]'))
            else:
                fq_list.append(('fq', '{}:{}'.format('taibif_year', values[0])))

        elif key == "month":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'taibif_month:[{vlist[0]} TO {vlist[1]}]'))
            else:
                fq_list.append(('fq', '{}:"{}"'.format('taibif_month', values[0])))
        elif key == 'decimalLatitude':
            coor_list = [ float(c) for c in values]
            y1 = convert_y_coor_to_grid(min(coor_list))
            y2 = convert_y_coor_to_grid(max(coor_list))
            map_query = "{!frange l=" + str(y1) + " u=" + str(y2) + "}grid_y"
            fq_list.append(('fq', map_query))
        elif key == 'decimalLongitude':
            coor_list = [ float(c) for c in values]
            x1 = convert_x_coor_to_grid(min(coor_list))
            x2 = convert_x_coor_to_grid(max(coor_list))
            map_query = "{!frange l=" + str(x1) + " u=" + str(x2) + "}grid_x"
            fq_list.append(('fq', map_query))
        elif key == "coordinateUncertaintyInMeters":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'taibif_coordinateUncertaintyInMeters:[{vlist[0]} TO {vlist[1]}]'))
            else:
                fq_list.append(('fq', '{}:{}'.format('taibif_coordinateUncertaintyInMeters', values[0])))
        elif key == 'license':
            litype = ''
            if values[0] == 'CC-BY':
                litype = 'Creative Commons Attribution (CC-BY) 4.0 License'
            elif values[0] == 'CC-BY-NC':
                litype = 'Creative Commons Attribution Non Commercial (CC-BY-NC) 4.0 License'
            elif values[0] == 'CC0':
                litype = 'Public Domain (CC0 1.0)'
            elif values[0] == 'NA':
                litype = 'unknown'
                # fq_list.append(('fq', '-license:[* TO *]'))
                # continue
            fq_list.append(('fq', '{}:"{}"'.format('license', litype)))
        elif key == "taibifDatasetID":
            fq_list.append(('fq', '(taibif_datasetKey:"{}" OR taibifDatasetID:"{}")'.format(values[0], values[0])))

        elif key == 'selfProduced':
            fq_list.append(('fq', '{}:{}'.format('selfProduced', values[0])))
        else:
            return JsonResponse({
                'results': 0,
                'query_column': key,
                'error_msg':"the column can't be search in this mode.",
            })
    
    if "rows" not in generate_list:
        generate_list.append(("rows", 100))
        
    solr = SolrQuery('taibif_occurrence')
    fq_query = urllib.parse.urlencode(fq_list)
    q_query = urllib.parse.urlencode(q_list)
    generate_query = urllib.parse.urlencode(generate_list)

    solr.solr_url = f'http://solr:8983/solr/{solr.core}/select?indent=true&q.op=OR'
    if generate_query:
        solr.solr_url = solr.solr_url+f'&{generate_query}'
    if q_query:
        solr.solr_url = solr.solr_url+f'&{q_query}'
    if fq_query:
        solr.solr_url = solr.solr_url+f'&{fq_query}'
        
    try: 
        resp =urllib.request.urlopen(solr.solr_url)
        resp_dict = resp.read().decode()
        solr.solr_response = json.loads(resp_dict)
    except urllib.request.HTTPError as e:
        solr_error = str(e)
    
    if not solr.solr_response['response']['docs']: 
        if solr_error:
            return JsonResponse({
                'results': 0,
                'query_list': fq_list,
                'error_url': solr.solr_url,
                'error_msg': solr_error,
            })    
        
        if solr.solr_response['response']['numFound'] == 0:
            res={}
            res_list=[] 
            res['count'] = solr.solr_response['response']['numFound']
            res['offset'] = int(offset)
            res['rows'] = int(rows)
            res['results'] = res_list
            return JsonResponse(res)
   
    res={}
    res_list=[] 
    for i in solr.solr_response['response']['docs']:
        taicolTaxonID = None
        gbifAcceptedID = None
        scientificName = None
        taxonRank = None
        backbone = i['taxon_backbone'] if 'taxon_backbone' in i else (i['taibif_taxonBackbone'] if 'taibif_taxonBackbone' in i else None)
        if backbone == 'TaiCol' or backbone == 'TaiCOL':
            taicolTaxonID = i['taibif_accepted_namecode'] if 'taibif_accepted_namecode' in i else (i['taibif_taicolTaxonID'] if 'taibif_taicolTaxonID' in i else None)
            gbifAcceptedID = i['taxonKey'] if 'taxonKey' in i else None
            scientificName = i['taibif_scientificname'] if 'taibif_scientificname' in i else (i['taibif_scientificName'] if 'taibif_scientificName' in i else None)
            taxonRank = i['taxon_rank'] if 'taxon_rank' in i else (i['taibif_taxonRank'] if 'taibif_taxonRank' in i else None)
        elif backbone == 'GBIF':
            gbifAcceptedID = int(float(i['taibif_accepted_namecode'])) if 'taibif_accepted_namecode' in i else None
            scientificName = i['taibif_scientificname'] if 'taibif_scientificname' in i else None
            taxonRank = i['taxon_rank'] if 'taxon_rank' in i else None
        elif backbone == None:
            gbifAcceptedID = i['taxonKey'] if 'taxonKey' in i else None
            scientificName = i['scientificName'] if 'scientificName' in i else None
            taxonRank = i['taxonRank'] if 'taxonRank' in i else None
            
        issue = None
        if 'geo_issue' in i and i['geo_issue'] or 'taxon_issue' in i and i['taxon_issue'] or 'time_issue' in i:
            issue = ';'.join(filter(None, [i.get('geo_issue'), i.get('taxon_issue'), i.get('time_issue')]))
        
        
        mediaLicense = i['taibif_mediaLicense'] if 'taibif_mediaLicense' in i else None
        group = i['taibif_taxonGroup'][0] if 'taibif_taxonGroup' in i else None
        if 'orderzh' in i :
            if i['orderzh'] in ['Accipitriformes','Anseriformes','Apodiformes','Bucerotiformes','Caprimulgiformes','Charadriiformes','Ciconiiformes','Columbiformes','Coraciiformes','Cuculiformes','Falconiformes','Galliformes','Gaviiformes','Gruiformes','Passeriformes','Pelecaniformes','Phaethontiformes','Phoenicopteriformes','Piciformes','Podicipediformes','Procellariiformes','Psittaciformes','Strigiformes','Suliformes','Struthioniformes',]:
                group = 'Birds'
        issues = []
        if 'TaxonMatchNone' in i and i['TaxonMatchNone'][0] == True:
            issues.append('TaxonMatchNone')
        if 'CoordinateInvalid' in i and i['CoordinateInvalid'][0] == True:
            issues.append('CoordinateInvalid')
        if 'RecordedDateInvalid' in i and i['RecordedDateInvalid'][0] == True:
            issues.append('RecordedDateInvalid')
        
        res_list.append({
            # 轉譯資料
            'taibifOccurrenceID':i['taibif_occ_id'],
            'basisOfRecord':i['taibif_basisOfRecord'] if 'taibif_basisOfRecord' in i else None,
            'scientificName': scientificName,
            'taxonGroup':group,
            'taxonRank': taxonRank,
            'scientificNameID':i['taibif_namecode'] if 'taibif_namecode' in i else  None,
            'isPreferredName': i['taibif_vernacular_name'] if 'taibif_vernacular_name' in i else None,
            'taxonBackbone':backbone,
            'taicolTaxonID': taicolTaxonID, 
            'gbifAcceptedID': gbifAcceptedID,
            'kingdom':i['kingdomzh'] if 'kingdomzh' in i else (i['kingdom'] if 'kingdom' in i else None),
            'phylum':i['phylumzh'] if 'phylumzh' in i else (i['phylum'] if 'phylum' in i else None),
            'class':i['classzh'] if 'classzh' in i else (i['class'] if 'class' in i else None),
            'order':i['orderzh'] if 'orderzh' in i else (i['order'] if 'order' in i else None),
            'family':i['familyzh'] if 'familyzh' in i else (i['family'] if 'family' in i else None),
            'genus':i['genuszh'] if 'genuszh' in i else (i['genus'] if 'genus' in i else None),
            'eventDate':i['taibif_event_date'] if 'taibif_event_date' in i else (i['taibif_eventDate'] if 'taibif_eventDate' in i else None),
            'year':i['taibif_year'][0] if 'taibif_year' in i else None,
            'month':i['taibif_month'][0] if 'taibif_month' in i else None,
            'day':i['taibif_day'][0] if 'taibif_day' in i else None,
            'geodeticDatum':i['taibif_geodeticDatum'] if 'taibif_geodeticDatum' in i else None, #對到verbatimCoordinateSystem
            'verbatimSRS':i['taibif_crs'] if 'taibif_crs' in i else None, # verbatimSRS
            'decimalLongitude':str(i['taibif_longitude'][0]) if 'taibif_longitude' in i  else (i['taibif_decimalLongitude'] if 'taibif_decimalLongitude' in i else None),
            'decimalLatitude':str(i['taibif_latitude'][0]) if 'taibif_latitude' in i  else (i['taibif_decimalLatitude'] if 'taibif_decimalLatitude' in i else None),
            'coordinateUncertaintyInMeters':i['taibif_coordinateUncertaintyInMeters'][0] if 'taibif_coordinateUncertaintyInMeters' in i else None,
            'countryCode':i['taibif_countryCode'] if 'taibif_countryCode' in i else None,
            'country':i['taibif_country'] if 'taibif_country' in i else None,
            'county':i['taibif_county'] if 'taibif_county' in i else None,
            'habitatReserve':i['forestN'][0] if 'forestN' in i else (i['forest_reserves'] if 'forest_reserves' in i else None),
            'wildlifeReserve':i['wildlifeN'][0] if 'wildlifeN' in i else (i['wildlife_refuges'] if 'wildlife_refuges' in i else None),
            'occurrenceStatus':i['taibif_occurrenceStatus'] if 'taibif_occurrenceStatus' in i else None,
            'selfProduced':i['selfProduced'][0],
            'license':i['license'] if 'license' in i and i['license']!= 'unknown' else 'NA',
            # 基本資料
            'datasetName':i['taibif_dataset_name_zh'] if 'taibif_dataset_name_zh' in i else None,
            'datasetShortName':i['taibif_dataset_name'] if 'taibif_dataset_name' in i else None,
            'occurrenceID':i['occurrenceID'] if 'occurrenceID' in i else None,
            'catalogNumber': i['catalogNumber'] if 'catalogNumber' in i else None,
            'taibifCreatedDate':i['mod_date'][0] if 'mod_date' in i else None,
            'taibifModifiedDate':i['mod_date'][0] if 'mod_date' in i else (i['taibif_lastInterpreted'] if 'taibif_lastInterpreted' in i else None),
            'dataGeneralizations':i['dataGeneralizations'] if 'dataGeneralizations' in i else None,
            'coordinatePrecision':i['coordinatePrecision'] if 'coordinatePrecision' in i else None,
            'locality':i['locality'] if 'locality' in i  else None,
            'preservation':i['preservation'] if 'preservation' in i else None,
            'typeStatus':i['typeStatus'] if 'typeStatus' in i else (i['taibif_typeStatus'] if 'taibif_typeStatus' in i else None),
            'recordedBy':i['recordedBy'] if 'recordedBy' in i else None,
            'recordNumber':i['recordNumber'] if 'recordNumber' in i else None,
            'organismQuantity':i['organismQuantity'] if 'organismQuantity' in i else None,
            'organismQuantityType':i['organismQuantityType'] if 'organismQuantityType' in i else None,
            'associatedMedia':i['associatedMedia']  if 'associatedMedia' in i else  None,
            'mediaLicense':mediaLicense,
            # 常用資料
            'gbifID':  i['gbifID'] if 'gbifID' in i else None,
            'taibifDatasetID':  i['taibifDatasetID'] if 'taibifDatasetID' in i else (i['taibif_datasetKey'] if 'taibif_datasetKey' in i else None),
            'gbifDatasetID':i['gbif_dataset_uuid'] if 'gbif_dataset_uuid' in i else (i['taibif_datasetKey'] if 'taibif_datasetKey' in i else None),
            'establishmentMeans':i['establishmentMeans'] if 'establishmentMeans' in i else (i['taibif_establishmentMeans'] if 'taibif_establishmentMeans' in i else None),
            'issue':','.join(issues) if issues else (issue if issue else None),
            # 沒分類
            # 'modifiedDate':i['modified'] if 'modified' in i else None,
        })

    res['url'] = solr.solr_url
    res['count'] = solr.solr_response['response']['numFound']
    res['offset'] = int(offset)
    res['rows'] = int(rows)
    res['results'] = res_list
    return JsonResponse(res)



def raw_occ_api(request):
    solr_error = ''
    rows=100
    offset=0
    fq_query=''
    fq_list = []
    generate_list = []
    q_list = []
    map_query = ''
    
    if request.GET.get('q'): 
        q_list.append(('q', request.GET.get('q')))
    else:
        q_list.append(('q', '{}:{}'.format('*', '*')))
    
    for key, values in request.GET.lists():
        if key == "start_date" or key == "end_date":
            continue
        
        # generate search
        elif key == 'fl':
            generate_list.append(('fl', values[0]))
        elif key == 'wt':
            generate_list.remove(('wt', 'json'))
            generate_list.append(('wt', values[0]))
        elif key == "rows":
            rows = int(values[0])
            if rows <=3000:
                generate_list.append((key, values[0]))
            else : 
                rows = 3000
                generate_list.append((key, 3000))
        elif key == "offset":
            offset = values[0]
            generate_list.append(('start', values[0]))
        
        # fq query 
        elif key == "occurrenceID":
            fq_list.append(('fq', '{}:"{}"'.format('occurrenceID', values[0])))
        elif key == "taibifOccurrenceID":
            fq_list.append(('fq', '{}:"{}"'.format('taibif_occ_id', values[0])))
        elif key == "basisOfRecord":
            if ',' in values[0]:
                vlist = values[0].split(',')
                vlistString = '" OR "'.join(vlist)
                fq_list.append(('fq', f'taibif_basisOfRecord:"{vlistString}"'))
            else: 
                fq_list.append(('fq', '{}:{}'.format('taibif_basisOfRecord', values[0])))
        elif key == "datasetName":
            fq_list.append(('fq', '{}:{}'.format('taibif_dataset_name_zh', values[0].replace(":", "\:"))))
        elif key == "occurrenceStatus":
            fq_list.append(('fq', '{}:"{}"'.format('taibif_occurrenceStatus', values[0])))
        elif key == "scientificName":
            fq_list.append(('fq', '{}:{}'.format('taibif_scientificname', values[0])))
        elif key == "taxonRank":
            fq_list.append(('fq', '{}:"{}"'.format('taxon_rank', values[0])))
        elif key == "taicolTaxonId":
            fq_list.append(('fq', '{}:"{}"'.format('taicol_taxon_id', values[0])))
        elif key == "kingdom":
            fq_list.append(('fq', '{}:"{}"'.format('kingdomzh', values[0])))
        elif key == "phylum":
            fq_list.append(('fq', '{}:"{}"'.format('phylumzh', values[0])))
        elif key == "class":
            fq_list.append(('fq', '{}:"{}"'.format('classzh', values[0])))
        elif key == "order":
            fq_list.append(('fq', '{}:"{}"'.format('orderzh', values[0])))
        elif key == "family":
            fq_list.append(('fq', '{}:"{}"'.format('familyzh', values[0])))
        elif key == "genus":
            fq_list.append(('fq', '{}:"{}"'.format('genuszh', values[0])))
        elif key == "taxonGroup":
            if str(values[0]) == 'birds':
                fq_list.append(('fq', '{}:{}'.format('taibif_taxonGroup', 'Accipitriformes Anseriformes Apodiformes Bucerotiformes Caprimulgiformes Charadriiformes Ciconiiformes Columbiformes Coraciiformes Cuculiformes Falconiformes Galliformes Gaviiformes Gruiformes Passeriformes Pelecaniformes Phaethontiformes Phoenicopteriformes Piciformes Podicipediformes Procellariiformes Psittaciformes Strigiformes Suliformes Struthioniformes')))
            else:
                fq_list.append(('fq', '{}:"{}"'.format('taibif_taxonGroup', values[0])))
        elif key == "country":
            if ',' in values[0]:
                vlist = values[0].split(',')
                vlistString = '" OR "'.join(vlist)
                fq_list.append(('fq', f'taibif_country:"{vlistString}"'))
            else: 
                fq_list.append(('fq', '{}:{}'.format('taibif_country', values[0])))
        elif key == "county":
            if ',' in values[0]:
                vlist = values[0].split(',')
                vlistString = '" OR "'.join(vlist)
                fq_list.append(('fq', f'taibif_county:"{vlistString}"'))
            else: 
                fq_list.append(('fq', '{}:"{}"'.format('taibif_county', values[0])))
        elif key == "issue":
            if str(values[0]) == 'Taxon Match None':
                fq_list.append(('fq', '{}:"{}"'.format('TaxonMatchNone', 'true')))
            if str(values[0]) == 'Recorded Date Invalid':
                fq_list.append(('fq', '{}:"{}"'.format('RecordedDateInvalid', 'true')))
            if str(values[0]) == 'Coordinate Invalid':
                fq_list.append(('fq', '{}:"{}"'.format('CoordinateInvalid', 'true')))
        
        elif key == "taibifDatasetID":
            fq_list.append(('fq', '{}:"{}"'.format('taibifDatasetID', values[0])))
 
        elif key == "typeStatus":
            fq_list.append(('fq', '{}:{} -typeStatus:*voucher*'.format('typeStatus', '*'+values[0]+'*')))
        # range query
        elif key == "modifiedDate":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'modifiedDate:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]'))
            else:
                fq_list.append(('fq', f'modifiedDate:"{values[0]}T00:00:00Z"'))
        elif key == "taibifModifiedDate":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'mod_date:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]'))
            else:
                fq_list.append(('fq', f'mod_date:"{values[0]}T00:00:00Z"'))
        elif key == 'gbifDatasetID':
            if values[0]:
                fq_list.append(('fq', '{}:"{}"'.format('gbif_dataset_uuid', values[0])))
            else: 
                fq_list.append(('fq', '{}:{}'.format('gbif_dataset_uuid', '*')))
        elif key == "eventDate":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'taibif_event_date:[{vlist[0]}T00:00:00Z TO {vlist[1]}T00:00:00Z]'))
            else:
                fq_list.append(('fq', f'taibif_event_date:{values[0]}'))
        elif key == "year":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'taibif_year:[{vlist[0]} TO {vlist[1]}]'))
            else:
                fq_list.append(('fq', '{}:{}'.format('taibif_year', values[0])))

        elif key == "month":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'taibif_month:[{vlist[0]} TO {vlist[1]}]'))
            else:
                fq_list.append(('fq', '{}:"{}"'.format('taibif_month', values[0])))
        elif key == 'decimalLatitude':
            coor_list = [ float(c) for c in values]
            y1 = convert_y_coor_to_grid(min(coor_list))
            y2 = convert_y_coor_to_grid(max(coor_list))
            map_query = "{!frange l=" + str(y1) + " u=" + str(y2) + "}grid_y"
            fq_list.append(('fq', map_query))
        elif key == 'decimalLongitude':
            coor_list = [ float(c) for c in values]
            x1 = convert_x_coor_to_grid(min(coor_list))
            x2 = convert_x_coor_to_grid(max(coor_list))
            map_query = "{!frange l=" + str(x1) + " u=" + str(x2) + "}grid_x"
            fq_list.append(('fq', map_query))
        elif key == "coordinateUncertaintyInMeters":
            if ',' in values[0]:
                vlist = values[0].split(',')
                fq_list.append(('fq', f'taibif_coordinateUncertaintyInMeters:[{vlist[0]} TO {vlist[1]}]'))
            else:
                fq_list.append(('fq', '{}:{}'.format('taibif_coordinateUncertaintyInMeters', values[0])))
        elif key == 'license':
            litype = ''
            if values[0] == 'CC-BY':
                litype = 'Creative Commons Attribution (CC-BY) 4.0 License'
            elif values[0] == 'CC-BY-NC':
                litype = 'Creative Commons Attribution Non Commercial (CC-BY-NC) 4.0 License'
            elif values[0] == 'CC0':
                litype = 'Public Domain (CC0 1.0)'
            elif values[0] == 'NA':
                litype = 'unknown'
                # fq_list.append(('fq', '-license:[* TO *]'))
                # continue
            fq_list.append(('fq', '{}:"{}"'.format('license', litype)))
        
        elif key == 'establishmentMeans':
            fq_list.append(('fq', '{}:{}'.format('establishmentMeans', values[0])))

        elif key == 'selfProduced':
            fq_list.append(('fq', '{}:{}'.format('selfProduced', values[0])))
        else:
            return JsonResponse({
                'results': 0,
                'query_column': key,
                'error_msg':"the column can't be search in this mode.",
            })

    if "rows" not in generate_list:
        generate_list.append(("rows", 100))
        
    solr = SolrQuery('taibif_occurrence')
    fq_query = urllib.parse.urlencode(fq_list)
    q_query = urllib.parse.urlencode(q_list)
    generate_query = urllib.parse.urlencode(generate_list)

    solr.solr_url = f'http://solr:8983/solr/{solr.core}/select?indent=true&q.op=OR'
    if generate_query:
        solr.solr_url = solr.solr_url+f'&{generate_query}'
    if q_query:
        solr.solr_url = solr.solr_url+f'&{q_query}'
    if fq_query:
        solr.solr_url = solr.solr_url+f'&{fq_query}'
        
    resp =urllib.request.urlopen(solr.solr_url)
    resp_dict = resp.read().decode()
    solr.solr_response = json.loads(resp_dict)
    if not solr.solr_response['response']['docs']: 
        if solr_error:
            return JsonResponse({
                'results': 0,
                'query_list': fq_list,
                'error_url': solr.solr_url,
                'error_msg': solr_error,
            })    
        
        if solr.solr_response['response']['numFound'] == 0:
            res={}
            res_list=[] 
            res['count'] = solr.solr_response['response']['numFound']
            res['offset'] = int(offset)
            res['rows'] = int(rows)
            res['results'] = res_list
            return JsonResponse(res)
    return JsonResponse(solr.solr_response)


#@json_ret
def search_dataset(request):
    has_menu = True if request.GET.get('menu', '') else False
    menu_list = []
    # content search
    ds_search = DatasetSearch(list(request.GET.lists()))
    # menu item
    ds_menu = DatasetSearch([]) 
    if has_menu:
        condiction_menu = list(request.GET.lists())
        publisher_query = []
        for k,v in condiction_menu:
            if k!= "publisher":
                publisher_query.append((k,v))
        publisher_menu = DatasetSearch(publisher_query) 
        # publisher 
        publisher_list = ds_menu.query\
            .values('organization','organization_name')\
            .exclude(organization__isnull=True)\
            .exclude(organization_name__isnull=True)\
            .distinct('organization')
        
        publisher_count = publisher_menu.query\
            .values('organization')\
            .exclude(organization__isnull=True)\
            .exclude(organization_name__isnull=True)\
            .annotate(count=Count('organization'))\
            .order_by('-count')
        for i in publisher_list:
            if publisher_count.filter(organization=i['organization']):
                i['count'] = publisher_count.filter(organization=i['organization'])[0]['count']    
            else:
                i['count'] = 0
        publisher_rows = [{
            'key':x['organization'],
            'label':x['organization_name'],
            'count': x['count'],
        } for x in publisher_list]
        publisher_rows = sorted(publisher_rows, key=lambda d: d['count'], reverse=True) 


        country_query = []
        for k,v in condiction_menu:
            if k!= "country":
                country_query.append((k,v))
        country_menu = DatasetSearch(country_query) 
        # country
        country_list = ds_menu.query\
            .values('country')\
            .exclude(country__exact='')\
            .distinct('country')
        country_count = country_menu.query\
            .values('country')\
            .exclude(country__exact='')\
            .annotate(count=Count('country'))\
            .order_by('-count')
        for i in country_list:
            if country_count.filter(country=i['country']):
                i['count'] = country_count.filter(country=i['country'])[0]['count']    
            else:
                i['count'] = 0
        
        country_rows = [{
            'key':x['country'],
            'label':DATA_MAPPING['country'][x['country']],
            'count': x['count']
        } for x in country_list]
        country_rows = sorted(country_rows, key=lambda d: d['count'], reverse=True) 


        rights_query = []
        for k,v in condiction_menu:
            if k!= "rights":
                rights_query.append((k,v))
        rights_menu = DatasetSearch(rights_query) 
        # license
        rights_list = ds_menu.query\
            .values('data_license')\
            .exclude(data_license__exact='')\
            .distinct('data_license')
        rights_count = rights_menu.query\
            .values('data_license')\
            .exclude(data_license__exact='')\
            .annotate(count=Count('data_license'))\
            .order_by('-count')
        for i in rights_list:
            if rights_count.filter(data_license=i['data_license']):
                i['count'] = rights_count.filter(data_license=i['data_license'])[0]['count']
            else:
                i['count'] = 0
                
        rights_rows = [{
            'key': DATA_MAPPING['rights'][x['data_license']],
            'label':DATA_MAPPING['rights'][x['data_license']],
            'count': x['count']
        } for x in rights_list]
        rights_rows = sorted(rights_rows, key=lambda d: d['count'], reverse=True) 
        
        source_query = []
        for k,v in condiction_menu:
            if k != 'source':
                source_query.append((k,v))
        source_menu = DatasetSearch(source_query) 
        
        source_list = ds_menu.query.values('source').exclude(source__exact='').distinct('source')

        source_count_data = source_menu.query.values('source').exclude(source__exact='').annotate(count=Count('source')).order_by('-count')
        source_count_dict = {item['source']: item['count'] for item in source_count_data}
        
        for source in source_list:
            source['count'] = source_count_dict.get(source['source'], 0)

        source_rows = [{
            'key': DATA_MAPPING['source'].get(item['source'], ''),
            'label': DATA_MAPPING['source'].get(item['source'], ''),
            'count': item['count']
        } for item in source_list]

        source_rows = sorted(source_rows, key=lambda d: d['count'], reverse=True)

        menu_list = [
            {
                'key':'publisher',
                'label': '發布單位 Publisher',
                'rows': publisher_rows
            },
            {
                'key': 'country',
                'label': '發布地區/國家 Publishing Country or Area',
                'rows': country_rows
            },
            {
                'key': 'rights',
                'label': '授權類型 Licence',
                'rows': rights_rows
            },
            {
                'key': 'source',
                'label': '資料來源 Source',
                'rows': source_rows
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
    species_search = SpeciesSearch(list(request.GET.lists()))
    #species_ids = list(species_search.query.values('id').all())
    has_menu = True if request.GET.get('menu', '') else False
    menu_list = []
    
    condiction_menu = list(request.GET.lists())
    higherTaxon_query = []
    for k,v in condiction_menu:
        if k!= "highertaxon":
            higherTaxon_query.append((k,v))
    higherTaxon_menu = SpeciesSearch(higherTaxon_query) 

    kingdom_count = higherTaxon_menu.query\
            .extra(select ={'taxon_id':'kingdom_taxon_id'})\
            .values('taxon_id')\
            .exclude(kingdom_taxon_id__exact='')\
            .annotate(count=Count('kingdom_taxon_id'))\
            .order_by('-count')
    phylum_count = higherTaxon_menu.query\
            .extra(select ={'taxon_id':'phylum_taxon_id'})\
            .values('taxon_id')\
            .exclude(phylum_taxon_id__exact='')\
            .annotate(count=Count('phylum_taxon_id'))\
            .order_by('-count')
    order_count = higherTaxon_menu.query\
            .extra(select ={'taxon_id':'order_taxon_id'})\
            .values('taxon_id')\
            .exclude(order_taxon_id__exact='')\
            .annotate(count=Count('order_taxon_id'))\
            .order_by('-count')
    class_count = higherTaxon_menu.query\
            .extra(select ={'taxon_id':'class_taxon_id'})\
            .values('taxon_id')\
            .exclude(class_taxon_id__exact='')\
            .annotate(count=Count('class_taxon_id'))\
            .order_by('-count')
    family_count = higherTaxon_menu.query\
            .extra(select ={'taxon_id':'family_taxon_id'})\
            .values('taxon_id')\
            .exclude(family_taxon_id__exact='')\
            .annotate(count=Count('family_taxon_id'))\
            .order_by('-count')
    genus_count = higherTaxon_menu.query\
            .extra(select ={'taxon_id':'genus_taxon_id'})\
            .values('taxon_id')\
            .exclude(genus_taxon_id__exact='')\
            .annotate(count=Count('genus_taxon_id'))\
            .order_by('-count')
    
    taxon_count = kingdom_count.union(phylum_count).union(order_count).union(class_count).union(family_count).union(genus_count).order_by('-count')[:10]
    
    higherTaxon_menu_tmp = []
    if taxon_count:
        higherTaxon_menu_tmp = [{
            'key': x['taxon_id'],
            'label': Taxon.objects.get(taicol_taxon_id = x['taxon_id']).name,
            'count': x['count'],
        } for x in taxon_count if x['taxon_id'] != None]
    
    if has_menu:
        menus = [
            {
                'key': 'rank',
                'label': '分類位階 Rank',
                'rows': [{
                    'key': x['key'],
                    'label': x['label'],
                    'count': x['count'],
                } for x in Taxon.get_tree(rank=rank, status=status)]
            },
            {
                'key': 'highertaxon',
                'label': '高階分類群 Higher Taxon Classification',
                'rows': higherTaxon_menu_tmp,
            },
            {
                'key': 'status',
                'label': '學名狀態 Status',
                'rows': [
                    {'label': '有效的 Accepted', 'key': 'accepted'},
                    {'label': '同物異名 Synonym', 'key': 'synonym'}
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
            current_year_data['occurrence'][m-1]['y'] += i.num_occurrence
        if y not in hdata:
            hdata[y] = {
                'dataset': 1,
                'occurrence': i.num_occurrence
            } 
        else:
            hdata[y]['dataset'] += 1
            hdata[y]['occurrence'] += i.num_occurrence
            
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
#------- DEPRECATED ------#

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

        # print("commands === ", commands)
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



def get_autocomplete_taxon(request):
    names = []
    if keyword_str := request.GET.get('keyword','').strip():
        regex_string = '^'+ keyword_str +'.*'
        autocomplete_taxon = Taxon.objects.filter(name__iregex=regex_string)[:10]
        
        if autocomplete_taxon:
            names = [{
                'key': x.taicol_taxon_id,
                'name': x.name,
                'label':x.name,
            } for x in autocomplete_taxon]
     
    return HttpResponse(json.dumps(names), content_type='application/json') 
