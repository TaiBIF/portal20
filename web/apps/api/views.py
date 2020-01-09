from django.shortcuts import render
from django.db.models import Count

from apps.data.models import Dataset
from utils.decorators import json_ret

@json_ret
def search_page_menu(request):
    context = {
        'leftbar': {},
        'data_list': []
    }
    context['leftbar']['publisher'] = list(Dataset.objects.values('organisation').exclude(organisation__exact='').annotate(count=Count('organisation')).order_by('-count'))
    #context['leftbar']['country'] = Dataset.objects.values('country').exclude(country__exact='').annotate(count=Count('country')).order_by('-count')
    #context['leftbar']['data_license'] = Dataset.objects.values('data_license').exclude(data_license__exact='').annotate(count=Count('data_license')).order_by('-count')

    #context['data_list'] = Dataset.objects.all()
    return {'data':context}
