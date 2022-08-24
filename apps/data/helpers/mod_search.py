from abc import ABCMeta, abstractmethod
from pydoc import describe
import time
import re

from django.db.models import Count, Q
from django.db import connections

from apps.data.models import (
    DATA_MAPPING,
    #SimpleData,
    #RawDataOccurrence,
    Taxon,
    Dataset,
    DatasetOrganization,
    Dataset_description,
)


class SuperSearch(object):

    #__metaclass__ = ABCMeta
    DEFAULT_LIMIT = 20
    LIMIT_THRESHOLD = 10000

    # for _setimate_count
    is_estimate_count = False
    estimate_threshold = 100
    estimate_bias = 1.2

    def __init__(self, filters):
        '''
        firters: [('q', ['begonia']), ('year', ['1990', '1983']), ('menu', ['1'])]
        '''
        self.filters = filters

        # default values
        self.offset = 0
        self.limit = self.DEFAULT_LIMIT
        self.is_debug = False
        self.force_accurate_count = False

        self.timed = [time.time()]
        self.query = self.model.objects.filter()
        # parsing filters
        for i in filters:
            if i[0] == 'limit':
                self.limit = min(self.LIMIT_THRESHOLD, int(i[1][0]))
            if i[0] == 'offset':
                self.offset = int(i[1][0])
            if i[0] == 'debug':
                self.debug = True
            if i[0] == 'force_accurate_count':
                self.force_accurate_count = True

        self.timed = [time.time()]

    def _estimate_count(self):
        # inspired: https://blog.ionelmc.ro/2020/02/02/speeding-up-django-pagination/-
        query = self.query

        qs = query.model._base_manager.all()

        compiler = query.query.get_compiler('default')
        #print (qs, compiler)
        where, params = compiler.compile(query.query.where)
        qs = qs.extra(where=[where] if where else None, params=params)

        cursor = connections[query.db].cursor()
        que = qs.query.clone()
        que.add_annotation(Count('*'), alias='__count', is_summary=True)
        que.clear_ordering(True)
        que.select_for_update = False
        que.select_related = False
        que.select = []
        que.default_cols = False
        sql, params = que.sql_with_params()
        #logger.info('Running EXPLAIN %s', sql)
        #print (sql)
        cursor.execute("EXPLAIN %s" % sql, params)
        lines = cursor.fetchall()
        #logger.info('Got EXPLAIN result:\n> %s',
        #            '\n>   '.join(line for line, in lines))
        marker = ' on %s ' % query.model._meta.db_table
        for line in lines:
            for part in line:
                if marker in part:
                    m = re.search(r'rows=([0-9]+)',part)
                    if m:
                        count = int(m[1]) * self.estimate_bias
                        if count < self.estimate_threshold:
                            # Unreliable, will make views with lots of filtering
                            # output confusing results.
                            # Just do normal count, shouldn't be that slow.
                            # (well, not much slower than the actual query)
                            return query.count()
                        else:
                            return count
        return query.count()

    def _estimate_count_all(self):
        query = self.query
        cursor = connections[query.db].cursor()
        sql = "SELECT reltuples FROM pg_class WHERE relname = '%s';" % query.model._meta.db_table
        cursor.execute(sql)
        return int(cursor.fetchone()[0])

    #@abstractmethod
    def result_map(self, x):
        raise NotImplementedError("Must override result_map")


    def get_results(self):
        query = self.query
        offset = max(0, self.offset)
        limit = min(self.LIMIT_THRESHOLD, self.limit)

        #print("get_results---------", query,offset,limit)
        if limit > 0:
            results = [self.result_map(x) for x in query.all()[offset:offset+limit]]
        else:
            results = [self.result_map(x) for x in query.all()]

        self.timed.append(time.time())

        #count = 0
        # TODO need refine
        if len(self.filters) == 0:
            count = self._estimate_count_all()
        elif self.is_estimate_count and not self.force_accurate_count:
            count = self._estimate_count()
        else:
            count = query.count()

        ret = {
            'elapsed': self.timed[1] - self.timed[0],
            'count': int(count),
            'count_estimate1':self._estimate_count_all(),
            'count_estimate2': self._estimate_count(),
            'limit': limit,
            'offset': offset,
            'has_more': True if count > 0 and offset + limit <= count else False,
            'results': results,
        }
        if self.is_debug:
            ret['queryquery'] = str(query.query)
        return ret


