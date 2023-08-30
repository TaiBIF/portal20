from django.urls import path, re_path

from . import views

urlpatterns = [
    path('dataset/search/', views.search_dataset, name='api-search-dataset'),
    re_path('^occurrence/(?P<cat>search|taxonomy|charts|gallery|map|download)/', views.search_occurrence_v1, name='api-search-occurrence'),
    path('publisher/search/', views.search_publisher, name='api-search-publisher'),
    path('species/search/', views.search_species, name='api-search-species'),
    # path('species/<int:pk>/', views.species_detail, name='species-detail'),
    path('taxon/tree/node/<str:taicol_taxon_id>', views.taxon_tree_node, name='taxon-tree-branch'),
    path('data/stats/', views.data_stats, name='data-stats'),
    # path('taxon_bar/', views.taxon_bar, name='bar_chart'), ## TODO
    path('v1/occurrence', views.search_occurrence_v1, name='search-occurrence-v1'),
    path('v1/occurrence/charts', views.occurrence_search_v2, name='search-occurrence-v1-charts'),
    path('v2/occurrence/search', views.occurrence_search_v2, name='api-occurrence-search-v2'),
    path('v2/occurrence/map', views.occurrence_search_v2, name='api-occurrence-search-v2-map'),
    path('dataset/export', views.export, name='export'),
    path('v2/occurrence/get_map_species', views.get_map_species, name='get_map_species'),
    
    # 外部使用的API
    path('v2/dataset', views.dataset_api, name='api_dataset'),
    # path('v1/taxon', views.taxon_api, name='api_taxon'),
    path('v2/publisher', views.publisher_api, name='api_publisher'),
    path('v2/publisher/dataset/<int:pk>', views.publisher_dataset_api, name='api_publisher_dataset'),
    path('v2/occurrence/basic_occ', views.for_basic_occ, name='api_basic_occ'),
    path('v2/occurrence/detail_occ', views.occurrence_api, name='occurrence_api'),    
    path('v2/occurrence/raw_occ', views.raw_occ_api, name='raw_occ_api'),
    path('get_autocomplete_taxon/', views.get_autocomplete_taxon, name='get_autocomplete_taxon'),
]
