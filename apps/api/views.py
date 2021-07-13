import time
import json
import datetime
import re
import random
import csv

from django.shortcuts import render
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
import requests

from apps.data.models import (
    Dataset,
    DATA_MAPPING,
    DatasetOrganization,
    Taxon,
    RawDataOccurrence,
    SimpleData,
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

from .cached import COUNTRY_ROWS, YEAR_ROWS

def search_occurrence_v1(request):
    solr_q_list = []
    solr_q = '*.*'
    for term, values in list(request.GET.lists()):
        if term != 'menu':
            solr_q_list.append('{}={}'.format(term, ' OR '.join(values)))
    if len(solr_q_list) > 0:
        solr_q = ', '.join(solr_q_list)

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
    facet_json = 'json.facet={dataset:{type:terms,field:taibif_dataset_name},year:{type:terms,field:year},month:{type:terms,field:month},country:{type:terms,field:country}}'
    r = requests.get(f'http://solr:8983/solr/taibif/select?facet=true&q.op=OR&rows={search_limit}&q={solr_q}&{facet_json}')
    if r.status_code == 200:
        data = r.json()

        search_count = data['response']['numFound']
        search_offset = data['response']['start']
        search_results = data['response']['docs']

        for i, v in enumerate(search_results):
            ## copy fields
            date = '{}-{}-{}'.format(v['year'] if v.get('year', '') else '',
                                     v['month'] if v.get('month', '') else '',
                                     v['day'] if v.get('day', '') else '')
            search_results[i]['vernacular_name'] = v.get('vernacularName', '')
            search_results[i]['scientific_name'] = v.get('scientificName', '')
            search_results[i]['dataset'] = v['taibif_dataset_name'][0]
            search_results[i]['date'] = date
            search_results[i]['taibif_id'] = '{}__{}'.format(v['taibif_dataset_name'][0], v['_version_'])

        #search_limit = 20
        menu_year = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['facets']['year']['buckets']]
        menu_month = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['facets']['month']['buckets']]
        menu_dataset = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['facets']['dataset']['buckets']]
        menu_country = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['facets']['country']['buckets']]

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
    return JsonResponse(ret)

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
            .values('organization','organization_verbatim')\
            .exclude(organization__isnull=True)\
            .annotate(count=Count('organization'))\
            .order_by('-count')
        #publisher_query = publisher_query.filter()
        #publisher_query = ds_search.query.values('organization','organization_verbatim')\
        #                                 .exclude(organization__isnull=True)\
        #                                 .annotate(count=Count('organization'))\
        #                                 .order_by('-count')
        publisher_rows = [{
            'key':x['organization'],
            'label':x['organization_verbatim'],
            'count': x['count']
        } for x in publisher_query]
        rights_query = ds_search.query\
            .values('data_license')\
            .exclude(data_license__exact='')\
            .annotate(count=Count('data_license'))\
            .order_by('-count')
        rights_rows = [{
            'key': DATA_MAPPING['rights'][x['data_license']],
            'label':x['data_license'],
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

    species_search = SpeciesSearch(list(request.GET.lists()))
    #species_ids = list(species_search.query.values('id').all())
    #print (species_ids, len(species_ids))
    has_menu = True if request.GET.get('menu', '') else False
    menu_list = []
    if has_menu:
        menus = [
            {
                'key': 'highertaxon',
                'label': '高階分類群',
                'rows': [{
                    'key': x.id,
                    'label': x.get_name(),
                } for x in Taxon.objects.filter(rank='kingdom')],
            },
            {
                'key': 'rank',
                'label': '分類位階',
                'rows': [{
                    'key': x['key'],
                    'label': x['label'],
                    #'count': x['count']
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
