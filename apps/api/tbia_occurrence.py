"""Read-only TBIA occurrence exchange backed by the existing public Solr index."""
import json
import logging
import math
import re
import uuid
from datetime import datetime, timedelta

import requests
from django.db import DatabaseError

from apps.data.models import DATA_MAPPING, Dataset
from utils.map_data import convert_x_coor_to_grid, convert_y_coor_to_grid
from .tbia import license_value, response, text, timestamp

logger = logging.getLogger(__name__)
SOLR_SELECT = 'http://solr:8983/solr/taibif_occurrence/select'
PARAMETERS = {
    'occurrenceID', 'catalogNumber', 'datasetID', 'modified', 'limit', 'offset',
    'originalOccurrenceID', 'basisOfRecord',
    'scientificName', 'taibifScientificName', 'taxonRank', 'kingdom', 'phylum',
    'class', 'order', 'family', 'genus', 'establishmentMeans',
    'occurrenceStatus', 'eventDate', 'year', 'month', 'taibifModifiedDate',
    'boundedBy', 'coordinateUncertaintyInMeters', 'country', 'county',
    'datasetName', 'taibifDatasetID', 'gbifDatasetID', 'selfProduced', 'license',
}

# Fields with an established public mapping. Do not fall back to raw coordinates.
STRING_FIELDS = {
    'catalogNumber': 'catalogNumber',
    'gbifID': 'gbifID',
    'establishmentMeans': 'taibif_establishmentMeans',
    'occurrenceStatus': 'taibif_occurrenceStatus',
    'eventDate': 'taibif_eventDate',
    'country': 'taibif_country',
    'habitatReserve': 'forest_reserves',
    'wildlifeReserve': 'wildlife_refuges',
    'datasetShortName': 'taibif_dataset_name',
    'gbifDatasetID': 'gbif_datasetKey',
    'issue': 'taibif_issue',
    'recordNumber': 'taibif_recordNumber',
    'recordedBy': 'taibif_recordedBy',
    'associatedMedia': 'taibif_mediaReferences',
    'organismQuantityType': 'organismQuantityType',
    'typeStatus': 'taibif_typeStatus',
    'locality': 'taibif_locality',
    'verbatimSRS': 'taibif_crs',
    'geodeticDatum': 'taibif_geodeticDatum',
    'dataGeneralizations': 'dataGeneralizations',
    'countryCode': 'taibif_countryCode',
    'county': 'taibif_county',
    'verbatimScientificName': 'scientificName',
    'scientificName': 'taibif_scientificName',
    'vernacularName': 'taibif_vernacularName',
    'nameAccordingTo': 'taibif_taxonBackbone',
    'taxonGroup': 'taibif_taxonGroup',
    'kingdom': 'taibif_kingdom',
    'phylum': 'taibif_phylum',
    'class': 'taibif_class',
    'order': 'taibif_order',
    'family': 'taibif_family',
    'genus': 'taibif_genus',
    'scientificNameID': 'taibif_accepted_namecode',
}

BASIS = {
    '保存標本': 'PreservedSpecimen', '化石標本': 'FossilSpecimen',
    '活體標本': 'LivingSpecimen', '材料樣本': 'MaterialSample', '組織樣本': 'MaterialSample',
    '人為觀測': 'HumanObservation', '機器觀測': 'MachineObservation',
    '調查活動': 'Event', '名錄/分類群': 'Taxon', '出現紀錄': 'Occurrence',
    '材料實體': 'MaterialEntity',
}
BASIS_VALUES = set(BASIS.values()) | {'MaterialCitation'}
RANKS = {name.lower(): name for name in (
    'Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus',
    'Species', 'Subspecies', 'Variety', 'Form',
)}
SOLR_FIELDS = sorted(set(STRING_FIELDS.values()) | {
    'id', 'taibif_occ_id', 'occurrenceID', 'taibif_datasetKey',
    'taibif_lastInterpreted', 'selfProduced', 'taibif_license', 'basisOfRecord',
    'taibif_basisOfRecord', 'taibif_taxonRank',
    'taibif_mediaLicense', 'organismQuantity',
    'taibif_coordinatePrecision', 'taibif_coordinateUncertaintyInMeters', 'taibif_decimalLatitude',
    'taibif_decimalLongitude', 'taibif_year', 'taibif_month', 'taibif_day',
})


