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
    path('data-policy', views.data_policy, name='data-policy'),
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
    path('taibif-achievement',views.taibif_achievement, name='taibif-achievement'),
    path('faq',views.faq, name='faq'),
    path('download-resources',views.download_resources, name='download-resources'),
    path('thanks-list',views.thanks_list, name='thanks-list'),
    
    path('open-process',views.open_process, name='open-process'),
    path('open-standard',views.open_standard, name='open-standard'),
    path('open-metadata',views.open_metadata, name='open-metadata'),
    path('open-uplaod',views.open_uplaod, name='open-uplaod'),
    path('open-license',views.open_license, name='open-license'),
    
    path('open-timezone',views.open_timezone, name='open-timezone'),
    path('tech-open',views.tech_open, name='tech-open'),
    path('tech-book',views.tech_book, name='tech-book'),
    path('tech-workshop',views.tech_workshop, name='tech-workshop'),
    path('tech-volunteer',views.tech_volunteer, name='tech-volunteer'),
    path('tech-online-class',views.tech_online_class, name='tech-online-class'),
    path('tech-class-license',views.tech_class_license, name='tech-class-license'),
    
    
    path('data-paper',views.data_paper, name='data-paper'),
    path('data-visual',views.data_visual, name='data-visual'),
    path('data-case',views.data_case, name='data-case'),
    path('data-product',views.data_product, name='data-product'),
    
    path('data-story',views.data_story, name='data-story'),
    
    path('web-navi',views.web_navi, name='web-navi'),
    path('open-data',views.open_data, name='open-data'),
    
    
    path('i18n/', include('django.conf.urls.i18n')),
    ## Kuan Yu added for sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    # path("robots.txt", robots_txt),
    path('taibif-api', views.taibif_api, name='taibif-api'),

]

