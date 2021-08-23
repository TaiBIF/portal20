from django.contrib.sitemaps import Sitemap
from apps.data.models import (
    Taxon,
    Occurrence,
    Dataset,
    #RawDataOccurrence,
    DatasetOrganization,
    #SimpleData,
)
from django.contrib import sitemaps
from django.urls import reverse


class DatasetSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7


    def items(self):
        return Dataset.objects.all()


    def lastmod(self, obj):
        return obj.pub_date



class StaticSitemap(sitemaps.Sitemap):
     priority = 0.8
     changefreq = 'weekly'

     # The below method returns all urls defined in urls.py file
     def items(self):
         return ['about_taibif', 'data_stats', 'open_data']

     def location(self, item):
         return reverse(item)
