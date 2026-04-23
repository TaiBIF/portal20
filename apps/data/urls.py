from django.urls import path

from . import views

urlpatterns = [
    path('', views.search_all, name='search_all'),
    path('occurrence/download/', views.search_occurrence_download_view, name='download-occurrence'),
    path('dataset/', views.search_view, {'cat': 'dataset'}, name='search-dataset'),
    path('publisher/', views.search_view, {'cat': 'publisher'}, name='search-publisher'),
]
