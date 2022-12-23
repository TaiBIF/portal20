from django.urls import path, re_path

from . import views

urlpatterns = [
    path('search/', views.article_search, name='article-search'),
    path('category/<str:category>/', views.article_list, name='article-list'),
    path('tag/<str:tag_name>/', views.article_tag_list, name='article-tag-list'),
    path('<int:pk>/', views.article_detail, name='article-detail-id'),
    #path('<int:pk>/<slug:slug>/', views.article_detail, name='article-detail-slug'),
]
