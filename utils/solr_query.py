import urllib
import logging
import json
import requests
import datetime

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
        'dataset_name': {
            'type': 'terms',
            'field': 'taibif_dataset_name_zh',
            'mincount': 1,
            'limit': -1,
        },
        'month': {
            'type': 'terms',
            'field':'taibif_month',
            'limit': -1,
            #'mincount': 0, cause solr error?
        },
        'year': {
            'type':'terms',
            'field':'taibif_year',
            'limit': -1,
        },
        'country': {
            'type':'terms',
            'field':'taibif_country',
            'mincount': 0,
            'limit': -1,
        },
        'publisher': {
            'type':'terms',
            'field':'publisher',
            'mincount': 0,
            'limit': -1,
        },
        'license': {
            'type':'terms',
            'field':'taibif_license',
            'mincount': 0,
        },
        'county': {
            'type':'terms',
            'field':'taibif_county',
            'limit': -1,
        },
        'taxon_id': {
            'type':'terms',
            'field':'taxon_id',
            'mincount': 1,
            'limit': -1,
        },
        'taibif_error': {
            'type':'terms',
            'field':'taibif_error',
            'mincount': 1,
        },
        'CoordinateInvalid': {
            'type':'terms',
            'field':'CoordinateInvalid',
            'mincount': 1,
        },
        'TaxonMatchNone': {
            'type':'terms',
            'field':'TaxonMatchNone',
            'mincount': 1,
        },
        'RecordedDateInvalid': {
            'type':'terms',
            'field':'RecordedDateInvalid',
            'mincount': 1,
        },
        'forest_reserves': {
            'type':'terms',
            'field':'forest_reserves',
            'mincount': 0,
            'limit': -1,
        },
        'wildlife_refuges': {
            'type':'terms',
            'field':'wildlife_refuges',
            'mincount': 0,
            'limit': -1,
        },
        'taibif_datasetKey': {
            'type':'terms',
            'field':'taibif_datasetKey',
            'mincount': 0,
            'limit': -1,
        },
        'selfProduced': {
            'type':'terms',
            'field':'selfProduced',
            'mincount': 0,
            'limit': -1,
        },
    }
}

CODE_MAPPING ={
    'county':{
        None : '其他',
        'Taipei City' : '臺北市',
        'Taichung City' : '臺中市',
        'Keelung City' : '基隆市',
        'Tainan City' : '臺南市',
        'Kaohsiung City' : '高雄市',
        'New Taipei City' : '新北市',
        'Yilan County' : '宜蘭縣',
        'Taoyuan City' : '桃園市',
        'Chiayi City' : '嘉義市',
        'Hsinchu County' : '新竹縣',
        'Miaoli County' : '苗栗縣',
        'Nantou County' : '南投縣',
        'Changhua County' : '彰化縣',
        'Hsinchu City' : '新竹市',
        'Yunlin County' : '雲林縣',
        'Chiayi County' : '嘉義縣',
        'Pingtung County' : '屏東縣',
        'Hualien County' : '花蓮縣',
        'Taitung County' : '臺東縣',
        'Kinmen County' : '金門縣',
        'Penghu County' : '澎湖縣',
        'Lienchiang County' : '連江縣',
    }
    
}

