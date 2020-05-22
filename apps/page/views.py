import re
import csv
import codecs

from django.shortcuts import render
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
)
from django.db.models import (
    Q,
    F,
)
from django.conf import settings

from apps.data.models import (
    Dataset,
    Taxon,
)
from apps.article.models import Article
from .models import Post, Journal
from utils.mail import taibif_mail_contact_us

from apps.data.helpers.stats import get_home_stats
from django.utils.translation import ugettext as _


def index(request):

    news_list = Article.objects.filter(category='NEWS').all()[0:4]
    event_list = Article.objects.filter(category='EVENT').all()[0:4]
    update_list = Article.objects.filter(category='UPDATE').all()[0:4]
    #topic_list = Article.objects.filter(category__in=['SCI', 'TECH', 'PUB']).order_by('?').all()[0:10]
    topic_list = Article.objects.filter(is_homepage=True).order_by('?').all()[0:10]

    context = {
        'news_list': news_list,
        'event_list': event_list,
        'update_list': update_list,
        'topic_list': topic_list,
        'stats': get_home_stats(),
    }

    return render(request, 'index.html', context)

def publishing_data(request):
    return render(request, 'publishing-data.html')

def journals(request):
    Journal_url = Journal.objects.all()

    return render(None,'journals.html', locals())


def cookbook(request):
    return render(request, 'cookbook.html')

def cookbook_detail_1(request):
    return render(request, 'cookbook-detail-1.html')

def cookbook_detail_2(request):
    return render(request, 'cookbook-detail-2.html')

def cookbook_detail_3(request):
    return render(request, 'cookbook-detail-3.html')

def tools(request):
    return render(request, 'tools.html')

def contact_us(request):
    if request.method == 'GET':
        return render(request, 'contact-us.html')
    elif request.method == 'POST':
        data = {
            'name':  request.POST.get('name', ''),
            'cat': request.POST.get('cat', ''),
            'email': request.POST.get('email', ''),
            'content': request.POST.get('content', ''),
        }
        context = taibif_mail_contact_us(data)
        #context = taibif_send_mail(subject, content, settings.SERVICE_EMAIL, to_list)

        return render(request, 'contact-us.html', context)

def plans(request):
    return render(request, 'plans.html')

def links(request):
    Post_url = Post.objects.all()
    return render(None,'links.html', locals())

def about_taibif(request):
    return render(request, 'about-taibif.html')

def about_gbif(request):
    return render(request, 'about-gbif.html')

def open_data(request):
    return render(request, 'open-data.html')

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
    return render(request, 'tools-common_name_checker.html', context)



def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'
    response.write(codecs.BOM_UTF8)

    writer = csv.writer(response)
    
    

    for row in results: 
        writer.writerow(row['match_list'])

    return response

def trans(request):
    translate_str = _("這裡放需要翻譯的文字")
    context = {"translate_str": translate_str}
    return render(request, 'index.html', context)


