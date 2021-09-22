import urllib
import logging
import json

import requests

SOLR_PREFIX = 'http://solr:8983/solr/'

JSON_FACET_MAP = {
    'taibif_occurrence': '{dataset:{type:terms,field:taibif_dataset_name},month:{type:terms,field:month},year:{type:terms,field:year}}',
}


class SolrQuery(object):
    '''
    solr = SolrQuery('taibif_occurrence')
    resp = solr.request(request.GET.lists())
    response = solr_ret['data']
    '''
    rows = 20
    #query = {}
    facet_fields = {
        'year': {},
        'month': {},
        'taibif_dataset_name': {},
    }
    '''
    test
    solr_tuples = [
        ('q', 'brueggemanni'),
        #('rows', '*.*'),
        ('q', '20'),
        ('facet', 'true'),
        ('json.facet', '{dataset:{type:terms,field:taibif_dataset_name},month:{type:terms,field:month}}'),
        ('wt', 'json'),
        ]
    '''

    def __init__(self, core):
        self.solr_tuples = [
            ('q.op', 'OR'),
            ('rows', self.rows),
            ('wt', 'json'),
        ]
        self.core = core
        self.has_facet = True
        self.solr_error = ''
        self.solr_response = {}

    def request(self, req_lists):
        for key, values in req_lists:
            if key == 'q':
                self.solr_tuples.append(('q', values[0]))
            elif key == 'offset':
                self.solr_tuples.append(('start', values[0]))
            elif key == 'limit':
                self.solr_tuples.append(('offset', values[0]))
            elif ',' in values[0]:
                vsplit = values.split(',')
                self.solr_tuples.append((key, f'{vsplit[0]} TO {vsplit[1]}'))
            elif key in self.facet_fields:
                if len(values) == 1:
                    self.solr_tuples.append(('fq', '{}:{}'.format(key, values[0])))
                else:
                    self.solr_tuples.append(('fq', '{}:({})'.format(key, ' OR '.join(values))))

        if self.has_facet:
            self.solr_tuples.append(('facet', 'true'))
            self.solr_tuples.append(('json.facet', JSON_FACET_MAP[self.core]))

        query_string = urllib.parse.urlencode(self.solr_tuples)
        #print (query_string)
        url = f'{SOLR_PREFIX}{self.core}/select?{query_string}'
        #print(url)
        try:
            resp =urllib.request.urlopen(url)
            resp_dict = resp.read().decode()
            self.solr_response = json.loads(resp_dict)
        except urllib.request.HTTPError as e:
            self.solr_error = str(e)
        #print(json.loads(connection))
        return {
            'solr_response': self.solr_response,
            'solr_error': self.solr_error
        }

    def get_response(self):
        if not self.solr_response:
            return

        resp = self.solr_response['response']
        facets = self.solr_response['facets']

        is_last = False
        if resp['start'] + self.rows >= resp['numFound']:
            is_last = True

        return {
            'offset': resp['start'],
            'limit': self.rows,
            'count': resp['numFound'],
            'results': resp['docs'],
            'endOfRecords': is_last,
            'facets': facets,
        }
