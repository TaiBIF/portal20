from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.urls import reverse

DATA_MAPPING = {
    'country': {
        'TW': '台灣',
        'PH': '菲律賓',
        'NP': '尼泊爾',
        'ZM': '尚比亞',
        'BI': '蒲隆地',
        'CN': '中國',
        'IN':'印度',
        'VN':'越南',
        'unknown':'其他',
    },
    'rights': {
        'Creative Commons Attribution Non Commercial (CC-BY-NC) 4.0 License': 'CC-BY-NC 4.0',
        'Creative Commons Attribution (CC-BY) 4.0 License': 'CC-BY 4.0',
        'Public Domain (CC0 1.0)': 'CC0 1.0',
        None:'未明確授權',
        'unknown':'未明確授權',
    },
    'core': {
        'occurrence': 'Occurrence',
        'taxon': 'checklist',
        'event': 'Sampling event',
        'meta': 'Metadata-only'
    },
    'publisher_dwc':{
        'OCCURRENCE':'出現紀錄',
        'CHECKLIST':'物種名錄',
        'SAMPLINGEVENT':'調查活動',
        'Metadata-only':'詮釋資料',
    }
}

# DEPRICATED?
class Organization(models.Model):

    NUM_PER_PAGE = 20
    STATUS_CHOICE = (
        ('Public', 'Public'),
        ('Private', 'Private'),
    )

    title = models.CharField('title', max_length=300)
    name = models.CharField('name', max_length=128) # ipt shortname
    description = models.TextField('Description')
    author = models.CharField('author', max_length=128)

class PublicDatasetManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='PUBLIC')

class Dataset(models.Model):

    NUM_PER_PAGE = 20

    STATUS_CHOICE = (
        ('PUBLIC', '公開'),
        ('PRIVATE', '非公開'),
    )

    DWC_CORE_TYPE_CHOICE = (
        ('OCCURRENCE', '出現紀錄'),
        ('CHECKLIST', '物種名錄'),
        ('SAMPLINGEVENT', '調查活動'),
        # Meta
    )

    title = models.CharField('title', max_length=300)
    name = models.CharField('name', max_length=128) # ipt shortname
    author = models.CharField('author', max_length=128)
    pub_date = models.DateTimeField('Publish Date', null=True)
    mod_date = models.DateTimeField('Modified Date', null=True)
    guid = models.CharField('GUID', max_length=40,null=True)
    status = models.CharField('status', max_length=10, choices=STATUS_CHOICE)
    dwc_core_type = models.CharField('Dw-C Core Type', max_length=128, choices=DWC_CORE_TYPE_CHOICE, null=True)
    data_license = models.CharField('Data License', max_length=128,null=True)
    version = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    gbif_doi = models.TextField(blank=True, null=True)
    organization_name = models.TextField(blank=True, null=True)
    organization = models.ForeignKey('DatasetOrganization', null=True, blank=True, on_delete=models.SET_NULL, related_name='datasets')
    num_occurrence = models.PositiveIntegerField(default=0)
    is_most_project = models.BooleanField('是否為國科會計畫', default=False)
    quality = models.CharField('資料集品質', max_length=4, default='')
    has_publish_problem = models.BooleanField('是否有發布問題 (IPT 裡黃色的區塊)', default=False, help_text='有可能 IPT 授權沒填?')
    admin_memo = models.TextField('後台管理註記', blank=True, null=True, help_text='不會在前台出現')
    
    pre_released = models.DateTimeField(null=True)
    pre_count = models.BigIntegerField(null=True)
    # pub_released = models.DateTimeField(null=True)
    # pub_count = models.BigIntegerField(null=True)
    num_checklist = models.PositiveIntegerField(default=0)
    num_event = models.PositiveIntegerField(default=0)
    # recordsPublished = models.PositiveIntegerField(default=0)
    metadataModified = models.DateTimeField(null=True)
    mappingsModified = models.DateTimeField(null=True)
    sourcesModified = models.DateTimeField(null=True)
    lastPublished = models.DateTimeField(null=True)
    created = models.DateTimeField(null=True)
    language= models.CharField(max_length=128,null=True)
    organization_uuid = models.CharField(max_length=256,null=True)
    num_record = models.PositiveIntegerField(default=0)
    objects = models.Manager()
    public_objects = PublicDatasetManager()

    def get_absolute_url(self):
        return reverse('dataset-detail', args=[self.name])

    @property
    def country_for_human(self):
        if self.country and self.country in DATA_MAPPING['country']:
            return DATA_MAPPING['country'][self.country]
        return self.country

    @property
    def link(self):
        return 'http://ipt.taibif.tw/resource?r={}'.format(self.name)

    @property
    def eml(self):
        return 'http://ipt.taibif.tw/eml.do?r={}'.format(self.name)

    @property
    def dwca_link(self):
        return 'https://ipt.taibif.tw/archive.do?r={}'.format(self.name)
    
    @property
    def doi_link(self):
        return 'https://doi.org/{}'.format(self.gbif_doi)
    
        

    def __str__(self):
        r = '<Dataset {}>'.format(self.name)
        return r


class Dataset_citation(models.Model):

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)
    identifier = models.TextField(null=True,blank=True)
    citation = models.TextField(null=True,blank=True)
    seq = models.TextField(null=True,blank=True)

class Dataset_Contact(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)
    givenname =  models.CharField(max_length=128,null=True,blank=True)
    surname  =  models.CharField(max_length=128,null=True,blank=True)
    organizationname =  models.CharField(max_length=512,null=True,blank=True)
    positionname =  models.CharField(max_length=1024,null=True,blank=True)
    deliverypoint =  models.CharField(max_length=2048,null=True,blank=True)
    city =  models.CharField(max_length=128,null=True,blank=True)
    administrativearea =  models.CharField(max_length=128,null=True,blank=True)
    postalcode =  models.CharField(max_length=128,null=True,blank=True)
    country =  models.CharField(max_length=256,null=True,blank=True)
    phone =  models.CharField(max_length=128,null=True,blank=True)
    electronicmailaddress =  models.CharField(max_length=512,null=True,blank=True)
    onlineurl =  models.CharField(max_length=256,null=True,blank=True)
    role =  models.CharField(max_length=128,null=True,blank=True)
    role_type = models.CharField(max_length=128,null=True,blank=True)
    # creator =  models.BooleanField(default=False,null=True,blank=True)
    

class Dataset_keyword(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)
    keyword = models.TextField(null=True,blank=True)
    seq = models.TextField(null=True,blank=True)

class Dataset_description(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True, related_query_name="desc",)
    description = models.TextField(null=True,blank=True)
    seq = models.TextField(null=True,blank=True)

class DatasetOrganization(models.Model):
    '''publisher'''

    NUM_PER_PAGE = 20

    name = models.CharField('name', max_length=512)
    description = models.TextField('description', default='',null=True)
    country_code = models.CharField('country_code', max_length=8, default='TW',null=True)
    administrative_contact = models.CharField('administrative_contact', max_length=256, default='',null=True)
    endorsed_by = models.CharField('endorsed_by', max_length=256, default='',null=True)
    installations = models.CharField('installations', max_length=256, default='',null=True)
    technical_contact = models.CharField('technical_contact', max_length=256, default='',null=True)
    country_or_area = models.CharField('country_or_area', max_length=256, default='',null=True)
    occurences_num = models.IntegerField('country_or_area', default=0,null=True)
    dataset_num = models.IntegerField('dataset_num',default=0,null=True)

    @property
    def sum_occurrence(self):
        n = 0
        for d in self.datasets.values('num_occurrence').all():
            n += d['num_occurrence']
        return n

class TaxonTree(models.Model):
    name = models.CharField('name', max_length=64)
    rank_map = models.CharField('rank map', max_length=256)

    def full_taxa_map(self):
        taxa = {}
        for rank in self.rank_map.split('|')[:-2]: # skip genus & species
            taxa[rank] = {}
            tlist = Taxon.objects.filter(rank=rank).all()
            for t in tlist:
                if taxa[rank].get(t.name, '--') != '--' and t.rank not in ['species','genus']:
                    print ('duplicate', t.rank, t.name, t.id)
                taxa[rank][t.name] = t.id
        # append genus+species
        # for gen-sample-data use
        taxa['sci_name'] = {}
        counter = 0
        for t in Taxon.objects.filter(rank='species').all():
            counter += 1
            if counter % 10000 == 0:
                print (counter)
            key = t.scientific_name_infraspecific
            tlist = [t.id]
            if t.parent:
                tlist.append(t.parent_id)
            taxa['sci_name'][key] = tlist
        return taxa

    def __str__(self):
        r = '{}'.format(self.name)
        return r

