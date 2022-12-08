from django.urls import path

from . import views
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls import include
from django.urls import path

## Kuan Yu added for sitemap
from django.contrib.sitemaps.views import sitemap
from .sitemaps import DatasetSitemap
from .sitemaps import StaticSitemap
from .views import robots_txt



# Dictionary containing your sitemap classes
sitemaps = {
    'static': StaticSitemap,
    'dataset': DatasetSitemap,
}


urlpatterns = [
    path('', views.index, name='index'),
    path('publishing-data', views.publishing_data, name='publishing_data'),
    path('data-policy', views.data_policy, name='data_policy'),
    path('journals', views.journals, name='journals'),
    path('tools', views.tools, name='tools'),
    path('common-name-checker', views.common_name_checker, name='tools-common_name_checker'),
    path('cookbook', views.cookbook, name='cookbook'),
    path('cookbook/1', views.cookbook_detail_1, name='cookbook_detail_1'),
    path('cookbook/2', views.cookbook_detail_2, name='cookbook_detail_2'),
    path('cookbook/3', views.cookbook_detail_3, name='cookbook_detail_3'),
    path('contact-us', views.contact_us, name='contact_us'),
    path('plans', views.plans, name='plans'),
    path('links', views.links, name='links'),
    path('about-taibif', views.about_taibif, name='about_taibif'),
    path('about-gbif', views.about_gbif, name='about_gbif'),
    path('open-data', views.open_data, name='open_data'),
    path('data-stats', views.data_stats, name='data_stats'),
    path('export_csv',views.export_csv, name='export_csv'),
    path('i18n/', include('django.conf.urls.i18n')),
    ## Kuan Yu added for sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    # path("robots.txt", robots_txt),
    #path('test', views.test, name='test'),
    path('bar_chart', views.bar_chart, name='bar_chart'),
    path('taibif-api', views.taibif_api, name='taibif_api'),

]

