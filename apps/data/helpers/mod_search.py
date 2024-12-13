from abc import ABCMeta, abstractmethod
from datetime import datetime
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
from apps.data.helpers.synonyms_variants_convertion import *


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
        # print(f'qs: {qs}')
        # print(f'complier: {compiler}')
        where, params = compiler.compile(query.query.where)
        qs = qs.extra(where=[where] if where else None, params=params)

        cursor = connections[query.db].cursor()
        que = qs.query.clone()
        que.add_annotation(Count('*'), alias='__count')
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

        if limit > 0:
            results = [self.result_map(x) for x in query.all()[offset:offset+limit]]
        else:
            results = [self.result_map(x) for x in query.all()]

        self.timed.append(time.time())

        #count = 0
        # TODO need refine
        # if len(self.filters) == 0:
        #     count = self._estimate_count_all()
        # elif self.is_estimate_count and not self.force_accurate_count:
        #     count = self._estimate_count()
        # else:
        #     count = query.count()
        count = query.count()

        ret = {
            'elapsed': self.timed[1] - self.timed[0],
            'count': int(count),
            # 'count_estimate1':self._estimate_count_all(),
            # 'count_estimate2': self._estimate_count(),
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

        # 預設查詢
        query = self.model.public_objects.filter().select_related('organization')

        # 加載映射
        mappings = load_mappings()
        variant_map = mappings['variant_map']
        synonyms_map = mappings['synonyms_map']

        # 遍歷過濾條件
        for key, values in self.filters:
            if not values:  # 如果沒有值，跳過
                continue

            if key == 'q':
                v = values[0].strip()  # 僅取第一個值
                if not v:
                    continue
                
                # 同義字轉換
                v_synonyms = replace_synonyms(v, synonyms_map)
                # 生成所有可能的異體字組合
                v_variants = generate_variants(v_synonyms, variant_map)

                query = self._build_variant_query(query, v_variants)

            elif key == 'title' or key == 'datasetName':
                query = query.filter(title__contains=values[0])

            elif key == 'name':
                query = query.filter(name__contains=values[0])

            elif key == 'author':
                query = query.filter(author__contains=values[0])

            elif key == 'organization_id' or key == 'publisherID':
                query = query.filter(organization_uuid=values[0])

            elif key == 'organization_name' or key == 'publisherName':
                query = query.filter(organization_name__contains=values[0])

            elif key == 'dwc_core_type':
                query = query.filter(dwc_core_type__contains=values[0])

            elif key == 'gbif_dataset_id' or key == 'gbifDatasetID':
                query = query.filter(guid=values[0])

            elif key == 'pub_date' or key == 'publicationDate':
                query = self._apply_date_filter(query, values[0], 'pub_date')

            elif key == 'mod_date' or key == 'datasetModifiedDate':
                query = self._apply_date_filter(query, values[0], 'mod_date')

            elif key == 'doi':
                query = query.filter(doi_contains=values[0])

            elif key == 'taibifDatasetID':
                query = query.filter(taibif_dataset_id=values[0])

            elif key == 'core':
                query = self._apply_core_filter(query, values)

            elif key == 'publisher':
                query = query.filter(organization__in=values)

            elif key == 'rights' or key == 'license':
                query = self._apply_license_filter(query, values)

            elif key == 'country':
                query = query.filter(country__in=values)

            elif key == 'is_most_project':
                query = query.filter(is_most_project=True)

            elif key == 'order_by':
                query = query.order_by(*values)

            elif key == 'source':
                query = query.filter(source__in=values)

        self.query = query

    def _build_variant_query(self, query, v_variants):
        """處理異體字查詢邏輯"""
        variant_query = Q()
        for variant in v_variants:
            variant_query |= Q(title__icontains=variant)
        return query.filter(variant_query)

    def _apply_date_filter(self, query, date_range_str, field):
        """處理日期範圍過濾邏輯"""
        date_range = date_range_str.split(',', 1)
        if len(date_range) == 2:
            start_date = datetime.strptime(date_range[0], "%Y-%m-%d")
            end_date = datetime.strptime(date_range[1], "%Y-%m-%d")
            return query.filter(**{f'{field}__range': (start_date, end_date)})
        elif len(date_range) == 1:
            start_date = datetime.strptime(date_range[0], "%Y-%m-%d")
            end_date = datetime.strptime(str(datetime.today().date()), "%Y-%m-%d")
            return query.filter(**{f'{field}__range': (start_date, end_date)})
        return query

    def _apply_core_filter(self, query, values):
        """處理 core 查詢邏輯"""
        v = values[0]  # 只取第一個值
        if not v:
            return query
        return query.filter(dwc_core_type__exact=v)

    def _apply_license_filter(self, query, values):
        """處理 license 查詢邏輯"""
        if str(values[0]) == 'NA':
            return query.filter(data_license__contains='unknown')
        rights_reverse_map = {v: k for k, v in DATA_MAPPING['rights'].items()}
        rights_list = [rights_reverse_map[v] for v in values]
        return query.filter(data_license__in=rights_list)

    def result_map(self, x):
        return {
            'title': x.title,
            # 'description': x.description,
            'id': x.id,
            'name': x.name,
            'dwc_type': x.get_dwc_core_type_display(),
            'publisher': x.organization.name if x.organization else None,
            'num_occurrence': x.num_occurrence,
            'num_record': x.num_record,
            'pub_date': x.pub_date.strftime('%Y-%m-%d') if x.pub_date else None,
            'country': x.country_for_human,
            'status_display': x.get_status_display(),
            'status': x.status,
            'guid': x.guid,
            'taibif_dataset_id': str(x.taibif_dataset_id),
        }

class PublisherSearch(SuperSearch):

    def __init__(self, filters):
        self.model = DatasetOrganization
        super().__init__(filters)

        # filter query
        query = self.query

        mappings = load_mappings()
        variant_map = mappings['variant_map']
        synonyms_map = mappings['synonyms_map']

        for key, values in self.filters:
            if key == 'q' or key == 'publisherName':
                v = values[0] # only get one
                if not v:
                    continue
                # 同義字轉換
                v_synonyms = replace_synonyms(v, synonyms_map)
                # 生成所有可能的異體字組合
                v_variants = generate_variants(v_synonyms, variant_map)

                query = self._build_variant_query(query, v_variants)
            if key == 'countrycode' or key == 'countryCode':
                query = query.filter(country_code__in=values)
            if key == 'publisherGbifUuid' or key == 'publisherID':
                query = query.filter(organization_gbif_uuid__in=values)

        self.query = query

    def _build_variant_query(self, query, v_variants):
        """處理異體字查詢邏輯"""
        variant_query = Q()
        for variant in v_variants:
            variant_query |= Q(name__icontains=variant)
        return query.filter(variant_query)
    
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

        # 預設查詢
        query = self.model.objects.filter(taicol_taxon_id__isnull=False)

        mappings = load_mappings()
        variant_map = mappings['variant_map']
        synonyms_map = mappings['synonyms_map']

        # 遍歷過濾器
        for key, values in self.filters:
            if not values:  # 如果沒有值，跳過
                continue

            if key == 'q':
                v = values[0].strip()  # 僅取第一個值
                if not v:
                    continue
                
                # 同義字轉換
                v_synonyms = replace_synonyms(v, synonyms_map)
                # 生成所有可能的異體字組合
                v_variants = generate_variants(v_synonyms, variant_map)

                query = self._build_variant_query(query, v_variants)

            elif key == 'rank':
                query = query.filter(rank__in=values)

            elif key == 'status':
                v = values[0]  # 只取第一個值
                if v == 'accepted':
                    query = query.filter(is_accepted_name=True)
                elif v == 'synonym':
                    query = query.filter(is_accepted_name=False)

            elif key == 'highertaxon':
                query = self._build_higher_taxon_query(query, values)

        self.query = query.order_by('taicol_taxon_id')

    def _build_variant_query(self, query, v_variants):
        """處理異體字查詢邏輯"""
        variant_query = Q()
        for variant in v_variants:
            variant_query |= Q(name__icontains=variant) | Q(name_zh__icontains=variant)
        return query.filter(variant_query)

    def _build_higher_taxon_query(self, query, values):
        """處理 higher taxon 查詢邏輯"""
        higher_taxon_query = Q()
        for value in values:
            higher_taxon_query |= Q(path__icontains=value)
        return query.filter(higher_taxon_query)
        

    def result_map(self, x):
        return {
            'id': x.id,
            'name': x.name,
            'name_zh': x.name_zh,
            'name_full': '',#TODO react.js
            'taicol_taxon_id': x.taicol_taxon_id,
            'formatted_name': x.formatted_name,
            'rank': x.rank,
            'rank_display': x.get_rank_display(),
            'rank_list': [{'name': t.name, 'rank': t.rank, 'name_zh': t.name_zh, 'taicol_taxon_id': t.taicol_taxon_id,'formatted_name':t.formatted_name} for t in x.rank_list],
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