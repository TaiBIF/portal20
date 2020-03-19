from django.urls import path

from . import views

urlpatterns = [
    path('dataset/search/', views.search_dataset, name='search-dataset'),
    path('occurrence/search/', views.search_occurrence, name='search-occurrence'),
    path('publisher/search/', views.search_publisher, name='search-publisher'),
    path('species/search/', views.search_species, name='search-species'),
    path('species/<int:pk>/', views.species_detail, name='species-detail'),
    path('taxon/tree/', views.taxon_tree, name='taxon-tree'),
    path('data/stats/', views.data_stats, name='data-stats'),
]
