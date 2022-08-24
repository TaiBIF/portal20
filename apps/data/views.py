import time
from urllib.parse import urlencode
import re
import datetime
import csv
import requests


from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.db.models import Q
from django.http import (
    JsonResponse,
    HttpResponseRedirect,
    Http404,
    HttpResponse,
)
from django.urls import reverse
from django.conf import settings

from apps.article.models import Article
from .models import (
    Taxon,
    Occurrence,
    Dataset,
    Dataset_citation,
    Dataset_keyword,
    Dataset_Contact,
    Dataset_description,
    DatasetOrganization,
)
from .helpers.species import get_species_info
from .helpers.mod_search import (
    OccurrenceSearch,
    DatasetSearch,
    PublisherSearch,
    SpeciesSearch,
)
from utils.solr_query import SolrQuery

from apps.data.models import DATA_MAPPING

from conf.settings import ENV

def search_all(request):
    if request.method == 'POST':
        q = request.POST.get('q', '')
        url = '/search/'
        if q:
            url = '{}?q={}'.format(url, q)
        return HttpResponseRedirect(url)
    elif request.method == 'GET':
        q = request.GET.get('q', '')
        ## 預設最多每組 20 筆
        count = 0

        # TODO check article type 
        # article
        # article_rows = []
        # for x in Article.objects.filter(title__icontains=q).all()[:10]:
        #     article_rows.append({
        #         'title': x.title,
        #         'content': x.content,
        #         'url': x.get_absolute_url()
        #     })
        # count += len(article_rows)

        # occurrence
        occur_rows = []
        solr = SolrQuery('taibif_occurrence')
        req = solr.request(request.GET.lists())
        resp = solr.get_response()
        
        for x in resp['results']:
            name=''
            name_zh=''
            if 'scientificName' in x.keys():
                name = x['scientificName']
            if  'vernacularName' in x.keys():
                name_zh = x['vernacularName']
            occur_rows.append({
                'title': '{} {}'.format(name, name_zh),
                'content': '資料集: {}'.format(x['taibif_dataset_name_zh']),
                'url': '/occurrence/{}'.format(x['taibif_occ_id'][0]) 
            })
        count += len(occur_rows)

        # dataset
        dataset_rows = []
        for x in Dataset.objects.values('title', 'name','id').filter(Q(title__icontains=q)).exclude(status='Private').all()[:20]:
            dataset_rows.append({
                'title': x['title'],
                'content':Dataset_description.objects.filter(dataset=x['id']).order_by('seq')[0].description, 
                'url': '/dataset/{}'.format(x['name'])
            })
        count += len(dataset_rows)

        # species
        species_rows = []
        for x in Taxon.objects.filter(Q(name__icontains=q) | Q(name_zh__icontains=q)).all()[:20]:
            species_rows.append({
                'title': '[{}] {}'.format(x.get_rank_display(), x.get_name()),
                'content': '物種數: {}'.format(x.count),
                'url': '/species/{}'.format(x.id),
            })
        count += len(species_rows)

        # publisher
        publisher_rows = []
        for x in DatasetOrganization.objects.filter(name__icontains=q).all()[:20]:
            publisher_rows.append({
                'title': x.name,
                'content': x.description,
                'url': '/publisher/{}'.format(x.id)
            })
        count += len(publisher_rows)

        context = {
            'count': count,
            'results': [
                # {
                #     'cat': 'article',
                #     'label': '文章',
                #     'rows': article_rows
                # },
                {
                    'cat': 'occurrence',
                    'label': '出現紀錄',
                    'rows': occur_rows
                },
                {
                    'cat': 'species',
                    'label': '物種',
                    'rows': species_rows
                },
                {
                    'cat': 'dataset',
                    'label': '資料集',
                    'rows': dataset_rows
                },
                {
                    'cat': 'publisher',
                    'label': '發布單位',
                    'rows': publisher_rows
                },
            ]
        }
        return render(request, 'search_all.html', context)



