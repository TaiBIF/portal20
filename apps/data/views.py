import time
from urllib.parse import urlencode
import re
import datetime
import csv


from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count
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
    RawDataOccurrence,
    DatasetOrganization,
    SimpleData,
)
from .helpers.species import get_species_info
from .helpers.mod_search import (
    OccurrenceSearch,
    DatasetSearch,
    PublisherSearch,
    SpeciesSearch,
)

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
                    'label': '發布者',
                    'rows': publisher_rows
                },
            ]
        }
        return render(request, 'search_all.html', context)



def occurrence_view(request, taibif_id):
    occurrence = get_object_or_404(RawDataOccurrence, taibif_id=taibif_id)


    lat = 0
    lon = 0
    if occurrence.simple_data.latitude:
        lat = occurrence.simple_data.latitude
    elif occurrence.decimallatitude:
        lat = occurrence.decimallatitude

    if occurrence.simple_data.longitude:
        lon = occurrence.simple_data.longitude
    elif occurrence.decimallatitude:
        lon = occurrence.decimallongitude

    terms = {}
    for i in occurrence._meta.get_fields():
        if not i.is_relation and\
           i.column not in ['taibif_id', 'taibif_dataset_name']:
            x = getattr(occurrence, i.name, '')
            if x:
                terms[i.column] = x


    context = {
        'occurrence': occurrence,
        'terms': terms,
    }
    if lat and lon:
        context['map_view'] =  [lat, lon]

    return render(request, 'occurrence.html', context)

def dataset_view(request, name):

    try:
        dataset = Dataset.public_objects.get(name=name)


        #Count the number of longitude and latitude
        dataset_s = SimpleData.objects.filter(taibif_dataset_name = name).values_list('longitude','latitude','year','taxon_family_id',
                                                                                      'taxon_family_id')

        count_long = [item[0] for item in dataset_s]
        LonNum =  "{:.0%}".format(sum(1 for _ in filter(None.__ne__, count_long))/len(dataset_s))

        count_lat = [item[1] for item in dataset_s]
        LatNum = "{:.0%}".format(sum(1 for _ in filter(None.__ne__, count_lat))/len(dataset_s))

        count_yr = [item[2] for item in dataset_s]
        YrNum = "{:.0%}".format(sum(1 for _ in filter(None.__ne__, count_yr)) / len(dataset_s))

        count_fam = [item[3] for item in dataset_s]
        TaxNum = "{:.0%}".format(sum(1 for _ in filter(None.__ne__, count_fam)) / len(dataset_s))
        FamNum = len(set(count_fam))

        count_sp = [item[4] for item in dataset_s]
        SpNum = len(set(count_sp))

        #dataset_o = RawDataOccurrence.objects.filter(taibif_dataset_name=name).values_list('family')


        

    except Dataset.DoesNotExist:
        raise Http404("Dataset does not exist")

    return render(request, 'dataset.html', {'dataset': dataset, 'LonNum':LonNum, 'LatNum':LatNum,'YrNum':YrNum, 'TaxNum':TaxNum,
                                            'FamNum':FamNum, 'SpNum':SpNum})






def publisher_view(request, pk):
    context = {}
    context['publisher'] = get_object_or_404(DatasetOrganization, pk=pk)
    return render(request, 'publisher.html', context)

def species_view(request, pk):
    context = {}
    taxon = get_object_or_404(Taxon, pk=pk)
    

    q = RawDataOccurrence.objects.values('taibif_dataset_name', 'decimallatitude', 'decimallongitude').filter(scientificname=taxon.name).all()
    

    rank_key = 'taxon_{}_id'.format(taxon.rank)
    occur_search = OccurrenceSearch([(rank_key, [taxon.id])])
    res = occur_search.get_results()
    #print (occur_search.filters)
    

    '''q = SimpleData.objects.values('latitude', 'longitude').filter(taxon_species_id=pk).all()
    # q.count()
    occurrence_list = []
    rows = None
    lat = 0
    lng = 0
    if taxon.rank == 'species':
        sp_info = get_species_info(taxon)
        # HACK species 先全抓, 高層的資料多, 效能差
        rows = q.all()
    else:
        rows = q.all()[:20]
    print(rows)


    for r in rows:
        if r['latitude'] and r['longitude']:
            lat += float(r['latitude'])
            lng += float(r['longitude'])
            occurrence_list.append({
                #'taibif_dataset_name': r['taibif_dataset_name'],
                'decimallatitude': float(r['latitude']),
                'decimallongitude': float(r['longitude']),
            })


    n = len(occurrence_list)'''


    ## Kuan-Yu add : for counting dataset number
    SetNum = SimpleData.objects.values('taibif_dataset_name').filter(taxon_species_id=pk).all()
    dataset_list = SetNum.annotate(dataset=Count('taibif_dataset_name'))

    ## For map
    MapList = RawDataOccurrence.objects.values('taibif_dataset_name', 'decimallatitude', 'decimallongitude').filter(scientificname=taxon.name).all()

    lat = 0
    lon = 0

    test = []
    for m in MapList:
        if m['decimallatitude'] and m['decimallatitude']:

            lat = float(m['decimallatitude'])
            lon = float(m['decimallongitude'])

            test.append([lat,lon])
    #print(test[0])


    context = {
        'taxon': taxon,
        'occurrence_list': [],
        'dataset_list': dataset_list

    }
    if taxon.rank == 'species':
        context['species_info'] = get_species_info(taxon)
    if test:
       context['map_view'] = test[0]





    #if n:
    #   context['map_view'] = [lat/n, lng/n]
    #n =
    return render(request, 'species.html', context)

def search_view(request):
    context = {'env': settings.ENV}
    return render(request, 'search.html', context)

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
