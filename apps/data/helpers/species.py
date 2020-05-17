import json
import re
import random

import requests
from bs4 import BeautifulSoup


def _get_taieol_desc(taxon_id, page=''):
    rows = []
    url = 'https://taieol.tw/pages/{}'.format(taxon_id)
    
    r = requests.get(url)
    if r:
        soup = BeautifulSoup(r.text, 'lxml')

        table = soup.findAll('h2', attrs={"class": "taxa-page-chapter-title"})
        table1 = soup.findAll('div', attrs={"class": "taxon-desc-content"})

        TableCount = []
        Table1Count = []
        for x in table1:
            check = x.find('p')

            AllTag1 = x.find_all('p')
            Table1Count.append(len(AllTag1))

            if check != None:
                newlist = soup.select('.taxa-page-chapter-title')
                newlist1 = soup.select('.taxon-desc-content p')


            else:
                if sum(Table1Count) == 0:
                    newlist = soup.select('.taxa-page-chapter-title')
                    newlist1 = soup.select('.taxon-desc-content')
                else:
                    newlist = soup.select('.taxa-page-chapter-title')[:sum(Table1Count)]
                    newlist1 = soup.select('.taxon-desc-content p')
                    print(len(newlist))


        for i in range(len(newlist)):
            for x,y in zip(newlist[i], newlist1[i]):
                foto = {'title':x, 'src': y}


                rows.append(foto)

 
       
        if page == '':
            pager = soup.select('.pager-item a')
            if len(pager) > 0:
                for p in pager:
                    rows += _get_taieol_desc(taxon_id, int(p.text)-1)

    return rows



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
    desc_list = _get_taieol_desc(taieol_taxon_id)


    if media_list:
        if len(media_list) > 8:
            media_list = random.sample(media_list, 8)

    data = {
        #'rows': list(rows),
        #'count': len(rows)
        'taieol_taxon_id': taieol_taxon_id,
        'taieol_media': media_list,
        'taieol_desc': desc_list
    }
    return data