def occurrence_view(request, taibif_id):
    # occurrence = get_object_or_404(RawDataOccurrence, taibif_id=taibif_id)
    solr = SolrQuery('taibif_occurrence')
    req = solr.get_occurrence(taibif_id)
    resp = solr.get_response()
    result = req['results']
    
    intro = {}
    record = {}
    occ = {}
    event = {}
    taxon = {}
    location = {}
    other = {}
    
    lat = 0
    lon = 0

    # intro 
    intro['dataset_zh']=result[0].get('taibif_dataset_name_zh')
    intro['publisher']=result[0].get('publisher')
    intro['basisOfRecord']=result[0].get('basisOfRecord')
    intro['scientificName']=result[0].get('scientificName')
    intro['species_key']=result[0].get('species_key')
    intro['kingdom_key']=result[0].get('kingdom_key')
    intro['phylum_key']=result[0].get('phylum_key')
    intro['order_key']=result[0].get('order_key')
    intro['class_key']=result[0].get('class_key')
    intro['genus_key']=result[0].get('genus_key')
    intro['dataset']=result[0].get('taibif_dataset_name')
    intro['name_zh']=result[0].get('tname_zh')
    

    # record
    record['modified']={'name_zh':'資料更新時間','value':result[0].get('modified')}
    record['language']={'name_zh':'語言','value':result[0].get('language')}
    record['license']={'name_zh':'授權標示','value':result[0].get('license')}
    record['rightsHolder']={'name_zh':'所有權','value':result[0].get('rightsHolder')}
    record['references']={'name_zh':'參考資料','value':result[0].get('references')}
    record['institutionID']={'name_zh':'機構ID','value':result[0].get('institutionID')}
    record['collectionID']={'name_zh':'典藏ID','value':result[0].get('collectionID')}
    record['datasetID']={'name_zh':'資料集ID','value':result[0].get('datasetID')}
    record['institutionCode']={'name_zh':'機構代號','value':result[0].get('institutionCode')}
    record['collectionCode']={'name_zh':'典藏代號','value':result[0].get('collectionCode')}
    record['datasetName']={'name_zh':'資料集名稱','value':result[0].get('datasetName')}
    record['ownerInstitutionCode']={'name_zh':'所有者機構代碼','value':result[0].get('ownerInstitutionCode')}
    record['basisOfRecord'] ={'name_zh':'資料基底','value':result[0].get('asisOfRecord')}
    record['informationWithheld']={'name_zh':'其他隱藏資訊','value':result[0].get('informationWithheld')}
    record['dataGeneralizations']={'name_zh':'資料模糊化','value':result[0].get('dataGeneralizations')}

    # occ 
    occ['catalogNumber']={'name_zh':'catalogNumber','value':result[0].get('catalogNumber')}
    occ['occurrenceID']={'name_zh':'出現紀錄ID','value':result[0].get('occurrenceID')}
    occ['recordNumber ']={'name_zh':'採集號','value':result[0].get('recordNumber ')}
    occ['recordedByID ']={'name_zh':'記錄者ID','value':result[0].get('occurrenceID')}
    occ['recordedBy']={'name_zh':'記錄者','value':result[0].get('recordedBy')}
    occ['individualCount']={'name_zh':'個體數量','value':result[0].get('individualCount')}
    occ['organismQuantity']={'name_zh':'數量','value':result[0].get('organismQuantity')}
    occ['organismQuantityType']={'name_zh':'數量單位','value':result[0].get('organismQuantityType')}
    occ['lifeStage']={'name_zh':'生活史階段','value':result[0].get('lifeStage')}
    occ['sex']={'name_zh':'性別','value':result[0].get('sex')}
    occ['reproductiveCondition']={'name_zh':'生殖狀態','value':result[0].get('reproductiveCondition')}
    occ['establishmentMeans']={'name_zh':'establishmentMeans','value':result[0].get('establishmentMeans')}
    occ['behavior']={'name_zh':'行為','value':result[0].get('behavior')}
    occ['georeferenceVerificationStatus']={'name_zh':'georeferenceVerificationStatus','value':result[0].get('georeferenceVerificationStatus')}
    occ['occurrenceStatus']={'name_zh':'occurrenceStatus','value':result[0].get('occurrenceStatus')}
    occ['preparations']={'name_zh':'preparations','value':result[0].get('preparations')}
    occ['disposition']={'name_zh':'disposition','value':result[0].get('disposition')}
    occ['associatedMedia']={'name_zh':'多媒體URL','value':result[0].get('associatedMedia')}
    occ['associatedReferences']={'name_zh':'associatedReferences','value':result[0].get('associatedReferences')}
    occ['associatedSequences']={'name_zh':'associatedSequences','value':result[0].get('associatedSequences')}
    occ['associatedTaxa']={'name_zh':'associatedTaxa','value':result[0].get('associatedTaxa')}
    occ['otherCatalogNumbers']={'name_zh':'otherCatalogNumbers','value':result[0].get('otherCatalogNumbers')}
    occ['occurrenceRemarks']={'name_zh':'出現紀錄註記','value':result[0].get('occurrenceRemarks')}

    # event
    event['eventID']={'name_zh':'調查活動ID','value':result[0].get('eventID')}
    event['parentEventID']={'name_zh':'parentEventID','value':result[0].get(' parentEventID')}
    event['fieldNumber']={'name_zh':'野外調查編號','value':result[0].get('fieldNumber')}
    event['eventDate']={'name_zh':'調查活動日期','value':result[0].get('eventDate')}
    event['eventTime']={'name_zh':'調查活動時間','value':result[0].get('eventTime')}
    event['startDayOfYear']={'name_zh':'起始年份','value':result[0].get('startDayOfYear')}
    event['endDayOfYear']={'name_zh':'結束年份','value':result[0].get('endDayOfYear')}
    event['year']={'name_zh':'年','value':result[0].get('year')}
    event['month']={'name_zh':'月','value':result[0].get('month')}
    event['day']={'name_zh':'日','value':result[0].get('day')}
    event['verbatimEventDate']={'name_zh':'字面上調查活動日期','value':result[0].get('verbatimEventDate')}
    event['habitat']={'name_zh':'棲地','value':result[0].get('habitat')}
    event['samplingProtocol']={'name_zh':'調查方法','value':result[0].get('samplingProtocol')}
    event['samplingEffort']={'name_zh':'調查努力量','value':result[0].get('samplingEffort')}
    event['fieldNotes']={'name_zh':'野外調查註記','value':result[0].get('fieldNotes')}
    event['eventRemarks']={'name_zh':'調查活動註記','value':result[0].get('eventRemarks')}    
    
    # taxon
    try: 
        acceptedNameUsageID = int(float(result[0].get('acceptedNameUsageID')))
    except:
        acceptedNameUsageID = result[0].get('acceptedNameUsageID')

    taxon['taxonID']={'name_zh':'分類ID','value':result[0].get('taxonID')}
    taxon['scientificNameID']={'name_zh':'學名ID','value':result[0].get(' scientificNameID')}
    taxon['acceptedNameUsageID']={'name_zh':'有效學名ID','value':acceptedNameUsageID}
    taxon['scientificName']={'name_zh':'學名','value':result[0].get('scientificName')}
    taxon['acceptedNameUsage']={'name_zh':'有效學名','value':result[0].get('acceptedNameUsage')}
    taxon['originalNameUsage']={'name_zh':'originalNameUsage','value':result[0].get('originalNameUsage')}
    taxon['nameAccordingTo']={'name_zh':'nameAccordingTo','value':result[0].get('nameAccordingTo')}
    taxon['namePublishedIn']={'name_zh':'namePublishedIn','value':result[0].get('namePublishedIn')}
    taxon['higherClassification']={'name_zh':'高階分類階層','value':result[0].get('higherClassification')}
    taxon['kingdom']={'name_zh':'界','value':result[0].get('kingdom')}
    taxon['phylum']={'name_zh':'門','value':result[0].get('phylum')}
    taxon['class']={'name_zh':'綱','value':result[0].get('class')}
    taxon['order']={'name_zh':'目','value':result[0].get('order')}
    taxon['family']={'name_zh':'科','value':result[0].get('family')}
    taxon['genus']={'name_zh':'屬','value':result[0].get('genus')}
    taxon['subgenus']={'name_zh':'亞屬','value':result[0].get('subgenus')}
    taxon['specificEpithet']={'name_zh':'specificEpithet','value':result[0].get('specificEpithet')}
    taxon['infraspecificEpithet']={'name_zh':'infraspecificEpithet','value':result[0].get('infraspecificEpithet')}
    taxon['taxonRank']={'name_zh':'分類位階','value':result[0].get('taxonRank')}
    taxon['verbatimTaxonRank']={'name_zh':'字面上分類位階','value':result[0].get('verbatimTaxonRank')}
    taxon['scientificNameAuthorship']={'name_zh':'scientificNameAuthorship','value':result[0].get('scientificNameAuthorship')}
    taxon['vernacularName']={'name_zh':'俗名','value':result[0].get('vernacularName')}
    taxon['nomenclaturalCode']={'name_zh':'nomenclaturalCode','value':result[0].get('nomenclaturalCode')}
    taxon['taxonRemarks']={'name_zh':'分類註記','value':result[0].get('taxonRemarks')}

    # location
    location['locationID']={'name_zh':'資料更新時間','value':result[0].get('locationID')}
    location['higherGeographyID']={'name_zh':'higherGeographyID','value':result[0].get(' higherGeographyID')}
    location['higherGeography']={'name_zh':'higherGeography','value':result[0].get('higherGeography')}
    location['continent']={'name_zh':'洲','value':result[0].get('continent')}
    location['waterBody']={'name_zh':'水體','value':result[0].get('waterBody')}
    location['islandGroup']={'name_zh':'群島','value':result[0].get('islandGroup')}
    location['island']={'name_zh':'島嶼','value':result[0].get('island')}
    location['country']={'name_zh':'國家','value':result[0].get('country')}
    location['countryCode']={'name_zh':'國家代碼','value':result[0].get('countryCode')}
    location['stateProvince']={'name_zh':'省份/州','value':result[0].get('stateProvince')}
    location['county']={'name_zh':'縣市','value':result[0].get('county')}
    location['municipality']={'name_zh':'municipality','value':result[0].get('municipality')}
    location['locality']={'name_zh':'地區','value':result[0].get('locality')}
    location['verbatimLocality']={'name_zh':'字面上地區','value':result[0].get('verbatimLocality')}
    location['minimumElevationInMeters']={'name_zh':'最低海拔(公尺)','value':result[0].get('minimumElevationInMeters')}
    location['maximumElevationInMeters']={'name_zh':'最高海拔(公尺)','value':result[0].get('maximumElevationInMeters')}
    location['verbatimElevation']={'name_zh':'字面上海拔','value':result[0].get('verbatimElevation')}
    location['minimumDepthInMeters']={'name_zh':'最小深度(公尺)','value':result[0].get('minimumDepthInMeters')}
    location['maximumDepthInMeters']={'name_zh':'最大深度(公尺)','value':result[0].get('maximumDepthInMeters')}
    location['verbatimDepth']={'name_zh':'字面上深度','value':result[0].get('verbatimDepth')}
    location['locationAccordingTo']={'name_zh':'locationAccordingTo','value':result[0].get('locationAccordingTo')}
    location['locationRemarks']={'name_zh':'locationRemarks','value':result[0].get('locationRemarks')}
    location['decimalLatitude']={'name_zh':'十進位緯度','value':result[0].get('decimalLatitude')}
    location['decimalLongitude']={'name_zh':'十進位經度','value':result[0].get('decimalLongitude')}
    location['geodeticDatum']={'name_zh':'geodeticDatum','value':result[0].get('geodeticDatum')}
    location['coordinateUncertaintyInMeters']={'name_zh':'座標誤差(公尺)','value':result[0].get('coordinateUncertaintyInMeters')}
    location['coordinatePrecision']={'name_zh':'座標精準度','value':result[0].get('coordinatePrecision')}
    location['pointRadiusSpatialFit']={'name_zh':'pointRadiusSpatialFit','value':result[0].get('pointRadiusSpatialFit')}
    location['verbatimCoordinates']={'name_zh':'字面上座標','value':result[0].get('verbatimCoordinates')}
    location['verbatimLatitude']={'name_zh':'字面上緯度','value':result[0].get('verbatimLatitude')}
    location['verbatimLongitude']={'name_zh':'字面上經度','value':result[0].get('verbatimLongitude')}
    location['verbatimCoordinateSystem']={'name_zh':'字面上座標格式','value':result[0].get('verbatimCoordinateSystem')}
    location['verbatimSRS']={'name_zh':'verbatimSRS','value':result[0].get('verbatimSRS')}
    location['footprintWKT']={'name_zh':'footprintWKT','value':result[0].get('footprintWKT')}
    location['footprintSpatialFit']={'name_zh':'footprintSpatialFit','value':result[0].get('footprintSpatialFit')}
    location['georeferencedBy']={'name_zh':'georeferencedBy','value':result[0].get('georeferencedBy')}
    location['georeferencedDate']={'name_zh':'georeferencedDate','value':result[0].get('georeferencedDate')}
    location['georeferenceProtocol']={'name_zh':'georeferenceProtocol','value':result[0].get('georeferenceProtocol')}
    location['georeferenceSources']={'name_zh':'georeferenceSources','value':result[0].get('georeferenceSources')}
    location['georeferenceRemarks']={'name_zh':'georeferenceRemarks','value':result[0].get('georeferenceRemarks')}

    # other

    lat = None
    lon = None
    if result[0].get('taibif_latitude'):
        lat = result[0].get('taibif_latitude')[0]
    elif result[0].get('decimalLatitude'):
        lat = result[0].get('decimalLatitude')

    if result[0].get('taibif_longitude'):
        lon = result[0].get('taibif_longitude')[0]
    elif result[0].get('decimalLongitude'):
        lon = result[0].get('decimalLongitude')
    # print(result[0])
    context = {
        'intro':intro,
        'record':record,
        'occ':occ,
        'event':event, 
        'taxon':taxon,
        'location':location,
        'other':other,
    }
    if lat and lon:
        context['map_view'] =  [lat, lon]
    # print(context['map_view'])

    return render(request, 'occurrence.html', context)

