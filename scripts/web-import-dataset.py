
import os
import json
#import csv

from django.utils.dateparse import parse_date

BUCKET_PATH = '/taibif-volumes/bucket/'
#DATASET_CSV = '0-dataset-list_20200106-164549.csv'
DATASET_CSV = '0-dataset-list_20200316-175142.csv'

from apps.data.models import Dataset

class MgCsv(object):
    '''
    last import date: 2020-01-03

    notice:
    - csv must have header
    - cut first 2 columns
    '''
    columns = []
    rows = []
    length = 0
    def __init__(self, csv_path):
        import csv # import outside this will get 'not defined' NameError?
        header = []
        data = []
        counter = 0
        with open(csv_path) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if len(header) == 0:
                    # create header
                    header = row[2:] # ignore first 2 column
                else:
                    # map data with header
                    x = {}
                    counter += 1
                    for h, v in zip(header, row[2:]): # ignore firest 2 column (empty header)
                        x[h] = v
                    data.append(x)
            self.columns = header
            self.rows = data
            self.length = counter

d = MgCsv(os.path.join(BUCKET_PATH, DATASET_CSV))
#print (d.length)
#print (d.rows)
for i in d.rows:
    #print (i['title'], i['name'])
    d = json.loads(i['stats'])

    exist = Dataset.objects.get(name=i['name'])
    if not exist:
        # create
        ds = Dataset(
            title = i['title'],
            name = i['name'],
            description = i['descr'],
            organization_verbatim = i['org'],
            dwc_core_type = i['core'],
            pub_date = parse_date(i['pub_date']),
            mod_date = parse_date(i['mod_date']),
            status = i['status'],
            cite = i['cite'],
            guid = i['guid'],
            version = i['version'],
            country = i['country'],
            gbif_cite = i['cite_gbif'],
            gbif_doi = i['doi_gbif'],
            gbif_mod_date = parse_date(i['mod_date_gbif']),
            author = i['author'],
            num_record = int(float(i['stats_num_record'])),
            num_occurrence = int(float(i['stats_num_occurrence'])),
            data_license = d['license'],
            quality = d['quality']
        )
        ds.save()
        print ('create', ds)
    else:
        # update
        exist.title = i['title']
        exist.name = i['name']
        exist.description = i['descr']
        exist.organization_verbatim = i['org']
        exist.dwc_core_type = i['core']
        exist.pub_date = parse_date(i['pub_date'])
        exist.mod_date = parse_date(i['mod_date'])
        exist.status = i['status']
        exist.cite = i['cite']
        exist.guid = i['guid']
        exist.version = i['version']
        exist.country = i['country']
        exist.gbif_cite = i['cite_gbif']
        exist.gbif_doi = i['doi_gbif']
        exist.gbif_mod_date = parse_date(i['mod_date_gbif'])
        exist.author = i['author']
        exist.num_record = int(float(i['stats_num_record']))
        exist.num_occurrence = int(float(i['stats_num_occurrence']))
        exist.data_license = d['license']
        exist.quality = d['quality']
        exist.save()
        #print (exist)
        print ('update', exist)
