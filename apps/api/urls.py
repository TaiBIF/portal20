from django.urls import path, re_path

from . import views

urlpatterns = [
    path('dataset/search/', views.search_dataset, name='api-search-dataset'),
    #path('occurrence/search/', views.search_occurrence, name='api-search-occurrence'),
    re_path('^occurrence/(?P<cat>search|taxonomy)/', views.search_occurrence, name='api-search-occurrence'),
    path('publisher/search/', views.search_publisher, name='api-search-publisher'),
    path('species/search/', views.search_species, name='api-search-species'),
    path('species/<int:pk>/', views.species_detail, name='species-detail'),
    path('taxon/tree/node/<int:pk>', views.taxon_tree_node, name='taxon-tree-branch'),
    path('data/stats/', views.data_stats, name='data-stats'),

]
