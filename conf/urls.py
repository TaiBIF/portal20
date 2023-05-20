"""conf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve

from conf import settings
from apps.data.views import (
    occurrence_view,
    dataset_view,
    search_view,
    search_view_species,
    publisher_view,
    species_view,
    search_occurrence_download_view,
)
from apps.page.views import (
    page_not_found_view,
    response_error_handler
)
# from apps.api.views import (
#     ChartMonth,
#     ChartYear,
#     taxon_bar,
# )

urlpatterns = [
    re_path('media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    path('api/', include('apps.api.urls')),
    path('search/', include('apps.data.urls')),
    #path('occurrence/search|map/', search_view, name='search-occurrence'),
    re_path(r'^occurrence/(?P<cat>search|gallery|download|map|charts|taxonomy)/$', search_view, name='search-occurrence'),
    #path('occurrence/downloadlink', search_occurrence_download_view, name='search-occurrence-download'),
    path('dataset/search/', search_view, name='search-dataset'),
    path('publisher/search/', search_view, name='search-publisher'),
    path('species/search/', search_view, name='search-species'),
    # path('species/search/', search_view_species, name='search-species'),
    path('occurrence/<str:taibif_id>', occurrence_view, name='occurrence-detail'),
    path('dataset/<uuid:taibif_dataset_id>/', dataset_view, name='dataset-detail'),
    path('publisher/<int:pk>/', publisher_view, name='publisher-detail'),
    path('species/<str:taicol_taxon_id>/', species_view, name='species-detail'),
    path('article/', include('apps.article.urls')),
    path('',  include('apps.page.urls')),
    path('admin/', admin.site.urls),
    path('500', response_error_handler),
    path('400', page_not_found_view),

    ##Kuan-Yu added for API hichart function
    # path('test_y/', ChartYear, name='ChartYear'),
    # path('test_m/', ChartMonth, name='ChartMonth'),
    # path('taxon_bar/', taxon_bar, name='taxon_bar'),

    ]

# AWS SES
#urlpatterns += (path(r'^admin/django-ses/', include('django_ses.urls')),)
handler500 = response_error_handler
handler404 = page_not_found_view

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
