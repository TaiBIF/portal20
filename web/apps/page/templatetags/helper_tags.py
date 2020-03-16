from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter

import markdown as md

register = template.Library()

@register.filter()
@stringfilter
def markdown(value):
    return md.markdown(value, extensions=['markdown.extensions.fenced_code'])


@register.simple_tag
def get_pagination_info(object_list, args):
    total = object_list.paginator.num_pages
    n = object_list.number
    rest = ['...']
    #print (total, n)

    # page_range
    page_range = []
    if total >= 10:
        if n <= 5:
            page_range = list(object_list.paginator.page_range[0:9]) + rest
        elif n <= total - 4:
            page_range = rest + list(object_list.paginator.page_range[n-5:n+4]) + rest
        else:
            page_range = rest + list(object_list.paginator.page_range[total-9:total+1])
    else:
        page_range = object_list.paginator.page_range

    # query_string
    query_string = ''
    qs_list = ['{}={}'.format(i, args[i]) for i in args if i != 'page']
    if qs_list:
        query_string = '&{}'.format('&'.join(qs_list))

    return {
        'page_range': page_range,
        'append_query_string': query_string
    }

@register.simple_tag
def get_taibif_env():
    return 'local' #settings.TAIBIF_ENV # TODO
