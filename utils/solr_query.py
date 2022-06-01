import urllib
import logging
import json
import requests
from apps.api.cached import COUNTRY_ROWS

from conf.settings import ENV

from utils.map_data import convert_coor_to_grid, convert_x_coor_to_grid, convert_y_coor_to_grid

from apps.data.models import (
    taibifcode
)
if ENV in ['dev','stag']:
    # SOLR_PREFIX = 'http://solr:8983/solr/'
# if ENV == 'dev':
    # SOLR_PREFIX = 'http://54.65.81.61:8983/solr/'
    SOLR_PREFIX = 'http://solr:8983/solr/'
else:
    SOLR_PREFIX = 'http://solr:8983/solr/'

JSON_FACET_MAP = {
    'taibif_occurrence': {
        'dataset': {
            'type': 'terms',
            'field': 'taibif_dataset_name_zh',
            'mincount': 1,
            'limit': -1,
        },
        'dataset_id': {
            'type': 'terms',
            'field': 'taibif_dataset_name',
            'mincount': 1,
            'limit': -1,
        },
        'month': {
            'type': 'terms',
            'field':'month',
            'start':'1',
            'end':'13',
            'gap':'1',
            'limit': 12,
            #'mincount': 0, cause solr error?
        },
        'year': {
            'type':'terms',
            'field':'year',
            'mincount': 0,
            'limit': -1,
        },
        'country': {
            'type':'terms',
            'field':'country',
            'mincount': 0,
        },
        'publisher': {
            'type':'terms',
            'field':'publisher',
            'mincount': 0,
            'limit': -1,
        },
         'license': {
            'type':'terms',
            'field':'license',
            'mincount': 0,
        },
         'taibif_county': {
            'type':'terms',
            'field':'taibif_county',
        },
    }
}

CODE_MAPPING ={
    'county':{
        0 : '其他',
        1 : '臺北市',
        2 : '臺中市',
        3 : '基隆市',
        4 : '臺南市',
        5 : '高雄市',
        6 : '新北市',
        7 : '宜蘭縣',
        8 : '桃園市',
        9 : '嘉義市',
        10 : '新竹縣',
        11 : '苗栗縣',
        12 : '南投縣',
        13 : '彰化縣',
        14 : '新竹市',
        15 : '雲林縣',
        16 : '嘉義縣',
        17 : '屏東縣',
        18 : '花蓮縣',
        19 : '臺東縣',
        20 : '金門縣',
        21 : '澎湖縣',
        22 : '連江縣',
    }
    
}


def get_init_menu(facet_values=[]):
    # TODO better to cache in redis?
    # not cache if solr schema not steady?
    solr_default = SolrQuery('taibif_occurrence', facet_values)
    req_default = solr_default.request()
    menus = solr_default.get_menus()
    
    print("init=====")
    # set all count to zero
    for i, v in enumerate(menus):
        for x in v['rows']:
            x['count'] = 0
    return menus