class InvalidSolrResponse(Exception):
    pass


def scalar(value):
    if isinstance(value, list):
        return value[0] if len(value) == 1 else None
    return value


def string(value):
    if isinstance(value, list):
        values = [string(item) for item in value]
        return ' | '.join(item for item in values if item is not None) or None
    if value is None:
        return None
    result = text(str(value))
    if result and result.casefold() in {'na', 'n/a', 'nan'}:
        return None
    return result


def number(value, integer=False):
    value = scalar(value)
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
        if not math.isfinite(result) or result in {-99999, -9999999}:
            return None
        if integer:
            return int(result) if result.is_integer() else None
        return result
    except (ValueError, TypeError, OverflowError):
        return None


def date_value(value):
    value = string(scalar(value))
    if value is None:
        return None
    try:
        if re.fullmatch(r'\d{8}', value):
            return datetime.strptime(value, '%Y%m%d').strftime('%Y%m%d')
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return timestamp(parsed)
    except ValueError:
        return None


def normalized_license(value):
    value = string(scalar(value))
    # Recognize the known alternate human-readable CC descriptions, too.
    aliases = {
        'Creative Commons Attribution (CC-BY 4.0) License': 'CC-BY',
        'Creative Commons Attribution Non Commercial (CC-BY-NC 4.0) License': 'CC-BY-NC',
    }
    return aliases.get(value) or license_value(value)


def basis_value(doc):
    for field in ('taibif_basisOfRecord', 'basisOfRecord'):
        value = string(scalar(doc.get(field)))
        if value in BASIS_VALUES:
            return value
        if value in BASIS:
            return BASIS[value]
    return None


def serialize_occurrence(doc, dataset):
    result = {key: string(doc.get(field)) for key, field in STRING_FIELDS.items()}
    produced = scalar(doc.get('selfProduced'))
    result.update({
        'occurrenceID': string(doc.get('taibif_occ_id')),
        'originalOccurrenceID': string(doc.get('occurrenceID')),
        'datasetID': str(dataset['taibif_dataset_id']),
        'datasetName': text(dataset['title']),
        'resourceCitationIdentifier': (
            f"https://www.gbif.org/dataset/{text(dataset['guid'])}" if text(dataset['guid']) else None
        ),
        'modified': date_value(doc.get('taibif_lastInterpreted')),
        'selfProduced': produced if isinstance(produced, bool) else None,
        'license': normalized_license(doc.get('taibif_license')),
        'mediaLicense': normalized_license(doc.get('taibif_mediaLicense')),
        'basisOfRecord': basis_value(doc),
        'taxonRank': RANKS.get((string(scalar(doc.get('taibif_taxonRank'))) or '').lower()),
    })
    for output, field, integer in (
        ('coordinatePrecision', 'taibif_coordinatePrecision', False),
        ('organismQuantity', 'organismQuantity', False),
        ('coordinateUncertaintyInMeters', 'taibif_coordinateUncertaintyInMeters', False),
        ('decimalLatitude', 'taibif_decimalLatitude', False),
        ('decimalLongitude', 'taibif_decimalLongitude', False),
        ('year', 'taibif_year', True), ('month', 'taibif_month', True), ('day', 'taibif_day', True),
    ):
        result[output] = number(doc.get(field), integer=integer)
    county = result['county']
    result['county'] = COUNTIES.get(county, county if county in COUNTIES.values() else None)
    return result


def pagination(params):
    for key, default in (('limit', '100'), ('offset', '0')):
        if not re.fullmatch(r'[0-9]+', params.get(key, default)):
            raise ValueError(f'{key} must be an integer.')
    limit = min(int(params.get('limit', 100)), 1000)
    if limit < 1:
        raise ValueError('limit must be greater than zero.')
    return limit, int(params.get('offset', 0))


def modified_filter(value):
    parts = value.split(',')
    if len(parts) not in (1, 2) or any(not re.fullmatch(r'[0-9]{8}', part) for part in parts):
        raise ValueError('modified must use YYYYMMDD or YYYYMMDD,YYYYMMDD.')
    try:
        dates = [datetime.strptime(part, '%Y%m%d').date() for part in parts]
        if dates[0] > dates[-1]:
            raise ValueError
        end = dates[-1] + timedelta(days=1)
    except (ValueError, OverflowError):
        raise ValueError('Invalid modified date range.')
    # This existing Solr string field stores Taiwan calendar dates as YYYY-MM-DD.
    return f'taibif_lastInterpreted:[{dates[0].isoformat()} TO {end.isoformat()}' + '}'


