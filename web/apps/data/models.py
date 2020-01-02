from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from django.shortcuts import get_object_or_404

class DataSet(models.Model):
    title = models.CharField('title', max_length=300)
    name = models.CharField('name', max_length=128) # ipt shortname
    description = models.TextField('Description')
    author = models.CharField('author', max_length=128)
    pub_date = models.DateTimeField('Publish Date')
    guid = models.CharField('GUID', max_length=40)
    guid_verbatim = models.CharField('GUID', max_length=100)
    dwc_core_type = models.CharField('Dw-C Core Type', max_length=128)
    data_license = models.CharField('Data License', max_length=128)
    stats_num_record = models.PositiveIntegerField(default=0)
    stats_num_occurrence = models.PositiveIntegerField(default=0)
    #stats_num_year_column = models.PositiveIntegerField(default=0)
    #stats_num_coordinates = models.PositiveIntegerField(default=0)
    stats_extensions = JSONField()
    is_most_project = models.BooleanField('是否為科技部計畫', default=False)
    #is_about_taiwan = models.BooleanField('是否 about Taiwan', default=True)
    #is_from_taiwan = models.BooleanField('是否 from Taiwan', default=True)

    @property
    def dwc_core_type_human(self):
        if 'Occurrence' in self.dwc_core_type:
            return '出現記錄 (Occurrence)'
        elif 'Taxon' in self.dwc_core_type:
            return '物種名錄 (Checklist)'
        elif 'Event' in self.dwc_core_type:
            return '調查活動 (Sampling Event)'

    @property
    def link(self):
        return 'http://ipt.taibif.tw/resource?r={}'.format(self.name)

    @property
    def eml(self):
        return 'http://ipt.taibif.tw/eml.do?r={}'.format(self.name)

    @property
    def dwca(self):
        return 'http://ipt.taibif.tw/archive.do?r={}'.format(self.name)

    def __str__(self):
        r = '<DataSet {}>'.format(self.name)
        return r

class TaxonTree(models.Model):
    name = models.CharField('name', max_length=64)
    rank_map = models.CharField('rank map', max_length=256)

    def __str__(self):
        r = '{}'.format(self.name)
        return r

