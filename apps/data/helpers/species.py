import json
import re
import random

import requests
from bs4 import BeautifulSoup


def _get_taieol_media(taxon_id, page=''):
    rows = []
    url = 'https://taieol.tw/pages/{}/media'.format(taxon_id)
    if page:
        url = 'https://taieol.tw/pages/{}/media?page={}'.format(taxon_id, page)
    r = requests.get(url)
    if r:
        soup = BeautifulSoup(r.text, 'lxml')
        fotos = soup.select('.views-view-grid .views-field-phpcode a')
        for x in fotos:
            rel_concat = ''.join(x['rel'])
            print (rel_concat)
            foto = {'author': '','thumb':'', 'cc': '', 'src': x['href']}
            m = re.search(r'<p>作者:(.+)</p><p>', rel_concat)
            if m:
                foto['author'] = m[1]
            m = re.search(r'<span>授權:(.+)<\/span>', rel_concat)
            if m:
                foto['cc'] = m[1]

            rows.append(foto)

        if page == '':
            pager = soup.select('.pager-item a')
            if len(pager) > 0:
                for p in pager:
                    rows += _get_taieol_media(taxon_id, int(p.text)-1)

    return rows


def get_species_info(taxon):
    scname = taxon.scientific_name

    # get info from taieol
    url = 'https://taieol.tw/tree/autocomplete/1/{}'.format(scname)
    r = requests.get(url)
    resp = json.loads(r.text)

    taieol_taxon_id = ''
    for x in resp:
        m = re.search(r'\[tid\:([0-9]+)\]', x)
        if m:
            taieol_taxon_id = m[1]
        break

    media_list = _get_taieol_media(taieol_taxon_id)
    if media_list:
        media_list = random.sample(media_list, 8)
    data = {
        #'rows': list(rows),
        #'count': len(rows)
        'taieol_taxon_id': taieol_taxon_id,
        'taieol_media': media_list
    }
    return data
