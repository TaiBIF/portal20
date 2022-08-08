import re
import csv
import codecs
import json
import requests

import os
import environ
from django.shortcuts import render, get_object_or_404, redirect
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
)
from django.db.models import (
    Q,
    F,
    Count,
    Sum
)
from django.conf import settings
from django.contrib import messages
from apps.data.models import (
    Dataset,
    Taxon,
    #SimpleData,
)
from apps.article.models import Article
from .models import Post, Journal
from utils.mail import taibif_mail_contact_us

from apps.data.helpers.stats import get_home_stats
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET
from django.utils.translation import activate

def act_lang(func):
    def wrapper(*args, **kwargs):
        activate('zh-hant') # default 中文
        resp = func(*args, **kwargs)
        return resp
    return wrapper

# @act_lang
def index(request):
    news_list = Article.objects.filter(category='NEWS').all()[0:4]
    event_list = Article.objects.filter(category='EVENT').all()[0:4]
    update_list = Article.objects.filter(category='UPDATE').all()[0:4]
    #topic_list = Article.objects.filter(category__in=['SCI', 'TECH', 'PUB']).order_by('?').all()[0:10]
    topic_list = Article.objects.filter(is_homepage=True).order_by('?').all()[0:10]

    url = f'http://solr:8983/solr/taibif_occurrence/select?indent=true&q.op=OR&q=*%3A*&rows=0'
    r = requests.get(url).json()   
    occ_num =  r['response']['numFound']

    dataset_num = Dataset.objects.filter(status='PUBLIC').count()
    # taxon_cover = len(occ_result['facets']['taxon_id']['buckets'])
         
    context = {
        'news_list': news_list,
        'event_list': event_list,
        'update_list': update_list,
        'topic_list': topic_list,
        'stats': get_home_stats(),
        'dataset_num':dataset_num,
        'occ_num':occ_num,
        # 'taxon_cover':taxon_cover,
    }

    return render(request, 'index.html', context)

# @act_lang
def publishing_data(request):
    return render(request, 'publishing-data.html')

# @act_lang
def data_policy(request):
    return render(request, 'data-policy.html')

# @act_lang
def journals(request):
    Journal_url = Journal.objects.all()

    return render(request,'journals.html', locals())

# @act_lang
def cookbook(request):
    return render(request, 'cookbook.html')

# @act_lang
def cookbook_detail_1(request):
    return render(request, 'cookbook-detail-1.html')

# @act_lang
def cookbook_detail_2(request):
    return render(request, 'cookbook-detail-2.html')

# @act_lang
def cookbook_detail_3(request):
    return render(request, 'cookbook-detail-3.html')

# @act_lang
def tools(request):
    return render(request, 'tools.html')

