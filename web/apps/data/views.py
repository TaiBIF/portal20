import time
from urllib.parse import urlencode
import re

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect

from .models import Taxon, Occurrence, Dataset

def do_search(q, page):

    begin_time = time.time()
    #query = Catalog.objects.using('gbif').values('guid','institutioncode','country', 'locality','basisofrecord', 'longitude', 'latitude','scientificname','scientificnameinchinese', 'kingdom', 'phylum', 'class_field', 'order', 'family', 'genus', 'species', 'kingdominchinese', 'phyluminchinese', 'classinchinese', 'orderinchinese', 'familyinchinese', 'genusinchinese', 'speciesinchinese', 'name_code').order_by('scientificname')
    query = Occurrence.objects.values('id','dataset_id','country', 'locality','basis_of_record', 'decimal_longitude', 'decimal_latitude','scientific_name', 'kingdom', 'phylum', 'class_field', 'order_field', 'family', 'genus', 'vernacular_name', 'dataset_name').order_by('scientific_name')

    #mtv = MgTimeEvent()

    #if kingdom:
    #    query = query.filter(kingdom=kingdom)
    q = q.strip()
    if q:
        if len(q) == len(q.encode()):
            # is ascii
            query = query.filter(scientific_name__icontains=q)
        else:
            query = query.filter(Q(scientific_name__icontains=q) |
                                 Q(vernacular_name__icontains=q))
    #query = query.filter(kingdominchnese=q)
    #query = query.filter(phylum=q)
    #query = query.filter(phyluminchineem=q)

    rows = []#query.all()

    paginator = Paginator(rows, 50)
    occurrence_list = paginator.get_page(page)

    end_time = time.time()
    return {
        'occurrence_list': occurrence_list,
        'search_time': round((end_time - begin_time), 2)
    }

def search(request):
    page = 0
    q = ''
    if request.method == 'POST':
        page = request.POST.get('page', 0)
        q = request.POST.get('q', '')
        url = request.path
        qs = {}
        if page:
            qs['page'] = page
        if q:
            qs['q'] = q

        if qs:
            url += '?' + urlencode(qs)
        return HttpResponseRedirect(url)
    else:
        page = request.GET.get('page', '')
        q = request.GET.get('q', '')

    #kingdom = request.GET.get('kingdom', '')

    result = do_search(q, page)
    result['search_tags'] = []
    for i in request.GET:
        if i != 'page':
            if i == 'q':
                result['search_tags'].append(request.GET[i])
            else:
                result['search_tags'].append('{}:{}'.format(i, request.GET[i]))

    return render(request, 'search.html', result)


def occurrence_view(request, pk):
    context = {}
    context['occur'] = get_object_or_404(Occurrence, pk=pk)
    return render(request, 'occurrence.html', context)

def dataset_view(request, name):
    context = {}
    context['dataset'] = get_object_or_404(Dataset, name=name)
    return render(request, 'dataset.html', context)

def search_view(request, search_type):
    return render(request, 'search.html')
