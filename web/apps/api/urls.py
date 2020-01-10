from django.urls import path

from . import views

urlpatterns = [
    path('dataset/search/', views.search_dataset, name='search-dataset'),
    path('occurrence/search/', views.search_occurrence, name='search-occurrence'),
]