# @act_lang
def contact_us(request):
    if request.method == 'GET':
        return render(request, 'contact-us.html')
    elif request.method == 'POST':
        ''' Begin reCAPTCHA validation '''
        recaptcha_response = request.POST.get('h-captcha-response')
        # print(recaptcha_response)
        data = {
            'secret': settings.HCAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://hcaptcha.com/siteverify', data=data)
        result = r.json()
        ''' End reCAPTCHA validation '''
        
        if result['success'] == False:
            messages.error(request, '請進行驗證，謝謝')
            return redirect('contact_us')
        
        if re.search("\?", request.POST.get('cat','')) :
            messages.error(request, '請進行驗證，謝謝')
            return redirect('contact_us')
        
        data = {
            'name':  request.POST.get('name', ''),
            'cat': request.POST.get('cat', ''),
            'email': request.POST.get('email', ''),
            'content': request.POST.get('content', ''),
        }
        context = taibif_mail_contact_us(data)
        #context = taibif_send_mail(subject, content, settings.SERVICE_EMAIL, to_list)

        return render(request, 'contact-us.html', context)

@act_lang
def plans(request):
    return render(request, 'plans.html')

# @act_lang
def links(request):
    Post_url = Post.objects.all()
    return render(request,'links.html', locals())

# @act_lang
def about_taibif(request):
    return render(request, 'about-taibif.html')

# @act_lang
def about_gbif(request):
    return render(request, 'about-gbif.html')

# @act_lang
def open_data(request):
    return render(request, 'open-data.html')

# @act_lang
def data_stats(request):
    is_most = request.GET.get('most', '')

    query = Dataset.objects #.exclude(status='Private')
    if is_most:
        query = query.filter(is_most_project=True)

    context = {
        'dataset_list': query.order_by(F('pub_date').desc(nulls_last=True)).all(),
        'env': settings.ENV
    }
    return render(request, 'data-stats.html', context)

def common_name_checker(request):
    global results
    if request.method == 'GET':
        q = request.GET.get('q', '')
        sep = request.GET.get('sep', '')
        context = {
            'q': q,
            'sep': sep,
        }
        return render(request, 'tools-common_name_checker.html', context)
    elif request.method == 'POST':
        
        q = request.POST.get('q', '')
        sep = request.POST.get('sep', 'n')

        if not q:
            context = {
                'message': {
                    'head': '輸入錯誤',
                    'content': '請輸入中文名',
                }
            }
            return render(request, 'tools-common_name_checker.html', context)

        if q in ['台灣', '臺灣']:
            context = {
                'message': {
                    'head': '結果太多',
                    'content': '請輸入更完整中文名',
                },
                'sep': sep,
                'q': q,
            }
            return render(request, 'tools-common_name_checker.html', context)

        if not sep:
            sep = 'n'
        results = []
        if sep not in [',', 'n']:
            return HttpResponseNotFound('err input')

        sep_real = '\n' if sep == 'n' else sep
        cname_list = q.split(sep_real)
        cname_list = list(set(cname_list))

        #taiwan_char_check_exclude = ['台灣留鳥', '台灣過境', '台灣亞種', '台灣特有亞種']
        for cn in cname_list:
            cn = cn.strip()

            q_replace = ''
            if '台灣' in cn:
                q_replace = cn.replace('台灣', '臺灣')

            if '臺灣' in cn:
                q_replace = cn.replace('臺灣', '台灣')

            row = {
                'common_name': cn,
                'match_type': 'no match',
                'match_list': []
            }
            taxa = Taxon.objects.filter(rank='species')
            if q_replace:
                row['q_replace'] = q_replace
                taxa = Taxon.objects.filter(Q(name_zh__icontains=cn) | Q(name_zh__icontains=q_replace)).all()
            else:
                taxa = Taxon.objects.filter(name_zh__icontains=cn).all()

            if taxa:
                row['match_type'] = 'match'

            for t in taxa:
                row['match_list'].append(t)
            results.append(row)

        context = {
            'results': results,
            'q': q,
            'sep': sep,
        }
        if 'export_csv' in request.POST:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="users.csv"'
            response.write(codecs.BOM_UTF8)

            writer = csv.writer(response)
            print(request)
            

            for row in results: 
                writer.writerow(row['match_list'])

            return response
    return render(request, 'tools-common_name_checker.html', context)



def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'
    response.write(codecs.BOM_UTF8)

    writer = csv.writer(response)
    print(request)
    

    for row in results: 
        writer.writerow(row['match_list'])

    return response

def trans(request):
    translate_str = _("這裡放需要翻譯的文字")
    context = {"translate_str": translate_str}
    return render(request, 'index.html', context)

@require_GET
def robots_txt(request):

    if os.environ.get('ENV')=='prod':
        lines = [
            "User-Agent: *",
            "Disallow: /admin/",
        ]

        return HttpResponse("\n".join(lines), content_type="text/plain")

    else:
        lines = [
            "User-Agent: *",
            "Disallow: /",
        ]

        return HttpResponse("\n".join(lines), content_type="text/plain")



## Kuan-Yu added for API occurence record


def test(request):
    Yearquery = SimpleData.objects \
        .filter(scientific_name='Rana latouchii') \
        .values('scientific_name', 'vernacular_name', 'year') \
        .exclude(year__isnull=True) \
        .annotate(count=Count('year')) \
        .order_by('-count')

    year_rows = [{
        'key': x['scientific_name'],
        'label': x['vernacular_name'],
        'year': x['year'],
        'count': x['count']
    } for x in Yearquery]



    context = {
            'occurrence_list': year_rows,
        }
    return render(request, 'test.html', context)


###example
filt1 = 'speices'
filt2 = 'database'
pk1 = 'Rana latouchii'
pk2 = 'manager_17_15'
pk3 = 'Rana longicrus'
pk4 = 'e10100001_4_10'

def bar_chart(request):
    ## Use species find
    if filt1 == filt1:

        species = SimpleData.objects.filter(Q(scientific_name=pk1)) \
            .values('taxon_kingdom_id', 'taxon_phylum_id','taxon_class_id','taxon_order_id','taxon_family_id','taxon_genus_id', 'taxon_species_id') \
            .exclude(
            Q(taxon_kingdom_id__isnull=True) | Q(taxon_phylum_id__isnull=True) | Q(taxon_class_id__isnull=True) | Q(
                taxon_order_id__isnull=True) | Q(taxon_family_id__isnull=True) | Q(taxon_genus_id__isnull=True) | Q(
                taxon_species_id__isnull=True))[:1]

    context = {
        'kingdom': Taxon.objects.get(id=species[0]['taxon_kingdom_id']),
        'phylum': Taxon.objects.get(id=species[0]['taxon_phylum_id']),
        'class': Taxon.objects.get(id=species[0]['taxon_class_id']),
        'order': Taxon.objects.get(id=species[0]['taxon_order_id']),
        'family': Taxon.objects.get(id=species[0]['taxon_family_id']),
        'genus': Taxon.objects.get(id=species[0]['taxon_genus_id']),
        'species': Taxon.objects.get(id=species[0]['taxon_species_id']),

    }




    return render(request, 'bar_chart.html',context)













