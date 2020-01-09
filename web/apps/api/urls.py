from django.urls import path

from . import views

urlpatterns = [
    path('search-page/menu', views.search_page_menu, name='api'),
]
