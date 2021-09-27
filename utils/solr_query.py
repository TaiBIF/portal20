import urllib
import logging
import json

import requests

SOLR_PREFIX = 'http://solr:8983/solr/'

JSON_FACET_MAP = {
    'taibif_occurrence': {
        'dataset': {
            'type': 'terms',
            'field': 'taibif_dataset_name_zh'
        },
        'month': {
            'type': 'terms',
            'field':'month',
            'start':'1',
            'end':'13',
            'gap':'1'
        },
        'year': {
            'type':'terms',
            'field':'year'
        },
        'country': {
            'type':'terms',
            'field':'country'
        },
        'publisher': {
            'type':'terms',
            'field':'publisher'
        },
    }
}


class SolrQuery(object):
    '''
    solr = SolrQuery('taibif_occurrence')
    resp = solr.request(request.GET.lists())
    response = solr_ret['data']
    '''
    rows = 20

    def __init__(self, core):
        self.solr_tuples = [
            ('q.op', 'OR'),
            ('rows', self.rows),
            ('wt', 'json'),
        ]
        self.core = core
        self.has_facet = False
        self.facet_values = []
        self.solr_error = ''
        self.solr_response = {}

    def request(self, req_lists):
        solr_q = '*:*'
        for key, values in req_lists:
            #print(key, values)
            if key == 'q':
                solr_q = values[0]
            elif key == 'offset':
                self.solr_tuples.append(('start', values[0]))
            elif key == 'limit':
                self.solr_tuples.append(('offset', values[0]))
            elif key in JSON_FACET_MAP[self.core]:
                if len(values) == 1:
                    if ',' in values[0]:
                        vlist = values[0].split(',')
                        self.solr_tuples.append(('fq', f'{key}:[{vlist[0]} TO {vlist[1]}]'))
                    else:
                        if key in JSON_FACET_MAP[self.core]:
                            self.solr_tuples.append(('fq', '{}:{}'.format(JSON_FACET_MAP[self.core][key]['field'], values[0])))
                else:
                    self.solr_tuples.append(('fq', '{}:({})'.format(key, ' OR '.join(values))))
            elif key == 'facet':
                self.has_facet = True
                self.facet_values = values

        self.solr_tuples.append(('q', solr_q))

        if self.has_facet:
            self.solr_tuples.append(('facet', 'true'))
            s = ''
            flist = []
            print (str(JSON_FACET_MAP[self.core]).replace("'", '',).replace(' ', ''))
            for i in self.facet_values:
                if i in JSON_FACET_MAP[self.core]:
                    flist.append('{}:{}'.format(i, str(JSON_FACET_MAP[self.core][i]).replace("'", '',).replace(' ', '')))
                    #flist.append('{}:{}'.format(i, JSON_FACET_MAP[self.core][i]))
            s = ','.join(flist)
            self.solr_tuples.append(('json.facet', '{'f'{s}''}'))

        query_string = urllib.parse.urlencode(self.solr_tuples)
        #print (query_string)
        #print(self.solr_tuples)
        url = f'{SOLR_PREFIX}{self.core}/select?{query_string}'
        #print(url)
        try:
            resp =urllib.request.urlopen(url)
            resp_dict = resp.read().decode()
            self.solr_response = json.loads(resp_dict)
        except urllib.request.HTTPError as e:
            self.solr_error = str(e)

        return {
            'solr_response': self.solr_response,
            'solr_error': self.solr_error
        }

    def get_response(self):
        if not self.solr_response:
            return

        resp = self.solr_response['response']
        facets = self.solr_response.get('facets', [])

        is_last = False
        if resp['start'] + self.rows >= resp['numFound']:
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

        url = f'{SOLR_PREFIX}{self.core}/select?q.op=OR&q={query_string}'
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