def dataset_view(request, name):
    
    try:
        dataset = Dataset.public_objects.get(name=name)
        organization_name = None
        try :
            organization_name = DatasetOrganization.objects.get(id=dataset.organization_id).name 
        except :
            organization_name = None
        contacts = []
        citation =[]
        description = []
        keyword = []
        for x in Dataset_Contact.objects.filter(dataset=dataset.id).values():
            del x['id'],x['dataset_id']
            contacts.append(x)
            
        for x in Dataset_citation.objects.filter(dataset=dataset.id).values():
            del x['id'],x['dataset_id']
            citation.append(x)

        for x in Dataset_description.objects.filter(dataset=dataset.id).values():
            del x['id'],x['dataset_id']
            description.append(x)
        

        for x in Dataset_keyword.objects.filter(dataset=dataset.id).values():
            del x['id'],x['dataset_id']
            keyword.append(x)        
        
        #Count the number of longitude and latitude
        # dataset_s = SimpleData.objects.filter(taibif_dataset_name = name).values_list('longitude','latitude','year','taxon_family_id',
        #                                                                               'taxon_family_id')

        # count_long = [item[0] for item in dataset_s]
        # LonNum =  "{:.0%}".format(sum(1 for _ in filter(None.__ne__, count_long))/len(dataset_s))

        # count_lat = [item[1] for item in dataset_s]
        # LatNum = "{:.0%}".format(sum(1 for _ in filter(None.__ne__, count_lat))/len(dataset_s))

        # count_yr = [item[2] for item in dataset_s]
        # YrNum = "{:.0%}".format(sum(1 for _ in filter(None.__ne__, count_yr)) / len(dataset_s))

        # count_fam = [item[3] for item in dataset_s]
        # TaxNum = "{:.0%}".format(sum(1 for _ in filter(None.__ne__, count_fam)) / len(dataset_s))
        # FamNum = len(set(count_fam))

        # count_sp = [item[4] for item in dataset_s]
        # SpNum = len(set(count_sp))

        #dataset_o = RawDataOccurrence.objects.filter(taibif_dataset_name=name).values_list('family')

        

    except Dataset.DoesNotExist:
        raise Http404("Dataset does not exist")

    # return render(request, 'dataset.html', {'dataset': dataset, 'LonNum':LonNum, 'LatNum':LatNum,'YrNum':YrNum, 'TaxNum':TaxNum,
                                            # 'FamNum':FamNum, 'SpNum':SpNum})
    return render(request,'dataset.html',{'dataset':dataset,'contacts':contacts,'citation':citation,'description': description, 'keyword':keyword,'organization_name':organization_name,})





