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
    Book_citation,
    Dataset_Contact,
    #RawDataOccurrence,
    DatasetOrganization,
    #SimpleData,
)
from .helpers.species import get_species_info
from .helpers.mod_search import (
    OccurrenceSearch,
    DatasetSearch,
    PublisherSearch,
    SpeciesSearch,
)
from utils.solr_query import SolrQuery


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
        article_rows = []
        for x in Article.objects.filter(title__icontains=q).all()[:10]:
            article_rows.append({
                'title': x.title,
                'content': x.content,
                'url': x.get_absolute_url()
            })
        count += len(article_rows)

        occur_rows = []
        for x in RawDataOccurrence.objects.values('vernacularname', 'scientificname', 'taibif_id', 'taibif_dataset_name').filter(Q(scientificname__icontains=q)|Q(vernacularname__icontains=q)).all()[:20]:
            occur_rows.append({
                'title': '{} {}'.format(x['scientificname'], x['vernacularname']),
                'content': '資料集: {}'.format(x['taibif_dataset_name']),
                'url': '/occurrence/{}'.format(x['taibif_id']) #x.get_absolute_url()
            })
        count += len(occur_rows)

        dataset_rows = []
        for x in Dataset.objects.values('title', 'description', 'name').filter(Q(title__icontains=q) | Q(description__icontains=q)).exclude(status='Private').all()[:20]:
            dataset_rows.append({
                'title': x['title'],
                'content':x['description'],
                'url': '/dataset/{}'.format(x['name'])
            })
        count += len(dataset_rows)

        species_rows = []
        for x in Taxon.objects.filter(Q(name__icontains=q) | Q(name_zh__icontains=q)).all():
            species_rows.append({
                'title': '[{}] {}'.format(x.get_rank_display(), x.get_name()),
                'content': '物種數: {}'.format(x.count),
                'url': '/species/{}'.format(x.id),
            })
        count += len(species_rows)

        publisher_rows = []
        for x in DatasetOrganization.objects.filter(name__icontains=q).all():
            publisher_rows.append({
                'title': x.name,
                'content': x.description,
                'url': '/publisher/{}'.format(x.id)
            })
        count += len(publisher_rows)

        context = {
            'count': count,
            'results': [
                {
                    'cat': 'article',
                    'label': '文章',
                    'rows': article_rows
                },
                {
                    'cat': 'occurrence',
                    'label': '出現紀錄',
                    'rows': occur_rows
                },
                # {
                #     'cat': 'species',
                #     'label': '物種',
                #     'rows': species_rows
                # },
                {
                    'cat': 'dataset',
                    'label': '資料集',
                    'rows': dataset_rows
                },
                {
                    'cat': 'publisher',
                    'label': '發布者',
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
    record['modified']=result[0].get('modified')
    record['language']=result[0].get('language')
    record['license']=result[0].get('license')
    record['rightsHolder']=result[0].get('rightsHolder')
    record['references']=result[0].get('references')
    record['institutionID']=result[0].get('institutionID')
    record['collectionID']=result[0].get('collectionID')
    record['datasetID']=result[0].get('datasetID')
    record['institutionCode']=result[0].get('institutionCode')
    record['collectionCode']=result[0].get('collectionCode')
    record['datasetName']=result[0].get('datasetName')
    record['ownerInstitutionCode']=result[0].get('ownerInstitutionCode')
    record['basisOfRecord'] =result[0].get('asisOfRecord')
    record['informationWithheld']=result[0].get('informationWithheld')
    record['dataGeneralizations']=result[0].get('dataGeneralizations')

    # occ 
    occ['catalogNumber']=result[0].get('catalogNumber')
    occ['occurrenceID']=result[0].get('occurrenceID')
    occ['recordNumber ']=result[0].get('recordNumber ')
    occ['recordedBy']=result[0].get('recordedBy')
    occ['individualCount']=result[0].get('individualCount')
    occ['organismQuantity']=result[0].get('organismQuantity')
    occ['organismQuantityType']=result[0].get('organismQuantityType')
    occ['lifeStage']=result[0].get('lifeStage')
    occ['ex']=result[0].get('sex')
    occ['reproductiveCondition']=result[0].get('reproductiveCondition')
    occ['establishmentMeans']=result[0].get('establishmentMeans')
    occ['behavior']=result[0].get('behavior')
    occ['georeferenceVerificationStatus']=result[0].get('georeferenceVerificationStatus')
    occ['occurrenceStatus']=result[0].get('occurrenceStatus')
    occ['preparations']=result[0].get('preparations')
    occ['disposition']=result[0].get('disposition')
    occ['associatedMedia']=result[0].get('associatedMedia')
    occ['associatedReferences']=result[0].get('associatedReferences')
    occ['associatedSequences']=result[0].get('associatedSequences')
    occ['associatedTaxa']=result[0].get('associatedTaxa')
    occ['otherCatalogNumbers']=result[0].get('otherCatalogNumbers')
    occ['occurrenceRemarks']=result[0].get('occurrenceRemarks')
    occ['occurrenceID']=result[0].get('occurrenceID')
    occ['individualCount']=result[0].get('individualCount')

    # event
    event['eventID']=result[0].get('eventID')
    event['parentEventID']=result[0].get(' parentEventID')
    event['fieldNumber']=result[0].get('fieldNumber')
    event['eventDate']=result[0].get('eventDate')
    event['eventTime']=result[0].get('eventTime')
    event['startDayOfYear']=result[0].get('startDayOfYear')
    event['endDayOfYear']=result[0].get('endDayOfYear')
    event['year']=result[0].get('year')
    event['month']=result[0].get('month')
    event['day']=result[0].get('day')
    event['verbatimEventDate']=result[0].get('verbatimEventDate')
    event['habitat']=result[0].get('habitat')
    event['samplingProtocol']=result[0].get('samplingProtocol')
    event['samplingEffort']=result[0].get('samplingEffort')
    event['fieldNotes']=result[0].get('fieldNotes')
    event['eventRemarks']=result[0].get('eventRemarks')    
    
    # taxon
    taxon['taxonID']=result[0].get('taxonID')
    taxon['scientificNameID']=result[0].get(' scientificNameID')
    taxon['acceptedNameUsageID']=result[0].get('acceptedNameUsageID')
    taxon['scientificName']=result[0].get('scientificName')
    taxon['acceptedNameUsage']=result[0].get('acceptedNameUsage')
    taxon['originalNameUsage']=result[0].get('originalNameUsage')
    taxon['nameAccordingTo']=result[0].get('nameAccordingTo')
    taxon['namePublishedIn']=result[0].get('namePublishedIn')
    taxon['higherClassification']=result[0].get('higherClassification')
    taxon['kingdom']=result[0].get('kingdom')
    taxon['phylum']=result[0].get('phylum')
    taxon['class']=result[0].get('class')
    taxon['order']=result[0].get('order')
    taxon['family']=result[0].get('family')
    taxon['genus']=result[0].get('genus')
    taxon['subgenus']=result[0].get('subgenus')
    taxon['specificEpithet']=result[0].get('specificEpithet')
    taxon['infraspecificEpithet']=result[0].get('infraspecificEpithet')
    taxon['taxonRank']=result[0].get('taxonRank')
    taxon['verbatimTaxonRank']=result[0].get('verbatimTaxonRank')
    taxon['scientificNameAuthorship']=result[0].get('scientificNameAuthorship')
    taxon['vernacularName']=result[0].get('vernacularName')
    taxon['nomenclaturalCode']=result[0].get('nomenclaturalCode')
    taxon['taxonRemarks']=result[0].get('taxonRemarks')

    print('==================',taxon)
    # location
    location['locationID']=result[0].get('locationID')
    location[' higherGeographyID']=result[0].get(' higherGeographyID')
    location['higherGeography']=result[0].get('higherGeography')
    location['continent']=result[0].get('continent')
    location['waterBody']=result[0].get('waterBody')
    location['islandGroup']=result[0].get('islandGroup')
    location['island']=result[0].get('island')
    location['country']=result[0].get('country')
    location['countryCode']=result[0].get('countryCode')
    location['stateProvince']=result[0].get('stateProvince')
    location['county']=result[0].get('county')
    location['municipality']=result[0].get('municipality')
    location['locality']=result[0].get('locality')
    location['verbatimLocality']=result[0].get('verbatimLocality')
    location['minimumElevationInMeters']=result[0].get('minimumElevationInMeters')
    location['maximumElevationInMeters']=result[0].get('maximumElevationInMeters')
    location['verbatimElevation']=result[0].get('verbatimElevation')
    location['minimumDepthInMeters']=result[0].get('minimumDepthInMeters')
    location['maximumDepthInMeters']=result[0].get('maximumDepthInMeters')
    location['verbatimDepth']=result[0].get('verbatimDepth')
    location['locationAccordingTo']=result[0].get('locationAccordingTo')
    location['locationRemarks']=result[0].get('locationRemarks')
    location['decimalLatitude']=result[0].get('decimalLatitude')
    location['decimalLongitude']=result[0].get('decimalLongitude')
    location['geodeticDatum']=result[0].get('geodeticDatum')
    location['coordinateUncertaintyInMeters']=result[0].get('coordinateUncertaintyInMeters')
    location['coordinatePrecision']=result[0].get('coordinatePrecision')
    location['pointRadiusSpatialFit']=result[0].get('pointRadiusSpatialFit')
    location['verbatimCoordinates']=result[0].get('verbatimCoordinates')
    location['verbatimLatitude']=result[0].get('verbatimLatitude')
    location['verbatimLongitude']=result[0].get('verbatimLongitude')
    location['verbatimCoordinateSystem']=result[0].get('verbatimCoordinateSystem')
    location['verbatimSRS']=result[0].get('verbatimSRS')
    location['footprintWKT']=result[0].get('footprintWKT')
    location['footprintSpatialFit']=result[0].get('footprintSpatialFit')
    location['georeferencedBy']=result[0].get('georeferencedBy')
    location['georeferencedDate']=result[0].get('georeferencedDate')
    location['georeferenceProtocol']=result[0].get('georeferenceProtocol')
    location['georeferenceSources']=result[0].get('georeferenceSources')
    location['georeferenceRemarks']=result[0].get('georeferenceRemarks')

    # other


    if result[0].get('latitude'):
        lat = result[0].get('latitude')
    elif result[0].get('decimallatitude'):
        lat = result[0].get('decimallatitude')

    if result[0].get('longitude'):
        lon = result[0].get('longitude')
    elif result[0].get('decimallongitude'):
        lon = result[0].get('decimallongitude')

    if lat and lon:
        context['map_view'] =  [lat, lon]

    context = {
        'intro':intro,
        'record':record,
        'occ':occ,
        'event':event, 
        'taxon':taxon,
        'location':location,
        'other':other,
    }

    return render(request, 'occurrence.html', context)

def dataset_view(request, name):
    
    try:
        dataset = Dataset.public_objects.get(name=name)

        contacts = []
        citation =[]
        for x in Dataset_Contact.objects.filter(dataset=dataset.id).values():
            del x['id'],x['dataset_id']
            contacts.append(x)
            
        for x in Book_citation.objects.filter(dataset=dataset.id).values():
            del x['id'],x['dataset_id']
            citation.append(x)


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
    return render(request,'dataset.html',{'dataset':dataset,'contacts':contacts,'citation':citation})





def publisher_view(request, pk):
    context = {}
    context['publisher'] = get_object_or_404(DatasetOrganization, pk=pk)
    return render(request, 'publisher.html', context)


# 地理分佈|資料集出現次數|物種描述|文獻
def species_view(request, pk):
    context = {}
    dataset = []
    search_count = 0
    taxon = get_object_or_404(Taxon, pk=pk)
    switch = {
            'kingdom':'kingdom_key',
            'phylum':'phylum_key',
            'class':'class_key',
            'order':'order_key',
            'family':'family_key',
            'genus':'genus_key',
            'species':'scientficName',
        }
    total = []
    
    if taxon.rank != 'species':
        solr_q = switch.get(taxon.rank) + ':' + str(pk)
    else :
        solr_q = switch.get(taxon.rank) + ':' + taxon.name


    search_limit = 20
    facet_dataset = 'dataset:{type:terms,field:taibif_dataset_name,limit:-1,mincount:1}'
    facet_dataset_zh = 'dataset_zh:{type:terms,field:taibif_dataset_name_zh,limit:-1,mincount:1}'
    facet_json = 'json.facet={'+facet_dataset +','+facet_dataset_zh +'}'
    # r = requests.get(f'http://solr:8983/solr/taibif_occurrence/select?facet=true&q.op=OR&rows={search_limit}&q={solr_q}&{facet_json}')
    r = requests.get(f'http://solr:8983/solr/taibif_occurrence/select?facet=true&q.op=OR&rows={search_limit}&q=*:*&fq={solr_q}&{facet_json}')

    if r.status_code == 200:

        data = r.json()
        search_count = data['response']['numFound']
        search_offset = data['response']['start']
        search_results = data['response']['docs']


# dataset_occ_count
        if search_count != 0 :
            count = []
            dataset_list = []
            dataset_zh_list = []
            count = [x['count'] for x in data['facets']['dataset']['buckets']]
            dataset_list = [x['val'] for x in data['facets']['dataset']['buckets']]
            dataset_zh_list = [x['val']for x in data['facets']['dataset_zh']['buckets']]
            
            for x,y,z in zip(count, dataset_list, dataset_zh_list):
                dataset.append({'count':x,'name':y,'name_zh':z})                
        
    context = {
        'taxon': taxon,
        'dataset':dataset,
        'total':search_count,
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