class Taxon(models.Model):
    TAXON_RANK_LIST = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']

    rank = models.CharField('rank', max_length=32)
    name = models.CharField('name', max_length=128)
    name_zh = models.CharField('name_zh', max_length=128)
    count = models.PositiveIntegerField('count', default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    tree = models.ForeignKey(TaxonTree, on_delete=models.CASCADE, null=True)

    def __str__(self):
        r = '{}: {}'.format(self.rank, self.get_name())
        return r

    def get_name(self):
        if self.name_zh:
            return '{} {}'.format(self.name_zh, self.name)
        else:
            return '{}'.format(self.name)

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
        ordering = ['name']

OCCUR_COLUMN_MAP = {'occurrenceID': 'occurrence_id', 'occurrenceRemarks': 'occurrence_remarks', 'occurrenceStatus': 'occurrence_status', 'institutionID': 'institution_id', 'institutionCode': 'institution_code', 'ownerInstitutionCode': 'owner_institution_code', 'collectionID': 'collection_id', 'collectionCode': 'collection_code', 'catalogNumber': 'catalog_number', 'otherCatalogNumbers': 'other_catalog_numbers', 'recordNumber': 'record_number', 'recordedBy': 'recorded_by', 'fieldNumber': 'field_number', 'fieldNotes': 'field_notes', 'basisOfRecord': 'basis_of_record', 'datasetID': 'dataset_id', 'datasetName': 'dataset_name', 'language': 'language', 'type': 'type_field', 'typeStatus': 'type_status', 'coreid': 'coreid', 'lifeStage': 'life_stage', 'eventTime': 'event_time', 'eventRemarks': 'event_remarks', 'year': 'year', 'month': 'month', 'day': 'day', 'startDayOfYear': 'start_day_of_year', 'endDayOfYear': 'end_day_of_year', 'eventDate': 'event_date', 'eventID': 'event_id', 'verbatimEventDate': 'verbatim_event_date', 'verbatimDepth': 'verbatim_depth', 'kingdom': 'kingdom', 'phylum': 'phylum', 'class': 'class_field', 'order': 'order_field', 'family': 'family', 'genus': 'genus', 'subgenus': 'subgenus', 'vernacularName': 'vernacular_name', 'scientificName': 'scientific_name', 'scientificNameID': 'scientific_name_id', 'taxonRank': 'taxon_rank', 'taxonID': 'taxon_id', 'verbatimTaxonRank': 'verbatim_taxon_rank', 'associatedTaxa': 'associated_taxa', 'specificEpithet': 'specific_epithet', 'scientificNameAuthorship': 'scientific_name_authorship', 'acceptedNameUsage': 'accepted_name_usage', 'acceptedNameUsageID': 'accepted_name_usage_id', 'originalNameUsage': 'original_name_usage', 'nameAccordingTo': 'name_according_to', 'higherClassification': 'higher_classification', 'taxonRemarks': 'taxon_remarks', 'dateIdentified': 'date_identified', 'identificationQualifier': 'identification_qualifier', 'identifiedBy': 'identified_by', 'identificationVerificationStatus': 'identification_verification_status', 'previousIdentifications': 'previous_identifications', 'county': 'county', 'country': 'country', 'countryCode': 'country_code', 'stateProvince': 'state_province', 'locality': 'locality', 'locationID': 'location_id', 'higherGeography': 'higher_geography', 'georeferencedDate': 'georeferenced_date', 'georeferenceSources': 'georeference_sources', 'georeferencedBy': 'georeferenced_by', 'geodeticDatum': 'geodetic_datum', 'georeferenceProtocol': 'georeference_protocol', 'georeferenceRemarks': 'georeference_remarks', 'georeferenceVerificationStatus': 'georeference_verification_status', 'decimalLongitude': 'decimal_longitude', 'decimalLatitude': 'decimal_latitude', 'verbatimLatitude': 'verbatim_latitude', 'verbatimLongitude': 'verbatim_longitude', 'verbatimLocality': 'verbatim_locality', 'verbatimCoordinates': 'verbatim_coordinates', 'coordinateUncertaintyInMeters': 'coordinate_uncertainty_in_meters', 'verbatimCoordinateSystem': 'verbatim_coordinate_system', 'coordinatePrecision': 'coordinate_precision', 'locationAccordingTo': 'location_according_to', 'pointRadiusSpatialFit': 'point_radius_spatial_fit', 'rights': 'rights', 'rightsHolder': 'rights_holder', 'license': 'license_field', 'preparations': 'preparations', 'id': 'id_field', 'modified': 'modified', 'dataGeneralizations': 'data_generalizations', 'organismID': 'organism_id', 'organismQuantityType': 'organism_quantity_type', 'organismQuantity': 'organism_quantity', 'sex': 'sex', 'individualCount': 'individual_count', 'verbatimElevation': 'verbatim_elevation', 'minimumElevationInMeters': 'minimum_elevation_in_meters', 'maximumElevationInMeters': 'maximum_elevation_in_meters', 'minimumDepthInMeters': 'minimum_depth_in_meters', 'maximumDepthInMeters': 'maximum_depth_in_meters', 'waterBody': 'water_body', 'island': 'island', 'habitat': 'habitat', 'reproductiveCondition': 'reproductive_condition', 'continent': 'continent', 'infraspecificEpithet': 'infraspecific_epithet', 'footprintWKT': 'footprint_wkt', 'associatedMedia': 'associated_media', 'associatedSequences': 'associated_sequences', 'associatedReferences': 'associated_references', 'nomenclaturalCode': 'nomenclatural_code', 'footprintSpatialFit': 'footprint_spatial_fit', 'establishmentMeans': 'establishment_means', 'behavior': 'behavior', 'informationWithheld': 'information_withheld', 'islandGroup': 'island_group', 'municipality': 'municipality', 'materialSampleID': 'material_sample_id', 'samplingProtocol': 'sampling_protocol', 'samplingEffort': 'sampling_effort', 'disposition': 'disposition', 'references': 'references', 'namePublishedInYear': 'name_published_in_year', 'namePublishedIn': 'name_published_in', 'dataset_name': 'dataset_name'}
        
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
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
        dataset = get_object_or_404(DataSet, name=self.dataset_name)
        return dataset

    @property
    def display_terms(self):
        dict_values = vars(self)
        terms_map = dict((v,k) for k,v in OCCUR_COLUMN_MAP.items())
        ret = {}
        for k,v in dict_values.items():
            if k in terms_map:
                ret[terms_map[k]] = v or ''
        return ret

    class Meta:
        managed = False
        db_table = 'data_occurrence'