class OccurrenceSearch(SuperSearch):

    is_estimate_count = True

    def __init__(self, filters, using='', model=None):
        if model:
            self.model = model
        else:
            self.model = SimpleData
        super().__init__(filters)
        self.using = using

        self.query = self.model.public_objects.filter()

        # filter query
        query = self.query
        for key, values in self.filters:
            if key == 'q':
                v = values[0] # only get one
                if not v:
                    continue
                # find has species_id first
                species_list = Taxon.find_name(v, 'species', self.using)
                species_ids = [x.id for x in species_list]
                if species_ids:
                    #query = query.filter(Q(taxon_species_id__in=species_ids) |
                    #                     Q(taxon_genus_id__in=species_ids))
                    query = query.filter(taxon_species_id__in=species_ids)
                else:
                    if self.using == '':
                        query = query.filter(Q(vernacular_name__icontains=v) | Q(scientific_name__icontains=v))
                    elif self.using == 'latin':
                        query = query.filter(scientific_name__icontains=v)
                    elif self.using == 'zh':
                        query = query.filter(vernacular_name__icontains=v)
            #if menu_key == 'core':
            #    d = DATA_MAPPING['core'][item_keys]
            #    query = query.filter(dwc_core_type__exact=d)
            if key == 'year':
                query = query.filter(year__in=values)
            if key == 'month':
                query = query.filter(month__in=values)
            # TODO: change simpledata.country to country_code
            if key == 'countrycode':
                query = query.filter(country__exact=values)
            if key == 'dataset':
                query = query.filter(taibif_dataset_name__in=values)
            if key == 'publisher':
                datasets = Dataset.objects.filter(organization__in=values)
                dataset_names = [x.name for x in datasets]
                query = query.filter(taibif_dataset_name__in=dataset_names)

            if key == 'taxon_key':
                # not explict like: taxon_phylum_id=xxx, taxon_specied_id=yyy...

                taxa = Taxon.objects.filter(id__in=values).all()
                or_cond = Q()
                for t in taxa:
                    if t.rank == 'kingdom':
                        or_cond.add(Q(taxon_kingdom_id=t.id), Q.OR)
                    elif t.rank == 'phylum':
                        or_cond.add(Q(taxon_phylum_id=t.id), Q.OR)
                    elif t.rank == 'class':
                        or_cond.add(Q(taxon_class_id=t.id), Q.OR)
                    if t.rank == 'order':
                        or_cond.add(Q(taxon_order_id=t.id), Q.OR)
                    elif t.rank == 'family':
                        or_cond.add(Q(taxon_family_id=t.id), Q.OR)
                    if t.rank == 'genus':
                        or_cond.add(Q(taxon_genus_id=t.id), Q.OR)
                    elif t.rank == 'species':
                        or_cond.add(Q(taxon_species_id=t.id), Q.OR)

                query = query.filter(or_cond)
            else:
                # for species-detail page
                if 'taxon_' in key:
                    query = query.filter(**{key:values[0]})

            self.query = query

    def result_map(self, x):
        date = '{}-{}-{}'.format(x.year if x.year else '',
                                 x.month if x.month else '',
                                 x.day if x.day else '')
        return {
            'taibif_id': x.taibif_id,
            #'basis_of_record': x.basisofrecord'],
            'vernacular_name': x.vernacular_name,
            'country': x.country,
            'scientific_name': x.scientific_name,
            'latitude': float(x.latitude) if x.latitude else None,
            'longitude': float(x.longitude) if x.longitude else None,
            'dataset':  x.taibif_dataset_name,
            'date': date,
        }


class DatasetSearch(SuperSearch):

    def __init__(self, filters):
        self.model = Dataset
        super().__init__(filters)

        # filter query
        query = self.model.public_objects.filter()
        #query = self.query
        for key, values in self.filters:
            if key == 'q':
                v = values[0] # only get one
                if not v:
                    continue
                
                desc = list(Dataset_description.objects.filter(description__icontains=v).values_list('id', flat=True))                  
                query = query.filter(Q(title__icontains=v)| Q(pk__in=(desc)))
                
            if key == 'core':
                v = values[0] # only get one
                if not v:
                    continue
                d = v
                query = query.filter(dwc_core_type__exact=d)
            if key == 'publisher':
                query = query.filter(organization__in=values)
            if key == 'rights':
                rights_reverse_map = {v: k for k,v in DATA_MAPPING['rights'].items()}
                query = query.filter(data_license=rights_reverse_map[values[0]])
            if key == 'country':
                query = query.filter(country__in=values)
            if key == 'is_most_project':
                query = query.filter(is_most_project=True)

            if key == 'order_by':
                query = query.order_by(*values)

        self.query = query

    def result_map(self, x):
        return {
            'title': x.title,
            # 'description': x.description,
            'id': x.id,
            'name': x.name,
            'dwc_type': x.get_dwc_core_type_display(),
            'publisher': x.organization.name if x.organization else '',
            'num_occurrence': x.num_occurrence,
            'num_record': x.num_record,
            'pub_date': x.pub_date.strftime('%Y-%m-%d') if x.pub_date else '',
            'country': x.country_for_human,
            'status_display': x.get_status_display(),
            'status': x.status,
            'guid': x.guid,
        }

