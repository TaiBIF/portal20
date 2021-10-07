
from django.core.cache import cache
from utils.solr_query import SolrQuery
from utils.map_data import get_geojson

#----------------- defaul map geojson -----------------#
default_solr = SolrQuery('taibif_occurrence')
default_solr_url = default_solr.generate_solr_url()
default_map_geojson = get_geojson(default_solr_url)
cache.set('default_map_geojson', default_map_geojson, 2592000)

resp = default_solr.get_response()
cache.set('default_solr_count', resp['count'] if resp else 0, 2592000)

#----------------- defaul map geojson -----------------#