def publisher_view(request, pk):
    context = {}
    dataset = []
    
    context['publisher'] = get_object_or_404(DatasetOrganization, pk=pk)
    for x in Dataset.objects.filter(organization=pk).all():
        dataset.append({
            'name': x.name,
            'name_zh': x.title,
            'core_type':  DATA_MAPPING['publisher_dwc'][x.dwc_core_type],
            'num_record':  x.num_record,
        })
    
    
    context['dataset'] = dataset


    return render(request, 'publisher.html', context)


# 地理分佈|資料集出現次數|物種描述|文獻
def species_view(request, pk):
    context = {}
    dataset = []
    search_count = 0
    map_geojson = False
    taxon = get_object_or_404(Taxon, pk=pk)
    switch = {
            'kingdom':'kingdom_key',
            'phylum':'phylum_key',
            'class':'class_key',
            'order':'order_key',
            'family':'family_key',
            'genus':'genus_key',
            'species':'species_key',
        }
    total = []

    solr_q = switch.get(taxon.rank) + ':' + str(pk)
    

    search_limit = 20
    facet_dataset = 'dataset:{type:terms,field:taibif_dataset_name,limit:-1,mincount:1}'
    facet_dataset_zh = 'dataset_zh:{type:terms,field:taibif_dataset_name_zh,limit:-1,mincount:1}'
    facet_json = 'json.facet={'+facet_dataset +','+facet_dataset_zh +'}'
    

    # if ENV in ['dev','stag']:
    #     r = requests.get(f'http://54.65.81.61:8983/solr/taibif_occurrence/select?facet=true&q.op=AND&rows={search_limit}&q=*:*&fq={solr_q}&{facet_json}')
    # else:
    r = requests.get(f'http://solr:8983/solr/taibif_occurrence/select?facet=true&q.op=AND&rows={search_limit}&q=*:*&fq={solr_q}&{facet_json}')


    map_url = "http://"+request.META['HTTP_HOST']+"/api/v2/occurrence/search?taxon_key="+taxon.rank+":"+str(taxon.id)+"&facet=year&facet=month&facet=dataset&facet=dataset_id&facet=publisher&facet=country&facet=license"
    r2 = requests.get(map_url)

    if r.status_code == 200:

        data = r.json()
        search_count = data['response']['numFound']
        search_offset = data['response']['start']
        search_results = data['response']['docs']

        if search_count != 0 :
            count = []
            dataset_list = []
            dataset_zh_list = []
            count = [x['count'] for x in data['facets']['dataset']['buckets']]
            dataset_list = [x['val'] for x in data['facets']['dataset']['buckets']]
            dataset_zh_list = [x['val']for x in data['facets']['dataset_zh']['buckets']]
            
            for x,y,z in zip(count, dataset_list, dataset_zh_list):
                dataset.append({'count':x,'name':y,'name_zh':z})                

    if r2.status_code == 200:
        data2 = r2.json()

        if data2['map_geojson']['features']!=[]:
            map_geojson = True

    
