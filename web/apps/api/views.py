import timeit

from django.shortcuts import render
from django.db.models import Count, Q
from apps.data.models import Dataset, DATA_MAPPING
from apps.data.models import RawDataOccurrence
from utils.decorators import json_ret

from .cached import COUNTRY_ROWS, YEAR_ROWS
@json_ret
def search_occurrence(request):
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
    s = json.dumps(year_rows_update)
    '''
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

    query_start = timeit.timeit()
    #query = RawDataOccurrence.objects.values('basisofrecord', 'vernacularname', 'countrycode', 'scientificname', 'taibif_id', 'taibif_dataset_name', 'taibif_dataset_name__title')
    #query_rows = RawDataOccurrence.objects.all()[:50]

    page = 1
    query = RawDataOccurrence.objects.values('basisofrecord', 'vernacularname', 'countrycode', 'scientificname', 'taibif_id', 'taibif_dataset_name')
    if request.GET:
        for menu_key, item_keys in request.GET.items():
            if menu_key == 'q':
                query = query.filter(Q(vernacularname__icontains=item_keys) | Q(scientificname__icontains=item_keys))
            if menu_key == 'core':
                print (item_keys,'--')
                d = DATA_MAPPING['core'][item_keys]
                query = query.filter(dwc_core_type__exact=d)
            if menu_key == 'year':
                for key in item_keys.split(','):
                    query = query.filter(year__exact=key)
            if menu_key == 'month':
                for key in item_keys.split(','):
                    query = query.filter(month__exact=key)
            if menu_key == 'countrycode':
                for key in item_keys.split(','):
                    query = query.filter(countrycode__exact=key)
            if menu_key == 'dataset':
                for key in item_keys.split(','):
                    query = query.filter(taibif_dataset_name__exact=key)
            if menu_key == 'page':
                page = int(item_keys)

    offset = (page-1) * RawDataOccurrence.NUM_PER_PAGE
    limit = page * RawDataOccurrence.NUM_PER_PAGE
    query_fin = query.all()[offset:limit]
    #count = query.count()
    count = '--'
    results = [{
        'taibif_id': x['taibif_id'],
        'basis_of_record': x['basisofrecord'],
        'vernacular_name': x['vernacularname'],
        'country_code': x['countrycode'],
        'scientific_name': x['scientificname'],
        'dataset':  x['taibif_dataset_name']
    } for x in query_fin]
    query_elapsed = timeit.timeit() - query_start

    data = {
        'menus': menu_list,
        'results': results,
        'offset': 0,
        'limit': 0,
        'count': count,
        'elapsed': query_elapsed
    }
    return {'data': data}

@json_ret
def search_dataset(request):

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

    page = 1
    query = Dataset.objects.exclude(status='Private')
    if request.GET:
        for menu_key, item_keys in request.GET.items():
            if menu_key == 'q':
                query = query.filter(Q(title__icontains=item_keys) | Q(description__icontains=item_keys))
            if menu_key == 'core':
                print (item_keys,'--')
                d = DATA_MAPPING['core'][item_keys]
                query = query.filter(dwc_core_type__exact=d)
            if menu_key == 'publisher':
                for key in item_keys.split(','):
                    query = query.filter(organization__exact=key)
            if menu_key == 'rights':
                rights_reverse_map = {v: k for k,v in DATA_MAPPING['rights'].items()}
                for key in item_keys.split(','):
                    query = query.filter(data_license__exact=rights_reverse_map[key])
            if menu_key == 'country':
                for key in item_keys.split(','):
                    query = query.filter(country__exact=key)
            if menu_key == 'page':
                page = int(item_keys)

    offset = (page-1) * Dataset.NUM_PER_PAGE
    limit = page * Dataset.NUM_PER_PAGE
    query_fin = query.all()[offset:limit]

    results = [{
        'title': x.title,
        'description': x.description,
        'id': x.id,
        'name': x.name,
        'num_record': x.num_record,
        'dwc_type': x.dwc_core_type_for_human_simple,
    } for x in query_fin]
    data = {
        'menus': menu_list,
        'results': results,
        'offset': offset,
        'limit': limit,
        'count': query.count()
    }

    return {'data': data }