def literal_filter(field, value):
    # Exact indexed term: user input is a parameter, never Solr query syntax.
    return f'{{!term f={field} v=$filter_{field}}}', (f'filter_{field}', value)


COUNTIES = dict(zip(
    ('Keelung City', 'New Taipei City', 'Taipei City', 'Taoyuan City', 'Hsinchu County',
     'Hsinchu City', 'Miaoli County', 'Taichung City', 'Changhua County', 'Nantou County',
     'Yunlin County', 'Chiayi County', 'Chiayi City', 'Tainan City', 'Kaohsiung City',
     'Pingtung County', 'Yilan County', 'Hualien County', 'Taitung County', 'Penghu County',
     'Kinmen County', 'Lienchiang County'),
    ('基隆市', '新北市', '臺北市', '桃園市', '新竹縣', '新竹市', '苗栗縣', '臺中市',
     '彰化縣', '南投縣', '雲林縣', '嘉義縣', '嘉義市', '臺南市', '高雄市', '屏東縣',
     '宜蘭縣', '花蓮縣', '臺東縣', '澎湖縣', '金門縣', '連江縣'),
))
VOCABULARIES = {
    'kingdom': {'Animalia', 'Archaea', 'Bacteria', 'Chromista', 'Fungi', 'Plantae', 'Protozoa', 'Viruses'},
    'establishmentMeans': {'原生', '原生：再引進', '引進（外來、非原生、非原住）',
                           '引進（協助拓殖）', '流浪的', '不確定的（未知、隱源性）'},
    'occurrenceStatus': {'出現', '未出現'},
}


def any_terms(fields, values):
    # JSON quoting escapes Solr quoted-term metacharacters; no query syntax is accepted.
    return '(' + ' OR '.join(f'{field}:{json.dumps(value, ensure_ascii=False)}'
                             for field in fields for value in values) + ')'