class SolrQuery(object):
    '''
    solr = SolrQuery('taibif_occurrence')
    resp = solr.request(request.GET.lists())
    response = solr_ret['data']
    '''
    rows = 20

    def __init__(self, core, facet_values=[]):
        self.solr_tuples = [
            ('q.op', 'AND'),
            ('wt', 'json'),
        ]
        self.core = core
        self.facet_values = facet_values
        self.solr_error = ''
        self.solr_response = {}
        self.solr_url = ''
        self.solr_q = '*:*'

    def generate_solr_url(self, req_lists=[]):
        map_query = ''
        for key, values in req_lists:
            if key == 'q' and values[0] != '':
                self.solr_q = values[0]
            elif key == 'offset':
                self.solr_tuples.append(('start', values[0]))
            elif key == 'rows':
                self.rows = int(values[0])
                self.solr_tuples.append(('rows', self.rows))
            elif key == 'fl':
                self.solr_tuples.append(('fl', values[0]))
            elif key == 'wt':
                self.solr_tuples.remove(('wt', 'json'))
                self.solr_tuples.append(('wt', values[0]))
            elif key == 'taxon_key':
                taxon_key_list = []
                for v in values:
                    klist = v.split(':')
                    rank = klist[0]
                    if len(klist) > 1:
                        taxon_id = klist[1]
                        taxon_key_list.append(f'{rank}_key:{taxon_id}')
                #fq=(cat1:val1 OR cat2:val2 OR (cat3:(val3 AND val4)))
                self.solr_tuples.append(('fq', ' OR '.join(taxon_key_list)))
            elif key in JSON_FACET_MAP[self.core]:
                field = JSON_FACET_MAP[self.core][key]['field']
                if (field == 'taibif_dataset_name_zh'):
                    field = 'taibif_dataset_name'
                if len(values) == 1:
                    if ',' in values[0]:
                        vlist = values[0].split(',')
                        self.solr_tuples.append(('fq', f'{key}:[{vlist[0]} TO {vlist[1]}]'))
                    else:
                        if key in JSON_FACET_MAP[self.core]:
                            self.solr_tuples.append(('fq', '{}:"{}"'.format(field, values[0])))
                else:
                    self.solr_tuples.append(('fq', ' OR '.join([f'{field}:"{x}"' for x in values])))
                    #self.solr_tuples.append(('fq', 'taibif_dataset_name:A OR taibif_dataset_name:B'))
            # this get by __init__
            #elif key == 'facet':
            #    self.has_facet = True
            #    self.facet_values = values
            #-----map------#
            elif key == 'lat':
                coor_list = [ float(c) for c in values]
                y1 = convert_y_coor_to_grid(min(coor_list))
                y2 = convert_y_coor_to_grid(max(coor_list))
                map_query = "{!frange l=" + str(y1) + " u=" + str(y2) + "}grid_y"
                self.solr_tuples.append(('fq', map_query))
            elif key == 'lng':
                coor_list = [ float(c) for c in values]
                x1 = convert_x_coor_to_grid(min(coor_list))
                x2 = convert_x_coor_to_grid(max(coor_list))
                map_query = "{!frange l=" + str(x1) + " u=" + str(x2) + "}grid_x"
                self.solr_tuples.append(('fq', map_query))

        self.solr_tuples.append(('q', self.solr_q))
        self.solr_tuples.append(('rows', self.rows)) #TODO remove redundant key['rows']

        if len(self.facet_values):
            self.solr_tuples.append(('facet', 'true'))
            s = ''
            flist = []
            #print (str(JSON_FACET_MAP[self.core]).replace("'", '',).replace(' ', ''))
            for i in self.facet_values:
                if i in JSON_FACET_MAP[self.core]:
                    flist.append('{}:{}'.format(i, str(JSON_FACET_MAP[self.core][i]).replace("'", '',).replace(' ', '')))
                    #flist.append('{}:{}'.format(i, JSON_FACET_MAP[self.core][i]))
            s = ','.join(flist)
            self.solr_tuples.append(('json.facet', '{'f'{s}''}'))

        query_string = urllib.parse.urlencode(self.solr_tuples)
        self.solr_url = f'{SOLR_PREFIX}{self.core}/select?{query_string}'
        return self.solr_url

    def request(self, req_lists=[]):
        self.generate_solr_url(req_lists)

        try:
            resp =urllib.request.urlopen(self.solr_url)
            resp_dict = resp.read().decode()
            self.solr_response = json.loads(resp_dict)
        except urllib.request.HTTPError as e:
            self.solr_error = str(e)

        return {
            'solr_response': self.solr_response,
            'solr_error': self.solr_error,
        }

    def get_response(self):
        '''get solr response and convert to gbif-like response
        '''
        if not self.solr_response:
            return

        resp = self.solr_response['response']
        facets = self.solr_response.get('facets', [])

        is_last = False
        if resp['start'] + int(self.rows) >= resp['numFound']:
            is_last = True

        for i in resp['docs']:
            i['taibif_occurrence_id'] = i['taibif_occ_id']
        return {
            'offset': resp['start'],
            'limit': self.rows,
            'count': resp['numFound'],
            'results': resp['docs'],
            'endOfRecords': is_last,
            'facets': facets, # TODO: redundant with menus
        }


    def get_occurrence(self,taibif_occ_id):
        solr_q = '*:*'
        solr_fq = 'taibif_occ_id:' + str(taibif_occ_id)
        query_string = solr_fq

        url = f'{SOLR_PREFIX}{self.core}/select?q.op=AND&q={query_string}'
        try:
            resp =urllib.request.urlopen(url)
            resp_dict = resp.read().decode()
            self.solr_response = json.loads(resp_dict)
        except urllib.request.HTTPError as e:
            self.solr_error = str(e)
        return {
            'results': self.solr_response['response']['docs'],
            'solr_error': self.solr_error
        }

    def get_menus(self, key=''):
        '''for frontend menus struct
           should call get_response() before call get_menus()
        '''
        resp = self.solr_response
        if not resp or not resp.get('facets', ''):
            return []

        menus = []
        if data := resp['facets'].get('country', ''):
            rows = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['buckets']]
            menus.append({
                'key': 'country', #'countrycode',
                'label': '國家/區域',
                'rows': rows,
            })
            
        if data := resp['facets'].get('taibif_county', ''):
            rows = [{'key': str(x['val']), 'label': CODE_MAPPING['county'][x['val']], 'count': x['count']} for x in data['buckets']]
            for x  in rows:
                if x['key'] == '0':
                    rows.remove(x)
            menus.append({
                'key':'taibif_county',
                'label': '台灣縣市',
                'rows': rows,
            })
            
        if data := resp['facets'].get('year', ''):
            #menu_year = [{'key': 0, 'label': 0, 'count': 0,'year_start':1990,'year_end':2021}]
            rows = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['buckets']]
            # TODO
            menus.append({
                'key': 'year',
                'label': '年份',
                'rows':rows,
            })
        if data := resp['facets'].get('month', ''):
            rows = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in sorted(data['buckets'], key=lambda x: x['val'])]
            menus.append({
                'key': 'month',
                'label': '月份',
                'rows': rows,
            })
        if data := resp['facets'].get('dataset', ''):
            dataset_id = resp['facets'].get('dataset_id', '')
            rows = []
            for x in range(len(data['buckets'])):
                if x < len(dataset_id['buckets']): # prevent limited dataset_id buckets cause index error
                    rows.append({
                        'key': dataset_id['buckets'][x]['val'],
                        'label': data['buckets'][x]['val'],
                        'count': data['buckets'][x]['count']
                    })
            # rows = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['buckets']]
            menus.append({
                'key': 'dataset',
                'label': '資料集',
                'rows': rows,
            })
        if data := resp['facets'].get('publisher', ''):
            rows = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['buckets']]
            menus.append({
                'key':'publisher',
                'label': '發布單位',
                'rows': rows,
            })
        if data := resp['facets'].get('license', ''):
            rows = [{'key': x['val'], 'label': x['val'], 'count': x['count']} for x in data['buckets']]
            menus.append({
                'key':'license',
                'label': 'CC授權',
                'rows': rows,
            })
            
        if key == '':
            return menus
        else:
            for menu in menus:
                if menu['key'] == key:
                    return menu
