from django.urls import path

from . import views

urlpatterns = [
    path('', views.search, name='search'),
    #path('dataset/', views.search_dataset, name='search-dataset'),
    #path('occurrence/', views.search_occurrence, name='search-occurrence'),
    #path('api/', views.api, name='api'),
    #path('taxon/tree/', views.taxon_tree, name='taxon'),
]
