from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('publishing-data', views.publishing_data, name='publishing_data'),
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
    path('about-tibif', views.about_taibif, name='about_taibif'),
    path('about-gbif', views.about_gbif, name='about_gbif'),
    path('open-data', views.open_data, name='open_data'),
    path('data-stats', views.data_stats, name='data_stats')
]
