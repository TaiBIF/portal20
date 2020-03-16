from django.urls import path, re_path

from . import views

urlpatterns = [
    path('category/<str:category>/', views.article_list, name='article-list'),
    path('<int:pk>/', views.article_detail, name='article-detail'),
    re_path(r'(?P<slug>[\w-]+)/$', views.article_detail, name='article-detail'),
]
