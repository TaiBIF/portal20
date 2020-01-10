from django.shortcuts import render
from django.db.models import Count, Q

from apps.data.models import Dataset, DATA_MAPPING
from utils.decorators import json_ret

@json_ret
def search_occurrence(request):
    return {'data': {}}

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

    query = Dataset.objects
    if request.GET:
        for menu_key, item_keys in request.GET.items():
            if menu_key == 'q':
                query = query.filter(Q(title__icontains=item_keys) | Q(description__icontains=item_keys))
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

    results = [{
        'title': x.title,
        'description': x.description,
        'id': x.id,
        'name': x.name,
        'num_record': x.num_record,
        'dwc_type': x.dwc_core_type_for_human_simple,
    } for x in query.all()]
    data = {
        'menus': menu_list,
        'results': results,
        'offset': 0,
        'limit': 0,
        'count': len(results)
    }

    return {'data': data }