class PublisherSearch(SuperSearch):

    def __init__(self, filters):
        self.model = DatasetOrganization
        super().__init__(filters)

        # filter query
        query = self.query
        for key, values in self.filters:
            if key == 'q':
                v = values[0] # only get one
                if not v:
                    continue
                query = query.filter(name__icontains=v)
            if key == 'countrycode':
                query = query.filter(country_code__in=values)

        self.query = query

    def result_map(self, x):
        return {
            'id': x.id,
            'name': x.name,
            'description': x.description,
            'num_dataset': x.datasets.count(),
            'num_occurrence': x.sum_occurrence
        }

class SpeciesSearch(SuperSearch):

    is_estimate_count = True

    def __init__(self, filters):
        self.model = Taxon
        super().__init__(filters)
        print ('this is filters = ',self.filters)
        # filter query
        query = self.query
        for key, values in self.filters:
            if key == 'q':
                v = values[0].strip() # only get one
                if not v:
                    continue
                query = query.filter(Q(name__icontains=v) | Q(name_zh__icontains=v))
            if key == 'rank':
                query = query.filter(rank__in=values)
            if key == 'status':
                v = values[0] # only get one
                if not v:
                    continue
                if v == 'accepted':
                    query = query.filter(is_accepted_name=True)
                elif v == 'synonym':
                    query = query.filter(is_accepted_name=False)
            if key == 'highertaxon':
                or_cond = Q()
                for v in values:
                    if int(v) <=8 :
                        or_cond.add(Q(hierarchy_string__icontains='{}-'.format(v)), Q.OR)
                    else:
                        or_cond.add(Q(hierarchy_string__icontains='-{}-'.format(v)), Q.OR)
                query = query.filter(or_cond)

            self.query = query

    def result_map(self, x):
        return {
            'id': x.id,
            'name': x.name,
            'name_zh': x.name_zh,
            'name_full': '',#TODO react.js
            #'name_list': x.
            # 'count': x.count,
            'rank': x.rank,
            'rank_display': x.get_rank_display(),
            'rank_list': [{'name': t.name, 'rank': t.rank, 'name_zh': t.name_zh, 'id': t.id} for t in x.rank_list],
            'is_accepted_name': x.is_accepted_name,
        }

def filter_occurrence(queryset, filters):
    query = queryset
    for key, values in self.filters:
        if key == 'q':
            v = values[0] # only get one
            if not v:
                continue
            # find has species_id first
            species_list = Taxon.find_name(v, 'species', self.using)
            species_ids = [x.id for x in species_list]
            if species_ids:
                #query = query.filter(Q(taxon_species_id__in=species_ids) |
                #                     Q(taxon_genus_id__in=species_ids))
                query = query.filter(taxon_species_id__in=species_ids)
            else:
                if self.using == '':
                    query = query.filter(Q(vernacular_name__icontains=v) | Q(scientific_name__icontains=v))
                elif self.using == 'latin':
                    query = query.filter(scientific_name__icontains=v)
                elif self.using == 'zh':
                    query = query.filter(vernacular_name__icontains=v)
        #if menu_key == 'core':
        #    d = DATA_MAPPING['core'][item_keys]
        #    query = query.filter(dwc_core_type__exact=d)
        if key == 'year':
            query = query.filter(year__in=values)
        if key == 'month':
            query = query.filter(month__in=values)
        # TODO: change simpledata.country to country_code
        if key == 'countrycode':
            query = query.filter(country__exact=values)
        if key == 'dataset':
            query = query.filter(taibif_dataset_name__in=values)
        if key == 'publisher':
            datasets = Dataset.objects.filter(organization__in=values)
            dataset_names = [x.name for x in datasets]
            query = query.filter(taibif_dataset_name__in=dataset_names)

        if key == 'taxon_key':
            # not explict like: taxon_phylum_id=xxx, taxon_specied_id=yyy...

            taxa = Taxon.objects.filter(id__in=values).all()
            or_cond = Q()
            for t in taxa:
                if t.rank == 'kingdom':
                    or_cond.add(Q(taxon_kingdom_id=t.id), Q.OR)
                elif t.rank == 'phylum':
                    or_cond.add(Q(taxon_phylum_id=t.id), Q.OR)
                elif t.rank == 'class':
                    or_cond.add(Q(taxon_class_id=t.id), Q.OR)
                if t.rank == 'order':
                    or_cond.add(Q(taxon_order_id=t.id), Q.OR)
                elif t.rank == 'family':
                    or_cond.add(Q(taxon_family_id=t.id), Q.OR)
                if t.rank == 'genus':
                    or_cond.add(Q(taxon_genus_id=t.id), Q.OR)
                elif t.rank == 'species':
                    or_cond.add(Q(taxon_species_id=t.id), Q.OR)

            query = query.filter(or_cond)
        else:
            # for species-detail page
            if 'taxon_' in key:
                query = query.filter(**{key:values[0]})
    return query