class Taxon(models.Model):
    RANK_LIST = [
        ('kingdom', '界'),
        ('phylum', '門'),
        ('class', '綱'),
        ('order', '目'),
        ('family', '科'),
        ('genus', '屬'),
        ('species', '種'),
    ]

    rank = models.CharField('rank', max_length=32, choices=RANK_LIST)
    name = models.CharField('name', max_length=128)
    name_zh = models.CharField('name_zh', max_length=2000,null=True)
    hierarchy_string = models.CharField('hierarchy string', max_length=512, default='',null=True)
    
    kingdom_id = models.IntegerField('kingdom_id',default=0,null=True)
    phylum_id = models.IntegerField('phylum_id',default=0,null=True)
    class_id = models.IntegerField('class_id',default=0,null=True)
    order_id = models.IntegerField('order_id',default=0,null=True)
    family_id = models.IntegerField('family_id',default=0,null=True)
    genus_id = models.IntegerField('genus_id',default=0,null=True)
    
    
    specific_epithet = models.CharField('specific epithet', max_length=128, null=True)
    count = models.PositiveIntegerField('count', default=0,null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    tree = models.ForeignKey(TaxonTree, on_delete=models.CASCADE, null=True)
    is_accepted_name = models.BooleanField('is accepted nam', default=True)
    accepted_name_id = models.IntegerField('accepted_name_id',default=0,null=True)

    source_id = models.CharField('name_code', max_length=1000, null=True, blank=True)
    verbose = models.CharField('verbose', max_length=1000, default='',null=True)
    reference = models.CharField('reference',max_length=5000,null=True)
    taieol_desc = models.TextField('taieol_desc', null=True)
    taieol_pic = models.CharField('taieol_pic',max_length=1000,null=True)
    
    def __str__(self):
        r = '{}: {}'.format(self.rank, self.get_name())
        return r

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('species-detail', args=[str(self.id)])

    def get_name(self, cat=''):
        if cat == 'list':
            nlist = [self.name]
            if self.name_zh:
                nlist.append(self.name_zh)
            return nlist
        else:
            if self.name_zh:
                return '{} {}'.format(self.name_zh, self.name)
            else:
                return '{}'.format(self.name)


    def accepted_name(self):
        name = Taxon.objects.get(id=self.accepted_name_id)
        return name
    

    def synonyms(self):
        sys_name = Taxon.objects.filter(accepted_name_id=self.accepted_name_id,is_accepted_name=False).exclude(id=self.id)
        return list(sys_name.all())

    @staticmethod
    def find_name(name, rank='', using=''):
        query = Taxon.objects
        if rank:
            query = Taxon.objects.filter(rank=rank)
        if using == '':
            query = query.filter(Q(name__icontains=name) | Q(name_zh__icontains=name))
        elif using == 'latin':
            query = query.filter(name__icontains=name)
        elif using == 'zh':
            query = query.filter(name_zh__icontains=name)
        return list(query.all())

    @property
    def accepted_species(self):
        if not self.is_accepted_name:
            vlist = self.verbose.split('|')
            t = Taxon.objects.get(source_id=vlist[2])
            if t:
                return t
        return None
    @property
    def scientific_name(self):
            slist = []
            if self.parent:
                slist.append(self.parent.name)
            slist.append(self.name)
            return ' '.join(slist)
       

    @property
    def scientific_name_infraspecific(self):
        # if self.rank == 'species':
            # vlist = self.verbose.split('|')
            # slist = [self.name]
            # if vlist[4] and vlist[4] != '--':
            #     slist.append(vlist[4])
            # if vlist[3] and vlist[3] != '--':
            #     slist.append(vlist[3])
            # if vlist[6] and vlist[6] != '--':
            #     slist.append(vlist[6])
            # if vlist[5] and vlist[5] != '--':
            #     slist.append(vlist[5])
            # return ' '.join(slist)
        return self

    @property
    def scientific_name_full(self):
        # if self.rank == 'species':
        #     slist = [self.scientific_name_infraspecific]
        #     vlist = self.verbose.split('|')
        #     if vlist[7] and vlist[7] != '--':
        #         slist.append(vlist[7])
        #     if vlist[8] and vlist[8] != '--':
        #         slist.append(vlist[8])
        #     return ' '.join(slist)
        # else:
            return self.name

    @property
    def taicol_search_link(self):
        url = 'http://taibnet.sinica.edu.tw/chi/taibnet_species_list.php?T2={}&T2_new_value=true&fr=y'.format(self.name)
        return url

    @property
    def taicol_namecode_link(self):
        url =''
        if self.rank == 'species':
            if self.rank == 'species' and self.source_id:
                url = 'https://taibnet.sinica.edu.tw/chi/taibnet_species_detail.php?name_code={}'.format(self.source_id)
        return url

    @property
    def rank_list(self):
        def get_rank_tree(x, a=[]):
            if x.parent:
                a.append(x.parent)
                return get_rank_tree(x.parent, a)
            return list(reversed(a))
        return get_rank_tree(self)

    @property
    def species_pic(self):
        query = Taxon.objects
        if self.rank != 'species':
            if self.rank == 'kingdom':
                query = query.filter(kingdom_id=self.id,taieol_pic__isnull=False).order_by('taieol_pic').distinct('taieol_pic')
            elif self.rank == 'phylum':
                query = query.filter(phylum_id=self.id,taieol_pic__isnull=False).order_by('taieol_pic').distinct('taieol_pic')
            elif self.rank == 'class':
                query = query.filter(class_id=self.id,taieol_pic__isnull=False).order_by('taieol_pic').distinct('taieol_pic')
            elif self.rank == 'order':
                query = query.filter(order_id=self.id,taieol_pic__isnull=False).order_by('taieol_pic').distinct('taieol_pic')
            elif self.rank == 'family':
                query = query.filter(family_id=self.id,taieol_pic__isnull=False).order_by('taieol_pic').distinct('taieol_pic')
            elif self.rank == 'genus':
                query = query.filter(genus_id=self.id,taieol_pic__isnull=False).order_by('taieol_pic').distinct('taieol_pic')
        
            return list(query.all())
        else:
            query = query.filter(id = self.id)
            return list(query.all())

    @property
    def children(self):
        return Taxon.objects.filter(parent=self, is_accepted_name=True).all()

    @staticmethod
    def get_tree(rank='', status=''):
        rows = []
        for i in Taxon.RANK_LIST:
            q = Taxon.objects.filter(rank=i[0])
            if status and i[0] == 'species': # only count on species
                if status == 'accepted':
                    q = q.filter(is_accepted_name=True)
                elif status == 'synonym':
                    q = q.filter(is_accepted_name=False)
            rows.append({
                'count': q.count(),
                'key': i[0],
                'label': '{} {}'.format(i[1], i[0].capitalize())
            })
        #taxon_list = Taxon.objects.\
        #    filter(tree_id=1,
        #           rank=rank).\
        #    order_by('-count').all()
        return rows

    @property
    def data(self):
        return {
            'name': self.name,
            'name_zh': self.name_zh,
            'name_v': self.get_name(),
            'count': self.count,
            'taxon_id': self.id,
            #'rank': self.rank,
            'parent_id': self.parent.id if self.parent else None
        }

    class Meta:
        ordering = ['id','name']

OCCURRENCE_COLUMN_MAP = {'occurrenceID': 'occurrence_id', 'occurrenceRemarks': 'occurrence_remarks', 'occurrenceStatus': 'occurrence_status', 'institutionID': 'institution_id', 'institutionCode': 'institution_code', 'ownerInstitutionCode': 'owner_institution_code', 'collectionID': 'collection_id', 'collectionCode': 'collection_code', 'catalogNumber': 'catalog_number', 'otherCatalogNumbers': 'other_catalog_numbers', 'recordNumber': 'record_number', 'recordedBy': 'recorded_by', 'fieldNumber': 'field_number', 'fieldNotes': 'field_notes', 'basisOfRecord': 'basis_of_record', 'datasetID': 'dataset_id', 'datasetName': 'dataset_name', 'language': 'language', 'type': 'type_field', 'typeStatus': 'type_status', 'coreid': 'coreid', 'lifeStage': 'life_stage', 'eventTime': 'event_time', 'eventRemarks': 'event_remarks', 'year': 'year', 'month': 'month', 'day': 'day', 'startDayOfYear': 'start_day_of_year', 'endDayOfYear': 'end_day_of_year', 'eventDate': 'event_date', 'eventID': 'event_id', 'verbatimEventDate': 'verbatim_event_date', 'verbatimDepth': 'verbatim_depth', 'kingdom': 'kingdom', 'phylum': 'phylum', 'class': 'class_field', 'order': 'order_field', 'family': 'family', 'genus': 'genus', 'subgenus': 'subgenus', 'vernacularName': 'vernacular_name', 'scientificName': 'scientific_name', 'scientificNameID': 'scientific_name_id', 'taxonRank': 'taxon_rank', 'taxonID': 'taxon_id', 'verbatimTaxonRank': 'verbatim_taxon_rank', 'associatedTaxa': 'associated_taxa', 'specificEpithet': 'specific_epithet', 'scientificNameAuthorship': 'scientific_name_authorship', 'acceptedNameUsage': 'accepted_name_usage', 'acceptedNameUsageID': 'accepted_name_usage_id', 'originalNameUsage': 'original_name_usage', 'nameAccordingTo': 'name_according_to', 'higherClassification': 'higher_classification', 'taxonRemarks': 'taxon_remarks', 'dateIdentified': 'date_identified', 'identificationQualifier': 'identification_qualifier', 'identifiedBy': 'identified_by', 'identificationVerificationStatus': 'identification_verification_status', 'previousIdentifications': 'previous_identifications', 'county': 'county', 'country': 'country', 'countryCode': 'country_code', 'stateProvince': 'state_province', 'locality': 'locality', 'locationID': 'location_id', 'higherGeography': 'higher_geography', 'georeferencedDate': 'georeferenced_date', 'georeferenceSources': 'georeference_sources', 'georeferencedBy': 'georeferenced_by', 'geodeticDatum': 'geodetic_datum', 'georeferenceProtocol': 'georeference_protocol', 'georeferenceRemarks': 'georeference_remarks', 'georeferenceVerificationStatus': 'georeference_verification_status', 'decimalLongitude': 'decimal_longitude', 'decimalLatitude': 'decimal_latitude', 'verbatimLatitude': 'verbatim_latitude', 'verbatimLongitude': 'verbatim_longitude', 'verbatimLocality': 'verbatim_locality', 'verbatimCoordinates': 'verbatim_coordinates', 'coordinateUncertaintyInMeters': 'coordinate_uncertainty_in_meters', 'verbatimCoordinateSystem': 'verbatim_coordinate_system', 'coordinatePrecision': 'coordinate_precision', 'locationAccordingTo': 'location_according_to', 'pointRadiusSpatialFit': 'point_radius_spatial_fit', 'rights': 'rights', 'rightsHolder': 'rights_holder', 'license': 'license_field', 'preparations': 'preparations', 'id': 'id_field', 'modified': 'modified', 'dataGeneralizations': 'data_generalizations', 'organismID': 'organism_id', 'organismQuantityType': 'organism_quantity_type', 'organismQuantity': 'organism_quantity', 'sex': 'sex', 'individualCount': 'individual_count', 'verbatimElevation': 'verbatim_elevation', 'minimumElevationInMeters': 'minimum_elevation_in_meters', 'maximumElevationInMeters': 'maximum_elevation_in_meters', 'minimumDepthInMeters': 'minimum_depth_in_meters', 'maximumDepthInMeters': 'maximum_depth_in_meters', 'waterBody': 'water_body', 'island': 'island', 'habitat': 'habitat', 'reproductiveCondition': 'reproductive_condition', 'continent': 'continent', 'infraspecificEpithet': 'infraspecific_epithet', 'footprintWKT': 'footprint_wkt', 'associatedMedia': 'associated_media', 'associatedSequences': 'associated_sequences', 'associatedReferences': 'associated_references', 'nomenclaturalCode': 'nomenclatural_code', 'footprintSpatialFit': 'footprint_spatial_fit', 'establishmentMeans': 'establishment_means', 'behavior': 'behavior', 'informationWithheld': 'information_withheld', 'islandGroup': 'island_group', 'municipality': 'municipality', 'materialSampleID': 'material_sample_id', 'samplingProtocol': 'sampling_protocol', 'samplingEffort': 'sampling_effort', 'disposition': 'disposition', 'references': 'references', 'namePublishedInYear': 'name_published_in_year', 'namePublishedIn': 'name_published_in', 'dataset_name': 'dataset_name'}

class Occurrence(models.Model):
    id = models.BigIntegerField(primary_key=True)
    occurrence_id = models.TextField(blank=True, null=True)
    occurrence_remarks = models.TextField(blank=True, null=True)
    occurrence_status = models.TextField(blank=True, null=True)
    institution_id = models.TextField(blank=True, null=True)
    institution_code = models.TextField(blank=True, null=True)
    owner_institution_code = models.TextField(blank=True, null=True)
    collection_id = models.TextField(blank=True, null=True)
    collection_code = models.TextField(blank=True, null=True)
    catalog_number = models.BigIntegerField(blank=True, null=True)
    other_catalog_numbers = models.TextField(blank=True, null=True)
    record_number = models.TextField(blank=True, null=True)
    recorded_by = models.TextField(blank=True, null=True)
    field_number = models.TextField(blank=True, null=True)
    field_notes = models.TextField(blank=True, null=True)
    basis_of_record = models.TextField(blank=True, null=True)
    dataset_id = models.TextField(blank=True, null=True)
    dataset_name = models.TextField(blank=True, null=True)
    language = models.TextField(blank=True, null=True)
    type_field = models.TextField(blank=True, null=True)
    type_status = models.TextField(blank=True, null=True)
    coreid = models.TextField(blank=True, null=True)
    life_stage = models.TextField(blank=True, null=True)
    event_time = models.TextField(blank=True, null=True)
    event_remarks = models.TextField(blank=True, null=True)
    year = models.TextField(blank=True, null=True)
    month = models.TextField(blank=True, null=True)
    day = models.TextField(blank=True, null=True)
    start_day_of_year = models.TextField(blank=True, null=True)
    end_day_of_year = models.TextField(blank=True, null=True)
    event_date = models.TextField(blank=True, null=True)
    event_id = models.TextField(blank=True, null=True)
    verbatim_event_date = models.TextField(blank=True, null=True)
    verbatim_depth = models.TextField(blank=True, null=True)
    kingdom = models.TextField(blank=True, null=True)
    phylum = models.TextField(blank=True, null=True)
    class_field = models.TextField(blank=True, null=True)
    order_field = models.TextField(blank=True, null=True)
    family = models.TextField(blank=True, null=True)
    genus = models.TextField(blank=True, null=True)
    subgenus = models.TextField(blank=True, null=True)
    vernacular_name = models.TextField(blank=True, null=True)
    scientific_name = models.TextField(blank=True, null=True)
    scientific_name_id = models.TextField(blank=True, null=True)
    taxon_rank = models.TextField(blank=True, null=True)
    taxon_id = models.TextField(blank=True, null=True)
    verbatim_taxon_rank = models.TextField(blank=True, null=True)
    associated_taxa = models.TextField(blank=True, null=True)
    specific_epithet = models.TextField(blank=True, null=True)
    scientific_name_authorship = models.TextField(blank=True, null=True)
    accepted_name_usage = models.TextField(blank=True, null=True)
    accepted_name_usage_id = models.TextField(blank=True, null=True)
    original_name_usage = models.TextField(blank=True, null=True)
    name_according_to = models.TextField(blank=True, null=True)
    higher_classification = models.TextField(blank=True, null=True)
    taxon_remarks = models.TextField(blank=True, null=True)
    date_identified = models.TextField(blank=True, null=True)
    identification_qualifier = models.TextField(blank=True, null=True)
    identified_by = models.TextField(blank=True, null=True)
    identification_verification_status = models.TextField(blank=True, null=True)
    previous_identifications = models.TextField(blank=True, null=True)
    county = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    country_code = models.TextField(blank=True, null=True)
    state_province = models.TextField(blank=True, null=True)
    locality = models.TextField(blank=True, null=True)
    location_id = models.TextField(blank=True, null=True)
    higher_geography = models.TextField(blank=True, null=True)
    georeferenced_date = models.TextField(blank=True, null=True)
    georeference_sources = models.TextField(blank=True, null=True)
    georeferenced_by = models.TextField(blank=True, null=True)
    geodetic_datum = models.TextField(blank=True, null=True)
    georeference_protocol = models.TextField(blank=True, null=True)
    georeference_remarks = models.TextField(blank=True, null=True)
    georeference_verification_status = models.TextField(blank=True, null=True)
    decimal_longitude = models.FloatField(blank=True, null=True)
    decimal_latitude = models.FloatField(blank=True, null=True)
    verbatim_latitude = models.TextField(blank=True, null=True)
    verbatim_longitude = models.TextField(blank=True, null=True)
    verbatim_locality = models.TextField(blank=True, null=True)
    verbatim_coordinates = models.TextField(blank=True, null=True)
    coordinate_uncertainty_in_meters = models.TextField(blank=True, null=True)
    verbatim_coordinate_system = models.TextField(blank=True, null=True)
    coordinate_precision = models.TextField(blank=True, null=True)
    location_according_to = models.TextField(blank=True, null=True)
    point_radius_spatial_fit = models.TextField(blank=True, null=True)
    rights = models.TextField(blank=True, null=True)
    rights_holder = models.TextField(blank=True, null=True)
    license_field = models.TextField(blank=True, null=True)
    preparations = models.TextField(blank=True, null=True)
    id_field = models.TextField(blank=True, null=True)
    modified = models.TextField(blank=True, null=True)
    data_generalizations = models.TextField(blank=True, null=True)
    organism_id = models.TextField(blank=True, null=True)
    organism_quantity_type = models.TextField(blank=True, null=True)
    organism_quantity = models.TextField(blank=True, null=True)
    sex = models.TextField(blank=True, null=True)
    individual_count = models.BigIntegerField(blank=True, null=True)
    verbatim_elevation = models.BigIntegerField(blank=True, null=True)
    minimum_elevation_in_meters = models.TextField(blank=True, null=True)
    maximum_elevation_in_meters = models.TextField(blank=True, null=True)
    minimum_depth_in_meters = models.TextField(blank=True, null=True)
    maximum_depth_in_meters = models.TextField(blank=True, null=True)
    water_body = models.TextField(blank=True, null=True)
    island = models.TextField(blank=True, null=True)
    habitat = models.TextField(blank=True, null=True)
    reproductive_condition = models.TextField(blank=True, null=True)
    continent = models.TextField(blank=True, null=True)
    infraspecific_epithet = models.TextField(blank=True, null=True)
    footprint_wkt = models.TextField(blank=True, null=True)
    associated_media = models.TextField(blank=True, null=True)
    associated_sequences = models.TextField(blank=True, null=True)
    associated_references = models.TextField(blank=True, null=True)
    nomenclatural_code = models.TextField(blank=True, null=True)
    footprint_spatial_fit = models.TextField(blank=True, null=True)
    establishment_means = models.TextField(blank=True, null=True)
    behavior = models.TextField(blank=True, null=True)
    information_withheld = models.TextField(blank=True, null=True)
    island_group = models.TextField(blank=True, null=True)
    municipality = models.TextField(blank=True, null=True)
    material_sample_id = models.TextField(blank=True, null=True)
    sampling_protocol = models.TextField(blank=True, null=True)
    sampling_effort = models.TextField(blank=True, null=True)
    disposition = models.TextField(blank=True, null=True)
    references = models.TextField(blank=True, null=True)
    name_published_in_year = models.TextField(blank=True, null=True)
    name_published_in = models.TextField(blank=True, null=True)

    @property
    def dataset(self):
        dataset = get_object_or_404(Dataset, name=self.dataset_name)
        return dataset

    @property
    def display_terms(self):
        dict_values = vars(self)
        terms_map = dict((v,k) for k,v in OCCURRENCE_COLUMN_MAP.items())
        ret = {}
        for k,v in dict_values.items():
            if k in terms_map:
                ret[terms_map[k]] = v or ''
        return ret

    #class Meta:
    #    managed = False
    #    db_table = 'data_occurrence'

class PublicDataManager(models.Manager):
    def get_queryset(self):
        public_dataset_names = [x['name'] for x in Dataset.public_objects.values('name').all()]
        return super().get_queryset().filter(taibif_dataset_name__in=public_dataset_names)

    def filter_by_key_values(self, filters):
        query = self.get_queryset()
        has_filter = False
        #print (filters)
        for key, values in filters:
            #print (key, values)
            if key == 'q':
                has_filter = True
                v = values[0] # only get one
                if not v:
                    continue
                # find has species_id first
                #species_list = Taxon.find_name(v, 'species', self.using)
                #species_ids = [x.id for x in species_list]
                #if species_ids:
                    #query = query.filter(Q(taxon_species_id__in=species_ids) |
                    #                     Q(taxon_genus_id__in=species_ids))
                #    query = query.filter(taxon_species_id__in=species_ids)
                #else:
                #    if self.using == '':
                query = query.filter(Q(vernacular_name__icontains=v) | Q(scientific_name__icontains=v))
                #    elif self.using == 'latin':
                #        query = query.filter(scientific_name__icontains=v)
                #    elif self.using == 'zh':
                #        query = query.filter(vernacular_name__icontains=v)
            #if menu_key == 'core':
            #    d = DATA_MAPPING['core'][item_keys]
            #    query = query.filter(dwc_core_type__exact=d)
            if key == 'year':
                has_filter = True
                query = query.filter(year__in=values)
            if key == 'month':
                has_filter = True
                query = query.filter(month__in=values)
            # TODO: change simpledata.country to country_code
            if key == 'countrycode':
                has_filter = True
                query = query.filter(country__in=values)
            if key == 'dataset':
                has_filter = True
                query = query.filter(taibif_dataset_name__in=values)
            if key == 'publisher':
                has_filter = True
                datasets = Dataset.objects.filter(organization__in=values)
                dataset_names = [x.name for x in datasets]
                query = query.filter(taibif_dataset_name__in=dataset_names)

            if key == 'taxon_key':
                has_filter = True
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
                    has_filter = True
                    query = query.filter(**{key:values[0]})
        return has_filter, query


'''
class SimpleData(models.Model):

    NUM_PER_PAGE = 50

    taibif = models.OneToOneField('RawDataOccurrence', on_delete=models.CASCADE, primary_key=True, related_name='simple_data')
    taxon_kingdom = models.ForeignKey(Taxon, on_delete=models.CASCADE, null=True, related_name='kingdom_data')
    taxon_phylum = models.ForeignKey(Taxon, on_delete=models.CASCADE, null=True, related_name='phylum_data')
    taxon_class = models.ForeignKey(Taxon, on_delete=models.CASCADE, null=True, related_name='class_data')
    taxon_order = models.ForeignKey(Taxon, on_delete=models.CASCADE, null=True, related_name='order_data')
    taxon_family = models.ForeignKey(Taxon, on_delete=models.CASCADE, null=True, related_name='family_data')
    taxon_genus = models.ForeignKey(Taxon, on_delete=models.CASCADE, null=True, related_name='genus_data')
    taxon_species = models.ForeignKey(Taxon, on_delete=models.CASCADE, null=True, related_name='species_data')
    scientific_name = models.CharField('scientific_name', max_length=1000, null=True)
    vernacular_name = models.CharField('vernacular_name', max_length=1000, null=True)
    year = models.PositiveSmallIntegerField(null=True)
    month = models.PositiveSmallIntegerField(null=True)
    day = models.PositiveSmallIntegerField(null=True)
    #epithnet
    longitude = models.DecimalField('coordinates_longitude_decimal', decimal_places=8, max_digits=11, null=True, blank=True)
    Latitude = models.DecimalField('coordinates_latitude_decimal', decimal_places=8, max_digits=10, null=True, blank=True)
    country = models.CharField('country', max_length=1000, null=True)
    taibif_dataset_name = models.TextField(blank=True, null=True)
    spname = models.CharField('species_name', max_length=1000, null=True)

    objects = models.Manager()
    public_objects = PublicDataManager()

    @property
    def date_display(self):
        s = ''
        s += '{}年'.format(self.year)
        s += '{}月'.format(self.month)
        if self.day:
            s += '{}日'.format(self.day)
        return '{}年{}月{}日'.format(
            self.year if self.year else '--',
            self.month if self.month else '--',
            self.day if self.day else '--',
        )

class PublicRawOccurrenceDataManager(models.Manager):
    def get_queryset(self):
        public_dataset_names = [x['name'] for x in Dataset.public_objects.values('name').all()]
        return super().get_queryset().filter(taibif_dataset_name__in=public_dataset_names)

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class RawDataOccurrence(models.Model):
    NUM_PER_PAGE = 50
    taibif_id = models.BigIntegerField(primary_key=True)
    lifestage = models.TextField(db_column='lifeStage', blank=True, null=True)  # Field name made lowercase.
    institutioncode = models.TextField(db_column='institutionCode', blank=True, null=True)  # Field name made lowercase.
    datageneralizations = models.TextField(db_column='dataGeneralizations', blank=True, null=True)  # Field name made lowercase.
    dateidentified = models.TextField(db_column='dateIdentified', blank=True, null=True)  # Field name made lowercase.
    language = models.TextField(blank=True, null=True)
    locationaccordingto = models.TextField(db_column='locationAccordingTo', blank=True, null=True)  # Field name made lowercase.
    namepublishedinyear = models.TextField(db_column='namePublishedInYear', blank=True, null=True)  # Field name made lowercase.
    informationwithheld = models.TextField(db_column='informationWithheld', blank=True, null=True)  # Field name made lowercase.
    collectionid = models.TextField(db_column='collectionID', blank=True, null=True)  # Field name made lowercase.
    eventid = models.TextField(db_column='eventID', blank=True, null=True)  # Field name made lowercase.
    disposition = models.TextField(blank=True, null=True)
    institutionid = models.TextField(db_column='institutionID', blank=True, null=True)  # Field name made lowercase.
    namepublishedin = models.TextField(db_column='namePublishedIn', blank=True, null=True)  # Field name made lowercase.
    rightsholder = models.TextField(db_column='rightsHolder', blank=True, null=True)  # Field name made lowercase.
    recordedby = models.TextField(db_column='recordedBy', blank=True, null=True)  # Field name made lowercase.
    organismquantitytype = models.TextField(db_column='organismQuantityType', blank=True, null=True)  # Field name made lowercase.
    acceptednameusageid = models.TextField(db_column='acceptedNameUsageID', blank=True, null=True)  # Field name made lowercase.
    kingdom = models.TextField(blank=True, null=True)
    taxonid = models.TextField(db_column='taxonID', blank=True, null=True)  # Field name made lowercase.
    minimumdepthinmeters = models.TextField(db_column='minimumDepthInMeters', blank=True, null=True)  # Field name made lowercase.
    organismquantity = models.TextField(db_column='organismQuantity', blank=True, null=True)  # Field name made lowercase.
    identificationremarks = models.TextField(db_column='identificationRemarks', blank=True, null=True)  # Field name made lowercase.
    islandgroup = models.TextField(db_column='islandGroup', blank=True, null=True)  # Field name made lowercase.
    fieldnotes = models.TextField(db_column='fieldNotes', blank=True, null=True)  # Field name made lowercase.
    preparations = models.TextField(blank=True, null=True)
    modified = models.TextField(blank=True, null=True)
    verbatimlocality = models.TextField(db_column='verbatimLocality', blank=True, null=True)  # Field name made lowercase.
    datasetid = models.TextField(db_column='datasetID', blank=True, null=True)  # Field name made lowercase.
    verbatimeventdate = models.TextField(db_column='verbatimEventDate', blank=True, null=True)  # Field name made lowercase.
    decimallongitude = models.TextField(db_column='decimalLongitude', blank=True, null=True)  # Field name made lowercase.
    verbatimdepth = models.TextField(db_column='verbatimDepth', blank=True, null=True)  # Field name made lowercase.
    associatedtaxa = models.TextField(db_column='associatedTaxa', blank=True, null=True)  # Field name made lowercase.
    countrycode = models.TextField(db_column='countryCode', blank=True, null=True)  # Field name made lowercase.
    verbatimlatitude = models.TextField(db_column='verbatimLatitude', blank=True, null=True)  # Field name made lowercase.
    verbatimelevation = models.TextField(db_column='verbatimElevation', blank=True, null=True)  # Field name made lowercase.
    georeferenceprotocol = models.TextField(db_column='georeferenceProtocol', blank=True, null=True)  # Field name made lowercase.
    recordnumber = models.TextField(db_column='recordNumber', blank=True, null=True)  # Field name made lowercase.
    phylum = models.TextField(blank=True, null=True)
    geodeticdatum = models.TextField(db_column='geodeticDatum', blank=True, null=True)  # Field name made lowercase.
    verbatimtaxonrank = models.TextField(db_column='verbatimTaxonRank', blank=True, null=True)  # Field name made lowercase.
    order = models.TextField(blank=True, null=True)
    individualcount = models.TextField(db_column='individualCount', blank=True, null=True)  # Field name made lowercase.
    startdayofyear = models.TextField(db_column='startDayOfYear', blank=True, null=True)  # Field name made lowercase.
    maximumelevationinmeters = models.TextField(db_column='maximumElevationInMeters', blank=True, null=True)  # Field name made lowercase.
    occurrencestatus = models.TextField(db_column='occurrenceStatus', blank=True, null=True)  # Field name made lowercase.
    island = models.TextField(blank=True, null=True)
    datasetname = models.TextField(db_column='datasetName', blank=True, null=True)  # Field name made lowercase.
    parenteventid = models.TextField(db_column='parentEventID', blank=True, null=True)  # Field name made lowercase.
    identifiedby = models.TextField(db_column='identifiedBy', blank=True, null=True)  # Field name made lowercase.
    id = models.TextField(blank=True, null=True)
    decimallatitude = models.TextField(db_column='decimalLatitude', blank=True, null=True)  # Field name made lowercase.
    vernacularname = models.TextField(db_column='vernacularName', blank=True, null=True)  # Field name made lowercase.
    footprintwkt = models.TextField(db_column='footprintWKT', blank=True, null=True)  # Field name made lowercase.
    scientificname = models.TextField(db_column='scientificName', blank=True, null=True)  # Field name made lowercase.
    ownerinstitutioncode = models.TextField(db_column='ownerInstitutionCode', blank=True, null=True)  # Field name made lowercase.
    infraspecificepithet = models.TextField(db_column='infraspecificEpithet', blank=True, null=True)  # Field name made lowercase.
    specificepithet = models.TextField(db_column='specificEpithet', blank=True, null=True)  # Field name made lowercase.
    georeferencesources = models.TextField(db_column='georeferenceSources', blank=True, null=True)  # Field name made lowercase.
    type = models.TextField(blank=True, null=True)
    nomenclaturalcode = models.TextField(db_column='nomenclaturalCode', blank=True, null=True)  # Field name made lowercase.
    month = models.TextField(blank=True, null=True)
    originalnameusage = models.TextField(db_column='originalNameUsage', blank=True, null=True)  # Field name made lowercase.
    collectioncode = models.TextField(db_column='collectionCode', blank=True, null=True)  # Field name made lowercase.
    eventremarks = models.TextField(db_column='eventRemarks', blank=True, null=True)  # Field name made lowercase.
    highergeography = models.TextField(db_column='higherGeography', blank=True, null=True)  # Field name made lowercase.
    identificationqualifier = models.TextField(db_column='identificationQualifier', blank=True, null=True)  # Field name made lowercase.
    nameaccordingto = models.TextField(db_column='nameAccordingTo', blank=True, null=True)  # Field name made lowercase.
    coordinateuncertaintyinmeters = models.TextField(db_column='coordinateUncertaintyInMeters', blank=True, null=True)  # Field name made lowercase.
    country = models.TextField(blank=True, null=True)
    stateprovince = models.TextField(db_column='stateProvince', blank=True, null=True)  # Field name made lowercase.
    verbatimcoordinatesystem = models.TextField(db_column='verbatimCoordinateSystem', blank=True, null=True)  # Field name made lowercase.
    subgenus = models.TextField(blank=True, null=True)
    verbatimlongitude = models.TextField(db_column='verbatimLongitude', blank=True, null=True)  # Field name made lowercase.
    family = models.TextField(blank=True, null=True)
    organismid = models.TextField(db_column='organismID', blank=True, null=True)  # Field name made lowercase.
    locationid = models.TextField(db_column='locationID', blank=True, null=True)  # Field name made lowercase.
    coordinateprecision = models.TextField(db_column='coordinatePrecision', blank=True, null=True)  # Field name made lowercase.
    enddayofyear = models.TextField(db_column='endDayOfYear', blank=True, null=True)  # Field name made lowercase.
    taxonremarks = models.TextField(db_column='taxonRemarks', blank=True, null=True)  # Field name made lowercase.
    waterbody = models.TextField(db_column='waterBody', blank=True, null=True)  # Field name made lowercase.
    associatedsequences = models.TextField(db_column='associatedSequences', blank=True, null=True)  # Field name made lowercase.
    othercatalognumbers = models.TextField(db_column='otherCatalogNumbers', blank=True, null=True)  # Field name made lowercase.
    county = models.TextField(blank=True, null=True)
    maximumdepthinmeters = models.TextField(db_column='maximumDepthInMeters', blank=True, null=True)  # Field name made lowercase.
    pointradiusspatialfit = models.TextField(db_column='pointRadiusSpatialFit', blank=True, null=True)  # Field name made lowercase.
    coreid = models.TextField(blank=True, null=True)
    eventdate = models.TextField(db_column='eventDate', blank=True, null=True)  # Field name made lowercase.
    georeferenceremarks = models.TextField(db_column='georeferenceRemarks', blank=True, null=True)  # Field name made lowercase.
    basisofrecord = models.TextField(db_column='basisOfRecord', blank=True, null=True)  # Field name made lowercase.
    municipality = models.TextField(blank=True, null=True)
    verbatimcoordinates = models.TextField(db_column='verbatimCoordinates', blank=True, null=True)  # Field name made lowercase.
    eventtime = models.TextField(db_column='eventTime', blank=True, null=True)  # Field name made lowercase.
    genus = models.TextField(blank=True, null=True)
    associatedmedia = models.TextField(db_column='associatedMedia', blank=True, null=True)  # Field name made lowercase.
    establishmentmeans = models.TextField(db_column='establishmentMeans', blank=True, null=True)  # Field name made lowercase.
    day = models.TextField(blank=True, null=True)
    references = models.TextField(blank=True, null=True)
    identificationverificationstatus = models.TextField(db_column='identificationVerificationStatus', blank=True, null=True)  # Field name made lowercase.
    georeferencedby = models.TextField(db_column='georeferencedBy', blank=True, null=True)  # Field name made lowercase.
    georeferenceddate = models.TextField(db_column='georeferencedDate', blank=True, null=True)  # Field name made lowercase.
    materialsampleid = models.TextField(db_column='materialSampleID', blank=True, null=True)  # Field name made lowercase.
    rights = models.TextField(blank=True, null=True)
    license = models.TextField(blank=True, null=True)
    continent = models.TextField(blank=True, null=True)
    reproductivecondition = models.TextField(db_column='reproductiveCondition', blank=True, null=True)  # Field name made lowercase.
    occurrenceid = models.TextField(db_column='occurrenceID', blank=True, null=True)  # Field name made lowercase.
    georeferenceverificationstatus = models.TextField(db_column='georeferenceVerificationStatus', blank=True, null=True)  # Field name made lowercase.
    catalognumber = models.TextField(db_column='catalogNumber', blank=True, null=True)  # Field name made lowercase.
    minimumelevationinmeters = models.TextField(db_column='minimumElevationInMeters', blank=True, null=True)  # Field name made lowercase.
    scientificnameid = models.TextField(db_column='scientificNameID', blank=True, null=True)  # Field name made lowercase.
    acceptednameusage = models.TextField(db_column='acceptedNameUsage', blank=True, null=True)  # Field name made lowercase.
    scientificnameauthorship = models.TextField(db_column='scientificNameAuthorship', blank=True, null=True)  # Field name made lowercase.
    fieldnumber = models.TextField(db_column='fieldNumber', blank=True, null=True)  # Field name made lowercase.
    class_field = models.TextField(db_column='class', blank=True, null=True)  # Field renamed because it was a Python reserved word.
    higherclassification = models.TextField(db_column='higherClassification', blank=True, null=True)  # Field name made lowercase.
    samplingprotocol = models.TextField(db_column='samplingProtocol', blank=True, null=True)  # Field name made lowercase.
    behavior = models.TextField(blank=True, null=True)
    previousidentifications = models.TextField(db_column='previousIdentifications', blank=True, null=True)  # Field name made lowercase.
    sex = models.TextField(blank=True, null=True)
    occurrenceremarks = models.TextField(db_column='occurrenceRemarks', blank=True, null=True)  # Field name made lowercase.
    taxonrank = models.TextField(db_column='taxonRank', blank=True, null=True)  # Field name made lowercase.
    typestatus = models.TextField(db_column='typeStatus', blank=True, null=True)  # Field name made lowercase.
    habitat = models.TextField(blank=True, null=True)
    locality = models.TextField(blank=True, null=True)
    year = models.TextField(blank=True, null=True)
    samplingeffort = models.TextField(db_column='samplingEffort', blank=True, null=True)  # Field name made lowercase.
    footprintspatialfit = models.TextField(db_column='footprintSpatialFit', blank=True, null=True)  # Field name made lowercase.
    associatedreferences = models.TextField(db_column='associatedReferences', blank=True, null=True)  # Field name made lowercase.
    taibif_dataset_name = models.TextField(blank=True, null=True)

    @property
    def taibif_dataset(self):
        d = Dataset.objects.values('title', 'id', 'name').filter(name__exact=self.taibif_dataset_name).first()
        return d

    objects = models.Manager()
    public_objects = PublicRawOccurrenceDataManager()

    class Meta:
        managed = False
        db_table = 'raw_data_occurrence'

        indexes = [
            models.Index(fields=['year']),
            models.Index(fields=['scientificname']),
            models.Index(fields=['kingdom']),
            models.Index(fields=['phylum']),
            models.Index(fields=['class_field']),
            models.Index(fields=['order']),
        ]
'''

class Taxon20200619(models.Model):
    index = models.BigIntegerField(blank=True, null=True)
    id = models.TextField(primary_key=True)
    taxonid = models.TextField(db_column='taxonID', blank=True, null=True)  # Field name made lowercase.
    scientificnameid = models.TextField(db_column='scientificNameID', blank=True, null=True)  # Field name made lowercase.
    kingdom = models.TextField(blank=True, null=True)
    phylum = models.TextField(blank=True, null=True)
    class_field = models.TextField(db_column='class', blank=True, null=True)  # Field renamed because it was a Python reserved word.
    order = models.TextField(blank=True, null=True)
    family = models.TextField(blank=True, null=True)
    genus = models.TextField(blank=True, null=True)
    specificepithet = models.TextField(db_column='specificEpithet', blank=True, null=True)  # Field name made lowercase.
    infraspecificepithet = models.TextField(db_column='infraspecificEpithet', blank=True, null=True)  # Field name made lowercase.
    scientificnameauthorship = models.TextField(db_column='scientificNameAuthorship', blank=True, null=True)  # Field name made lowercase.
    vernacularname = models.TextField(db_column='vernacularName', blank=True, null=True)  # Field name made lowercase.
    taxonremarks = models.TextField(db_column='taxonRemarks', blank=True, null=True)  # Field name made lowercase.
    dataset_name = models.TextField(blank=True, null=True)
    scientificname = models.TextField(db_column='scientificName', blank=True, null=True)  # Field name made lowercase.
    taxonrank = models.TextField(db_column='taxonRank', blank=True, null=True)  # Field name made lowercase.
    taxonomicstatus = models.TextField(db_column='taxonomicStatus', blank=True, null=True)  # Field name made lowercase.
    acceptednameusageid = models.TextField(db_column='acceptedNameUsageID', blank=True, null=True)  # Field name made lowercase.
    subgenus = models.FloatField(blank=True, null=True)
    nameaccordingto = models.TextField(db_column='nameAccordingTo', blank=True, null=True)  # Field name made lowercase.
    nomenclaturalstatus = models.TextField(db_column='nomenclaturalStatus', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'taxon_20200619'

class Event20200619(models.Model):
    index = models.BigIntegerField(blank=True, null=True)
    id = models.TextField(primary_key=True)
    eventid = models.TextField(db_column='eventID', blank=True, null=True)  # Field name made lowercase.
    parenteventid = models.TextField(db_column='parentEventID', blank=True, null=True)  # Field name made lowercase.
    samplingprotocol = models.TextField(db_column='samplingProtocol', blank=True, null=True)  # Field name made lowercase.
    samplesizevalue = models.FloatField(db_column='sampleSizeValue', blank=True, null=True)  # Field name made lowercase.
    samplesizeunit = models.TextField(db_column='sampleSizeUnit', blank=True, null=True)  # Field name made lowercase.
    samplingeffort = models.TextField(db_column='samplingEffort', blank=True, null=True)  # Field name made lowercase.
    eventdate = models.TextField(db_column='eventDate', blank=True, null=True)  # Field name made lowercase.
    eventtime = models.TextField(db_column='eventTime', blank=True, null=True)  # Field name made lowercase.
    locationid = models.TextField(db_column='locationID', blank=True, null=True)  # Field name made lowercase.
    decimallatitude = models.TextField(db_column='decimalLatitude', blank=True, null=True)  # Field name made lowercase.
    decimallongitude = models.TextField(db_column='decimalLongitude', blank=True, null=True)  # Field name made lowercase.
    geodeticdatum = models.TextField(db_column='geodeticDatum', blank=True, null=True)  # Field name made lowercase.
    coordinateuncertaintyinmeters = models.FloatField(db_column='coordinateUncertaintyInMeters', blank=True, null=True)  # Field name made lowercase.
    coordinateprecision = models.FloatField(db_column='coordinatePrecision', blank=True, null=True)  # Field name made lowercase.
    dataset_name = models.TextField(blank=True, null=True)
    verbatimelevation = models.FloatField(db_column='verbatimElevation', blank=True, null=True)  # Field name made lowercase.
    verbatimlatitude = models.FloatField(db_column='verbatimLatitude', blank=True, null=True)  # Field name made lowercase.
    verbatimlongitude = models.FloatField(db_column='verbatimLongitude', blank=True, null=True)  # Field name made lowercase.
    verbatimcoordinatesystem = models.TextField(db_column='verbatimCoordinateSystem', blank=True, null=True)  # Field name made lowercase.
    year = models.FloatField(blank=True, null=True)
    month = models.FloatField(blank=True, null=True)
    day = models.FloatField(blank=True, null=True)
    habitat = models.TextField(blank=True, null=True)
    eventremarks = models.TextField(db_column='eventRemarks', blank=True, null=True)  # Field name made lowercase.
    countrycode = models.TextField(db_column='countryCode', blank=True, null=True)  # Field name made lowercase.
    county = models.TextField(blank=True, null=True)
    locality = models.TextField(blank=True, null=True)
    q_year = models.FloatField(blank=True, null=True)
    q_month = models.FloatField(blank=True, null=True)
    q_day = models.FloatField(blank=True, null=True)
    municipality = models.TextField(blank=True, null=True)
    geologicalcontextid = models.TextField(db_column='geologicalContextID', blank=True, null=True)  # Field name made lowercase.
    country = models.TextField(blank=True, null=True)
    stateprovince = models.TextField(db_column='stateProvince', blank=True, null=True)  # Field name made lowercase.
    type = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'event_20200619'

class CopyNew(models.Model):
    index = models.BigIntegerField(blank=True, null=True)
    occurrenceid = models.TextField(db_column='occurrenceID', blank=True, null=True)  # Field name made lowercase.
    occurrenceremarks = models.TextField(db_column='occurrenceRemarks', blank=True, null=True)  # Field name made lowercase.
    occurrencestatus = models.TextField(db_column='occurrenceStatus', blank=True, null=True)  # Field name made lowercase.
    institutionid = models.TextField(db_column='institutionID', blank=True, null=True)  # Field name made lowercase.
    institutioncode = models.TextField(db_column='institutionCode', blank=True, null=True)  # Field name made lowercase.
    ownerinstitutioncode = models.TextField(db_column='ownerInstitutionCode', blank=True, null=True)  # Field name made lowercase.
    collectionid = models.TextField(db_column='collectionID', blank=True, null=True)  # Field name made lowercase.
    collectioncode = models.TextField(db_column='collectionCode', blank=True, null=True)  # Field name made lowercase.
    catalognumber = models.TextField(db_column='catalogNumber', blank=True, null=True)  # Field name made lowercase.
    othercatalognumbers = models.TextField(db_column='otherCatalogNumbers', blank=True, null=True)  # Field name made lowercase.
    recordnumber = models.TextField(db_column='recordNumber', blank=True, null=True)  # Field name made lowercase.
    recordedby = models.TextField(db_column='recordedBy', blank=True, null=True)  # Field name made lowercase.
    fieldnumber = models.TextField(db_column='fieldNumber', blank=True, null=True)  # Field name made lowercase.
    fieldnotes = models.TextField(db_column='fieldNotes', blank=True, null=True)  # Field name made lowercase.
    basisofrecord = models.TextField(db_column='basisOfRecord', blank=True, null=True)  # Field name made lowercase.
    datasetid = models.TextField(db_column='datasetID', blank=True, null=True)  # Field name made lowercase.
    datasetname = models.TextField(db_column='datasetName', blank=True, null=True)  # Field name made lowercase.
    language = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    typestatus = models.TextField(db_column='typeStatus', blank=True, null=True)  # Field name made lowercase.
    coreid = models.TextField(blank=True, null=True)
    lifestage = models.TextField(db_column='lifeStage', blank=True, null=True)  # Field name made lowercase.
    eventtime = models.TextField(db_column='eventTime', blank=True, null=True)  # Field name made lowercase.
    eventremarks = models.TextField(db_column='eventRemarks', blank=True, null=True)  # Field name made lowercase.
    year = models.TextField(blank=True, null=True)
    month = models.TextField(blank=True, null=True)
    day = models.TextField(blank=True, null=True)
    startdayofyear = models.TextField(db_column='startDayOfYear', blank=True, null=True)  # Field name made lowercase.
    enddayofyear = models.TextField(db_column='endDayOfYear', blank=True, null=True)  # Field name made lowercase.
    eventdate = models.TextField(db_column='eventDate', blank=True, null=True)  # Field name made lowercase.
    eventid = models.TextField(db_column='eventID', blank=True, null=True)  # Field name made lowercase.
    verbatimeventdate = models.TextField(db_column='verbatimEventDate', blank=True, null=True)  # Field name made lowercase.
    verbatimdepth = models.TextField(db_column='verbatimDepth', blank=True, null=True)  # Field name made lowercase.
    kingdom = models.TextField(blank=True, null=True)
    phylum = models.TextField(blank=True, null=True)
    class_field = models.TextField(db_column='class', blank=True, null=True)  # Field renamed because it was a Python reserved word.
    order = models.TextField(blank=True, null=True)
    family = models.TextField(blank=True, null=True)
    genus = models.TextField(blank=True, null=True)
    subgenus = models.TextField(blank=True, null=True)
    vernacularname = models.TextField(db_column='vernacularName', blank=True, null=True)  # Field name made lowercase.
    scientificname = models.TextField(db_column='scientificName', blank=True, null=True)  # Field name made lowercase.
    scientificnameid = models.TextField(db_column='scientificNameID', blank=True, null=True)  # Field name made lowercase.
    taxonrank = models.TextField(db_column='taxonRank', blank=True, null=True)  # Field name made lowercase.
    taxonid = models.TextField(db_column='taxonID', blank=True, null=True)  # Field name made lowercase.
    verbatimtaxonrank = models.TextField(db_column='verbatimTaxonRank', blank=True, null=True)  # Field name made lowercase.
    associatedtaxa = models.TextField(db_column='associatedTaxa', blank=True, null=True)  # Field name made lowercase.
    specificepithet = models.TextField(db_column='specificEpithet', blank=True, null=True)  # Field name made lowercase.
    scientificnameauthorship = models.TextField(db_column='scientificNameAuthorship', blank=True, null=True)  # Field name made lowercase.
    acceptednameusage = models.TextField(db_column='acceptedNameUsage', blank=True, null=True)  # Field name made lowercase.
    acceptednameusageid = models.TextField(db_column='acceptedNameUsageID', blank=True, null=True)  # Field name made lowercase.
    originalnameusage = models.TextField(db_column='originalNameUsage', blank=True, null=True)  # Field name made lowercase.
    nameaccordingto = models.TextField(db_column='nameAccordingTo', blank=True, null=True)  # Field name made lowercase.
    higherclassification = models.TextField(db_column='higherClassification', blank=True, null=True)  # Field name made lowercase.
    taxonremarks = models.TextField(db_column='taxonRemarks', blank=True, null=True)  # Field name made lowercase.
    dateidentified = models.TextField(db_column='dateIdentified', blank=True, null=True)  # Field name made lowercase.
    identificationqualifier = models.TextField(db_column='identificationQualifier', blank=True, null=True)  # Field name made lowercase.
    identifiedby = models.TextField(db_column='identifiedBy', blank=True, null=True)  # Field name made lowercase.
    identificationverificationstatus = models.TextField(db_column='identificationVerificationStatus', blank=True, null=True)  # Field name made lowercase.
    previousidentifications = models.TextField(db_column='previousIdentifications', blank=True, null=True)  # Field name made lowercase.
    county = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    countrycode = models.TextField(db_column='countryCode', blank=True, null=True)  # Field name made lowercase.
    stateprovince = models.TextField(db_column='stateProvince', blank=True, null=True)  # Field name made lowercase.
    locality = models.TextField(blank=True, null=True)
    locationid = models.TextField(db_column='locationID', blank=True, null=True)  # Field name made lowercase.
    highergeography = models.TextField(db_column='higherGeography', blank=True, null=True)  # Field name made lowercase.
    georeferenceddate = models.TextField(db_column='georeferencedDate', blank=True, null=True)  # Field name made lowercase.
    georeferencesources = models.TextField(db_column='georeferenceSources', blank=True, null=True)  # Field name made lowercase.
    georeferencedby = models.TextField(db_column='georeferencedBy', blank=True, null=True)  # Field name made lowercase.
    geodeticdatum = models.TextField(db_column='geodeticDatum', blank=True, null=True)  # Field name made lowercase.
    georeferenceprotocol = models.TextField(db_column='georeferenceProtocol', blank=True, null=True)  # Field name made lowercase.
    georeferenceremarks = models.TextField(db_column='georeferenceRemarks', blank=True, null=True)  # Field name made lowercase.
    georeferenceverificationstatus = models.TextField(db_column='georeferenceVerificationStatus', blank=True, null=True)  # Field name made lowercase.
    decimallongitude = models.TextField(db_column='decimalLongitude', blank=True, null=True)  # Field name made lowercase.
    decimallatitude = models.TextField(db_column='decimalLatitude', blank=True, null=True)  # Field name made lowercase.
    verbatimlatitude = models.TextField(db_column='verbatimLatitude', blank=True, null=True)  # Field name made lowercase.
    verbatimlongitude = models.TextField(db_column='verbatimLongitude', blank=True, null=True)  # Field name made lowercase.
    verbatimlocality = models.TextField(db_column='verbatimLocality', blank=True, null=True)  # Field name made lowercase.
    verbatimcoordinates = models.TextField(db_column='verbatimCoordinates', blank=True, null=True)  # Field name made lowercase.
    coordinateuncertaintyinmeters = models.TextField(db_column='coordinateUncertaintyInMeters', blank=True, null=True)  # Field name made lowercase.
    verbatimcoordinatesystem = models.TextField(db_column='verbatimCoordinateSystem', blank=True, null=True)  # Field name made lowercase.
    coordinateprecision = models.TextField(db_column='coordinatePrecision', blank=True, null=True)  # Field name made lowercase.
    locationaccordingto = models.TextField(db_column='locationAccordingTo', blank=True, null=True)  # Field name made lowercase.
    pointradiusspatialfit = models.TextField(db_column='pointRadiusSpatialFit', blank=True, null=True)  # Field name made lowercase.
    rights = models.TextField(blank=True, null=True)
    rightsholder = models.TextField(db_column='rightsHolder', blank=True, null=True)  # Field name made lowercase.
    license = models.TextField(blank=True, null=True)
    preparations = models.TextField(blank=True, null=True)
    id = models.TextField(primary_key=True)
    modified = models.TextField(blank=True, null=True)
    datageneralizations = models.TextField(db_column='dataGeneralizations', blank=True, null=True)  # Field name made lowercase.
    organismid = models.TextField(db_column='organismID', blank=True, null=True)  # Field name made lowercase.
    organismquantitytype = models.TextField(db_column='organismQuantityType', blank=True, null=True)  # Field name made lowercase.
    organismquantity = models.TextField(db_column='organismQuantity', blank=True, null=True)  # Field name made lowercase.
    sex = models.TextField(blank=True, null=True)
    individualcount = models.TextField(db_column='individualCount', blank=True, null=True)  # Field name made lowercase.
    verbatimelevation = models.TextField(db_column='verbatimElevation', blank=True, null=True)  # Field name made lowercase.
    minimumelevationinmeters = models.TextField(db_column='minimumElevationInMeters', blank=True, null=True)  # Field name made lowercase.
    maximumelevationinmeters = models.TextField(db_column='maximumElevationInMeters', blank=True, null=True)  # Field name made lowercase.
    minimumdepthinmeters = models.TextField(db_column='minimumDepthInMeters', blank=True, null=True)  # Field name made lowercase.
    maximumdepthinmeters = models.TextField(db_column='maximumDepthInMeters', blank=True, null=True)  # Field name made lowercase.
    waterbody = models.TextField(db_column='waterBody', blank=True, null=True)  # Field name made lowercase.
    island = models.TextField(blank=True, null=True)
    habitat = models.TextField(blank=True, null=True)
    reproductivecondition = models.TextField(db_column='reproductiveCondition', blank=True, null=True)  # Field name made lowercase.
    continent = models.TextField(blank=True, null=True)
    infraspecificepithet = models.TextField(db_column='infraspecificEpithet', blank=True, null=True)  # Field name made lowercase.
    footprintwkt = models.TextField(db_column='footprintWKT', blank=True, null=True)  # Field name made lowercase.
    associatedmedia = models.TextField(db_column='associatedMedia', blank=True, null=True)  # Field name made lowercase.
    associatedsequences = models.TextField(db_column='associatedSequences', blank=True, null=True)  # Field name made lowercase.
    associatedreferences = models.TextField(db_column='associatedReferences', blank=True, null=True)  # Field name made lowercase.
    nomenclaturalcode = models.TextField(db_column='nomenclaturalCode', blank=True, null=True)  # Field name made lowercase.
    footprintspatialfit = models.TextField(db_column='footprintSpatialFit', blank=True, null=True)  # Field name made lowercase.
    establishmentmeans = models.TextField(db_column='establishmentMeans', blank=True, null=True)  # Field name made lowercase.
    behavior = models.TextField(blank=True, null=True)
    informationwithheld = models.TextField(db_column='informationWithheld', blank=True, null=True)  # Field name made lowercase.
    islandgroup = models.TextField(db_column='islandGroup', blank=True, null=True)  # Field name made lowercase.
    municipality = models.TextField(blank=True, null=True)
    materialsampleid = models.TextField(db_column='materialSampleID', blank=True, null=True)  # Field name made lowercase.
    samplingprotocol = models.TextField(db_column='samplingProtocol', blank=True, null=True)  # Field name made lowercase.
    samplingeffort = models.TextField(db_column='samplingEffort', blank=True, null=True)  # Field name made lowercase.
    disposition = models.TextField(blank=True, null=True)
    references = models.TextField(blank=True, null=True)
    namepublishedinyear = models.TextField(db_column='namePublishedInYear', blank=True, null=True)  # Field name made lowercase.
    namepublishedin = models.TextField(db_column='namePublishedIn', blank=True, null=True)  # Field name made lowercase.
    dataset_name = models.TextField(blank=True, null=True)
    q_year = models.TextField(blank=True, null=True)
    q_month = models.TextField(blank=True, null=True)
    q_day = models.TextField(blank=True, null=True)
    identificationremarks = models.TextField(db_column='identificationRemarks', blank=True, null=True)  # Field name made lowercase.
    parenteventid = models.TextField(db_column='parentEventID', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'copy_new'

class taibifcode(models.Model):
    objid = models.CharField(blank=True, null=True, max_length=128)
    name = models.CharField(blank=True, null=True, max_length=128)
    name_c = models.CharField(blank=True, null=True, max_length=128)
    desc = models.TextField(blank=True, null=True)
    