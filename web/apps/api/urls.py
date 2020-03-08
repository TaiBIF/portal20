from django.urls import path

from . import views

urlpatterns = [
    path('dataset/search/', views.search_dataset, name='search-dataset'),
    path('occurrence/search/', views.search_occurrence, name='search-occurrence'),
    path('publisher/search/', views.search_publisher, name='search-publisher'),
    path('species/search/', views.search_species, name='search-species'),
]