def legacy_date_filter(value, field):
    parts = value.split(',')
    if len(parts) not in (1, 2) or any(not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', part) for part in parts):
        raise ValueError(f'{field} must use YYYY-MM-DD or YYYY-MM-DD,YYYY-MM-DD.')
    try:
        dates = [datetime.strptime(part, '%Y-%m-%d').date() for part in parts]
        if dates[0] > dates[-1]:
            raise ValueError
    except ValueError:
        raise ValueError(f'Invalid {field} date range.')
    end = dates[-1].isoformat() if len(dates) == 2 else '*'
    return f'{field}:[{dates[0].isoformat()} TO {end}]'


def legacy_filters(params):
    filters, extra = [], {}
    for parameter, field in {
        'originalOccurrenceID': 'occurrenceID',
        'scientificName': 'taibif_scientificName', 'taibifScientificName': 'taibif_scientificName',
        'kingdom': 'taibif_kingdom', 'phylum': 'taibif_phylum', 'class': 'taibif_class',
        'order': 'taibif_order', 'family': 'taibif_family', 'genus': 'taibif_genus',
        'establishmentMeans': 'taibif_establishmentMeans',
        'occurrenceStatus': 'taibif_occurrenceStatus', 'country': 'taibif_country',
        'gbifDatasetID': 'gbif_datasetKey',
    }.items():
        if parameter not in params:
            continue
        value = params[parameter]
        if not value.strip():
            raise ValueError(f'{parameter} must not be empty.')
        if parameter in VOCABULARIES and value not in VOCABULARIES[parameter]:
            raise ValueError(f'Invalid {parameter} controlled vocabulary.')
        key = f'legacy_{parameter}'
        filters.append(f'{{!term f={field} v=${key}}}')
        extra[key] = value
    if 'basisOfRecord' in params:
        value = params['basisOfRecord']
        if value not in BASIS_VALUES:
            raise ValueError('Invalid basisOfRecord controlled vocabulary.')
        canonical = BASIS.get(value, value)
        equivalent = {canonical, value} | {key for key, mapped in BASIS.items() if mapped == canonical}
        normalized = any_terms(('taibif_basisOfRecord',), sorted(equivalent))
        # Match the serializer: prefer a recognized interpreted value over the raw value.
        recognized = any_terms(('taibif_basisOfRecord',), sorted(BASIS_VALUES | set(BASIS)))
        raw = any_terms(('basisOfRecord',), sorted(equivalent))
        filters.append(f'({normalized} OR (-{recognized} AND {raw}))')
    if 'taxonRank' in params:
        canonical = params['taxonRank']
        if canonical not in RANKS.values():
            raise ValueError('Invalid taxonRank controlled vocabulary.')
        filters.append(any_terms(('taibif_taxonRank',), [canonical, canonical.lower()]))
    for parameter, field in [('eventDate', 'taibif_eventDate'), ('taibifModifiedDate', 'taibif_lastInterpreted')]:
        if parameter in params:
            filters.append(legacy_date_filter(params[parameter], field))
    for parameter, field, minimum, maximum in [
        ('year', 'taibif_year', 1700, datetime.now().year), ('month', 'taibif_month', 1, 12),
    ]:
        if parameter not in params:
            continue
        parts = params[parameter].split(',')
        if len(parts) not in (1, 2) or any(not re.fullmatch(r'[0-9]+', part) for part in parts):
            raise ValueError(f'Invalid {parameter} integer range.')
        values = [int(part) for part in parts]
        if any(not minimum <= value <= maximum for value in values) or values[0] > values[-1]:
            raise ValueError(f'{parameter} must range from {minimum} to {maximum}.')
        end = str(values[-1]) if len(values) == 2 else '*'
        filters.append(f'{field}:[{values[0]} TO {end}]')
    if 'county' in params:
        counties = [value.strip() for value in params['county'].split(',')]
        inverse = {value: key for key, value in COUNTIES.items()}
        if any(value not in inverse for value in counties):
            raise ValueError('Invalid county controlled vocabulary.')
        values = set()
        for value in counties:
            english = inverse[value]
            values.update((english, COUNTIES[english]))
        filters.append(any_terms(('taibif_county',), sorted(values)))
    if 'coordinateUncertaintyInMeters' in params:
        value = number(params['coordinateUncertaintyInMeters'])
        if value is None or value < 0:
            raise ValueError('coordinateUncertaintyInMeters must be a non-negative finite number.')
        filters.append(f'taibif_coordinateUncertaintyInMeters:[0 TO {value}]')
    if 'selfProduced' in params:
        value = params['selfProduced'].lower()
        if value not in ('true', 'false'):
            raise ValueError('selfProduced must be true or false.')
        filters.append(f'selfProduced:{value}')
    if 'license' in params:
        value = params['license']
        if value not in {'CC0', 'CC-BY', 'CC-BY-NC', 'NA'}:
            raise ValueError('Invalid license controlled vocabulary.')
        if value == 'NA':
            values = {'unknown'}
        else:
            values = {value} | {key for key, mapped in DATA_MAPPING['rights'].items() if mapped == value and key}
            path = {'CC0': 'publicdomain/zero/1.0', 'CC-BY': 'licenses/by/4.0', 'CC-BY-NC': 'licenses/by-nc/4.0'}[value]
            values.update(f'{scheme}://creativecommons.org/{path}{suffix}' for scheme in ('http', 'https')
                          for suffix in ('/', '/legalcode', '/legalcode/'))
            if value == 'CC-BY':
                values.add('Creative Commons Attribution (CC-BY 4.0) License')
            if value == 'CC-BY-NC':
                values.add('Creative Commons Attribution Non Commercial (CC-BY-NC 4.0) License')
        filters.append(any_terms(('taibif_license',), sorted(values)))
    if 'boundedBy' in params:
        parts = params['boundedBy'].split(',')
        if len(parts) != 4:
            raise ValueError('boundedBy requires minLongitude,minLatitude,maxLongitude,maxLatitude.')
        values = [number(value) for value in parts]
        if any(value is None for value in values):
            raise ValueError('boundedBy requires finite coordinates.')
        west, south, east, north = values
        if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
            raise ValueError('Invalid boundedBy coordinate range.')
        filters.extend((
            f'{{!frange l={convert_x_coor_to_grid(west)} u={convert_x_coor_to_grid(east)}}}grid_x',
            f'{{!frange l={convert_y_coor_to_grid(south)} u={convert_y_coor_to_grid(north)}}}grid_y',
        ))
    return filters, extra


def occurrence_api(request):
    if request.method != 'GET':
        result = response(request, 405, 'Only GET is supported.')
        result['Allow'] = 'GET'
        return result
    limit = None
    try:
        params = request.GET
        if set(params) - PARAMETERS:
            raise ValueError('Unknown query parameter.')
        if any(len(params.getlist(key)) != 1 for key in params):
            raise ValueError('Repeated query parameters are not supported.')
        limit, offset = pagination(params)
        dataset_query = Dataset.public_objects.all()
        if 'datasetID' in params:
            try:
                dataset_id = uuid.UUID(params['datasetID'])
            except ValueError:
                raise ValueError('datasetID must be a valid UUID.')
            dataset_query = dataset_query.filter(taibif_dataset_id=dataset_id)
        if 'taibifDatasetID' in params:
            try:
                legacy_dataset_id = uuid.UUID(params['taibifDatasetID'])
            except ValueError:
                raise ValueError('taibifDatasetID must be a valid UUID.')
            dataset_query = dataset_query.filter(taibif_dataset_id=legacy_dataset_id)
        if 'datasetName' in params:
            name = params['datasetName']
            if not name.strip():
                raise ValueError('datasetName must not be empty.')
            dataset_query = dataset_query.filter(title=name)
        filters, extra = legacy_filters(params)
        for parameter, field in (('occurrenceID', 'taibif_occ_id'), ('catalogNumber', 'catalogNumber')):
            if parameter in params:
                value = params[parameter]
                if not value.strip():
                    raise ValueError(f'{parameter} must not be empty.')
                condition, (key, term) = literal_filter(field, value)
                filters.append(condition)
                extra[key] = term
        if 'modified' in params:
            filters.append(modified_filter(params['modified']))
        datasets = {str(row['taibif_dataset_id']): row for row in dataset_query.values(
            'taibif_dataset_id', 'title', 'guid')}
        if not datasets:
            return response(request, 200, 'Success', total=0, limit=limit)
        filters.insert(0, '{!terms f=taibif_datasetKey}' + ','.join(datasets))
        solr_params = {
            'q': '*:*', 'fq': filters, 'rows': limit, 'start': offset,
            'sort': 'taibif_occ_id asc,id asc', 'fl': ','.join(SOLR_FIELDS), 'wt': 'json',
            'omitHeader': 'false', **extra,
        }
        # POST avoids URL-length limits on the public-dataset allowlist.
        upstream = requests.post(SOLR_SELECT, data=solr_params, timeout=(5, 30))
        upstream.raise_for_status()
        body = upstream.json()
        if not isinstance(body, dict):
            raise InvalidSolrResponse
        header = body.get('responseHeader', {})
        payload = body.get('response')
        if (not isinstance(header, dict) or header.get('status', 0) != 0
                or header.get('partialResults') in (True, 'true')
                or not isinstance(payload, dict)):
            raise InvalidSolrResponse
        total, docs = payload.get('numFound'), payload.get('docs')
        if (type(total) is not int or total < 0 or not isinstance(docs, list)
                or payload.get('numFoundExact') is False
                or len(docs) != min(limit, max(0, total - offset))):
            raise InvalidSolrResponse
        if 'occurrenceID' in params and total > 1:
            # A single-record endpoint must not silently pick one of conflicting records.
            return response(request, 500, 'Duplicate occurrenceID in source data.', limit=limit)
        data = []
        for doc in docs:
            if not isinstance(doc, dict) or doc.get('taibif_datasetKey') not in datasets:
                raise InvalidSolrResponse
            data.append(serialize_occurrence(doc, datasets[doc['taibif_datasetKey']]))
        next_url = None
        if offset + limit < total:
            following = params.copy()
            following['limit'] = str(limit)
            following['offset'] = str(offset + limit)
            next_url = request.build_absolute_uri(request.path) + '?' + following.urlencode()
        return response(request, 200, 'Success', data, total, limit, next_url)
    except ValueError as exc:
        # JSON decoding errors from the upstream are not client parameter errors.
        if isinstance(exc, requests.exceptions.JSONDecodeError):
            logger.exception('TBIA occurrence upstream returned invalid JSON')
            return response(request, 500, 'Internal server error.', limit=limit)
        return response(request, 400, str(exc), limit=limit)
    except (DatabaseError, requests.RequestException, InvalidSolrResponse):
        logger.exception('TBIA occurrence query failed')
        return response(request, 500, 'Internal server error.', limit=limit)
