"""conf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf.urls import url
from django.views.static import serve

from conf import settings
from apps.data.views import occurrence_view, dataset_view, search_view

urlpatterns = [
    url('^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    path('api/', include('apps.api.urls')),
    path('search/', include('apps.data.urls')),
    path('occurrence/<int:pk>', occurrence_view, name='occurrence'),
    re_path('(?P<search_type>dataset|occurrence)/search/', search_view, name='search'),
    path('dataset/<name>/', dataset_view, name='dataset-detail'),
    path('article/', include('apps.article.urls')),
    path('',  include('apps.page.urls')),
    path('admin/', admin.site.urls),
]