MONTH_ORDER = {
                '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
                '7': 7, '8': 8, '9': 9, '10': 10, '11': 11, '12': 12
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

    def __init__(self, core, queryset, last_query_item):
        self.solr_tuples = [
            ('q.op', 'AND'),
            ('wt', 'json'),
        ]
        self.core = core
        self.queryset = queryset
        # self.facet_values = facet_values
        self.query_list = ''
        self.solr_error = ''
        self.solr_response = {}
        self.solr_url = ''
        self.solr_q = 'basisOfRecord:*' # Only fetch occurrence data, using basisOfRecord to estimate
        # Limit the respoense fields
        self.filter_field = 'taibif_vernacularName,taibif_country,taibif_locality,taibif_basisOfRecord,basisOfRecord,taibif_datasetKey,taibif_formattedName,taibif_dataset_name_zh,taibif_kingdom,taibif_phylum,taibif_class,taibif_order,taibif_family,taibif_genus,taibif_occ_id,taibif_eventDate'
        self.facet_field = 'facet=true&facet.field=taibif_year&facet.field=taibif_month&facet.field=taibif_dataset_name_zh&facet.field=publisher&facet.field=taibif_country&facet.field=taibif_license&facet.field=taibif_county&facet.field=CoordinateInvalid&facet.field=TaxonMatchNone&facet.field=RecordedDateInvalid&facet.field=wildlife_refuges&facet.field=forest_reserves&facet.field=selfProduced'
        self.last_query_item = last_query_item

    def generate_solr_url(self, queryset, last_query_item=None):
        map_query = ''
        if queryset is not None:
            print(f'QUERY SET:{queryset}')
            for key, values in queryset.lists():
                print(f'key:{key}, value:{values}')
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
                elif key == 'path':
                    self.solr_tuples.append(('fq', 'path:*{}*'.format(values[0])))
                elif key == 'issues':
                    self.solr_tuples.append(('fq', '{}:"{}"'.format(values[0], 'true')))
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
                                if key == 'selfProduced': # 布林值搜尋 value 不需要轉成 string
                                    self.solr_tuples.append(('fq', '{}:{}'.format(field, values[0])))
                                else:
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
                elif key == 'taibif_taxonGroup':
                    if len(values) > 1:
                        query = ' OR '.join(['{}:"{}"'.format('taibif_taxonGroup', value) for value in values])
                        self.solr_tuples.append(('fq', query))
                    else:
                        self.solr_tuples.append(('fq', '{}:{}'.format('taibif_taxonGroup', values[0])))

        self.solr_tuples.append(('q', self.solr_q))
        # if not 'rows' in req_lists:
        #     self.solr_tuples.append(('rows', self.rows)) #TODO remove redundant key['rows']
 
        # if len(self.facet_values):
        #     self.solr_tuples.append(('facet', 'true'))
        #     s = ''
        #     flist = []
        #     #print (str(JSON_FACET_MAP[self.core]).replace("'", '',).replace(' ', ''))
        #     for i in self.facet_values:
        #         if i in JSON_FACET_MAP[self.core]:
        #             flist.append('{}:{}'.format(i, str(JSON_FACET_MAP[self.core][i]).replace("'", '',).replace(' ', '')))
        #             #flist.append('{}:{}'.format(i, JSON_FACET_MAP[self.core][i]))
        #     s = ','.join(flist)
        #     self.solr_tuples.append(('json.facet', '{'f'{s}''}'))
        query_string = urllib.parse.urlencode(self.solr_tuples)
        self.solr_url = f'{SOLR_PREFIX}{self.core}/select?fl={self.filter_field}&{self.facet_field}&{query_string}'
        if last_query_item == 'month':
            self.solr_url = self.solr_url.replace('fq=taibif_month', '')
        print(f'SOLR URL: {self.solr_url}')
        return self.solr_url

    def request(self):
        if self.last_query_item:
            self.generate_solr_url(self.queryset, self.last_query_item)
        else:
            self.generate_solr_url(self.queryset)
        try:
            resp = urllib.request.urlopen(self.solr_url)
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
        # facets = self.solr_response.get('facet.field', [])

        return {
            'offset': resp['start'],
            'limit': self.rows,
            'count': resp['numFound'],
            'results': resp['docs'],
            # 'facets': facets,
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
        '''
            for frontend menus struct
            should call get_response() before call get_menus()
        '''
        menus = []
        resp = self.solr_response
        if not resp['facet_counts']['facet_fields']:
            return None

        if data := resp['facet_counts']['facet_fields']['taibif_country']:
            result = []
            for i in range(0, len(data), 2):
                result.append({
                    'key': data[i],
                    'label': data[i],
                    'count': data[i + 1]
                })
            
            menus.append({
                'key': 'country',
                'label': '國家/區域 Country or Area',
                'rows': result,  
            })

        if data := resp['facet_counts']['facet_fields']['taibif_county']:
            result = []
            for i in range(0, len(data), 2):
                result.append({
                    'key': data[i],
                    'label': CODE_MAPPING['county'][data[i]],
                    'count': data[i + 1]
                })
            
            menus.append({
                'key': 'county',
                'label': '台灣縣市 Taiwan City or County',
                'rows': result,  
            })

        if data := resp['facet_counts']['facet_fields']['forest_reserves']:
            result = []
            for i in range(0, len(data), 2):
                result.append({
                    'key': data[i],
                    'label': data[i],
                    'count': data[i + 1]
                })
            
            menus.append({
                'key': 'forest_reserves',
                'label': '自然生態保護區 Forest Reserves',
                'rows': result,  
            })

        if data := resp['facet_counts']['facet_fields']['wildlife_refuges']:
            result = []
            for i in range(0, len(data), 2):
                result.append({
                    'key': data[i],
                    'label': data[i],
                    'count': data[i + 1]
                })
            
            menus.append({
                'key': 'wildlife_refuges',
                'label': '野生動物保護區 Wildlife Refuges',
                'rows': result,  
            })

        if data := resp['facet_counts']['facet_fields']['taibif_year']:
            result = []
            for i in range(0, len(data), 2):
                result.append({
                    'key': data[i],
                    'label': data[i],
                    'count': data[i + 1]
                })
            
            menus.append({
                'key': 'year',
                'label': '年份 Year',
                'rows': result,  
            })
            
        if data := resp['facet_counts']['facet_fields']['taibif_month']:
            result = []
            i = 0
            while i < len(data):
                print(data[i])
                if data[i] in ['-1', '0']:
                    del data[i:i+2]  
                else:
                    i += 2 
            print(f'MONTH DATA: {data}')

            for i in range(0, len(data), 2):
                result.append({
                    'key': MONTH_ORDER[data[i]],
                    'label': data[i],
                    'count': data[i + 1]
                })
            
            result.sort(key=lambda x: x['key'])
            menus.append({
                'key': 'month',
                'label': '月份 Month',
                'rows': result,  
            })

        if data := resp['facet_counts']['facet_fields']['taibif_dataset_name_zh']:
            result = []
            if len(data) > 10:
                display_number = 10
            else:
                display_number = len(data)
            for i in range(0, display_number, 2): # 最多呈現前 5 多的資料集
                result.append({
                    'key': data[i],
                    'label': data[i],
                    'count': data[i + 1]
                })
            
            menus.append({
                'key': 'dataset_name',
                'label': '資料集 Dataset',
                'rows': result,  
            })
        
        if data := resp['facet_counts']['facet_fields']['publisher']:
            result = []
            if len(data) > 10:
                display_number = 10
            else:
                display_number = len(data)
            for i in range(0, display_number, 2): # 只呈現前 5 多的發布單位
                result.append({
                    'key': data[i],
                    'label': data[i],
                    'count': data[i + 1]
                })
            
            menus.append({
                'key': 'publisher',
                'label': '發布單位 Publisher',
                'rows': result,  
            })

        if data := resp['facet_counts']['facet_fields']['taibif_license']:
            result = []
            for i in range(0, len(data), 2):
                result.append({
                    'key': data[i],
                    'label': data[i],
                    'count': data[i + 1]
                })
            
            menus.append({
                'key': 'license',
                'label': '授權類型 License',
                'rows': result,  
            })

        if data := resp['facet_counts']['facet_fields']['selfProduced']:
            result = []
            for i in range(0, len(data), 2):
                result.append({
                    'key': data[i],
                    'label': data[i],
                    'count': data[i + 1]
                })
            
            menus.append({
                'key': 'selfProduced',
                'label': '資料來源 Source',
                'rows': result,  
            })
        
        return menus

        
        # geo = 0
        # taxon = 0
        # date_i = 0 
        # if data := resp['facets'].get('CoordinateInvalid', ''):
        #     geo = 0
        #     for i in data['buckets']:
        #         if str(i['val']) == 'True':
        #             geo = i['count']
        # if data := resp['facets'].get('TaxonMatchNone', ''):
        #     taxon = 0
        #     for i in data['buckets']:
        #         if str(i['val']) == 'True':
        #             taxon = i['count']
        # if data := resp['facets'].get('RecordedDateInvalid', ''):
        #     date_i = 0
        #     for i in data['buckets']:
        #         if str(i['val']) == 'True':
        #             date_i = i['count']            
                    
        #     rows = [{'key':'TaxonMatchNone', 'label': 'Taxon Match None', 'count': int(taxon)},
        #             {'key':'CoordinateInvalid', 'label': 'Coordinate Invalid', 'count': int(geo)},
        #             {'key':'RecordedDateInvalid', 'label': 'Recorded Date Invalid', 'count': int(date_i)},
        #             ]
        #     menus.append({
        #         'key':'issues',
        #         'label': '問題 Issues',
        #         'rows': rows,
        #     })
            
        # if key == '':
        #     return menus
        # else:
        #     for menu in menus:
        #         if menu['key'] == key:
        #             return menu