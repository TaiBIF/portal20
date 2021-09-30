from django.urls import path, re_path

from . import views

urlpatterns = [
    path('dataset/search/', views.search_dataset, name='api-search-dataset'),
    #path('occurrence/search/', views.search_occurrence, name='api-search-occurrence'),
    re_path('^occurrence/(?P<cat>search|taxonomy|charts|gallery|map|download)/', views.search_occurrence_v1, name='api-search-occurrence'),
    path('publisher/search/', views.search_publisher, name='api-search-publisher'),
    path('species/search/', views.search_species, name='api-search-species'),
    path('species/<int:pk>/', views.species_detail, name='species-detail'),
    path('taxon/tree/node/<int:pk>', views.taxon_tree_node, name='taxon-tree-branch'),
    path('data/stats/', views.data_stats, name='data-stats'),
    path('taxon_bar/', views.taxon_bar, name='bar_chart'), ## TODO
    path('v1/occurrence', views.search_occurrence_v1, name='search-occurrence-v1'),
    path('v1/occurrence/charts', views.search_occurrence_v1_charts, name='search-occurrence-v1-charts'),
    path('v2/occurrence/search', views.occurrence_search_v2, name='api-occurrence-search-v2'),
    path('dataset/export', views.export, name='export'),
    path('v2/occurrence/map', views.search_occurrence_v2_map, name='api-occurrence-search-v2-map'),
]