# dataset_occ_count
        
    context = {
        'taxon': taxon,
        'dataset':dataset,
        'total':search_count,
        'map_view':map_geojson,
    }
    
    return render(request, 'species.html', context)

def search_view(request, cat=''):
   
    context = {'env': settings.ENV}
    return render(request, 'search.html', context)


def search_view_species(request, cat=''): 

    context = {'env': settings.ENV}
    return render(request, 'search_species.html', context)

def search_occurrence_download_view(request):
    date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    # for dropna
    column_map = {}
    rows = []
    for i in RawDataOccurrence._meta.get_fields():
        if not i.many_to_many \
           and not i.one_to_one \
           and not i.one_to_many \
           and not i.many_to_one:
            column_map[i.name] = {
                'title': i.db_column or i.verbose_name,
                'is_na': True,
            }
    occur_search = OccurrenceSearch(list(request.GET.lists()))

    ## very slow!
    #def raw_data_map(x):
        #d = {}
        #for col, col_data in column_map.items():
        #    if v := getattr(x.taibif, col):
        #        column_map[col]['na'] = False
        #        d[col] = v
     #   return x

    # override mod_search
    #occur_search.result_map = raw_data_map
    occur_search.limit = -1

    res = occur_search.get_results()

    taibif_ids = [x['taibif_id'] for x in res['results']]
    raw_data_list = RawDataOccurrence.objects.filter(taibif_id__in=taibif_ids).all()

    rows = []
    for d in raw_data_list:
        r = {}
        for col, col_data in column_map.items():
            if v := getattr(d, col):
                column_map[col]['is_na'] = False
                r[col] = v
        rows.append(r)

    # prepare to csv
    csv_headers = []
    columns = []

    # get valid column and (not null)
    for col, col_data in column_map.items():
        if col_data['is_na'] == False and 'taibif_' not in col :
            csv_headers.append(col_data['title'])
            columns.append(col)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="taibif-occurrence-{}.csv"'.format(date_str)

    writer = csv.writer(response)
    writer.writerow(csv_headers)

    for d in raw_data_list:
            writer.writerow([getattr(d, col) for col in columns])

    return response
