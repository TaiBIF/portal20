from django.urls import path

from . import views

urlpatterns = [
    path('', views.search, name='search'),
    #path('api/', views.api, name='api'),
    #path('taxon/tree/', views.taxon_tree, name='taxon'),
]
