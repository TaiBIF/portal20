"""TBIA dataset exchange API, independent of the public v3 contract."""
import logging
import re
import uuid
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.http import JsonResponse
from django.db import DatabaseError
from django.db.models import Q
from apps.data.models import DATA_MAPPING, Dataset

logger = logging.getLogger(__name__)
TAIPEI = ZoneInfo('Asia/Taipei')
PARAMETERS = {
    'datasetID', 'datasetName', 'gbifDatasetID', 'datasetPublisher',
    'datasetPublisherID', 'core', 'source', 'datasetLicense',
    'created', 'modified', 'limit', 'offset',
}
MULTI_PARAMETERS = {'source', 'datasetLicense'}


def response(request, code, message, data=None, total=0, limit=None, next_url=None):
    result = JsonResponse({
        'status': {'code': code, 'message': message},
        'meta': {'total': total, 'limit': limit},
        'links': {'self': request.build_absolute_uri(), 'next': next_url},
        'data': data if data is not None else [],
    }, status=code, content_type='application/json; charset=utf-8')
    return result


def text(value):
    if isinstance(value, str):
        return value.strip() or None
    return value


def timestamp(value):
    if value is None:
        return None
    # Legacy naive values follow the project's Asia/Taipei default timezone.
    if value.tzinfo is None:
        value = value.replace(tzinfo=TAIPEI)
    return value.astimezone(TAIPEI).strftime('%Y%m%d')


def license_value(value):
    value = text(value)
    allowed = {'CC0', 'CC-BY', 'CC-BY-NC', '政府資料開放授權條款'}
    if value in allowed:
        return value
    mapped = DATA_MAPPING['rights'].get(value)
    if mapped in allowed:
        return mapped
    if value:
        match = re.fullmatch(r'https?://creativecommons\.org/(publicdomain/zero/1\.0|licenses/(by|by-nc)/4\.0)/(?:legalcode/?)?', value)
        if match:
            return {'by': 'CC-BY', 'by-nc': 'CC-BY-NC'}.get(match.group(2), 'CC0')
        if value.rstrip('/') == 'https://data.gov.tw/license':
            return '政府資料開放授權條款'
    return None


def serialize_dataset(dataset, request):
    return {
        'datasetName': text(dataset.title),
        'datasetID': str(dataset.taibif_dataset_id),
        'gbifDatasetID': text(dataset.guid),
        'occurrenceCount': dataset.num_record,
        'resourceCitationIdentifier': (
            f'https://www.gbif.org/dataset/{text(dataset.guid)}'
            if text(dataset.guid) else None
        ),
        'datasetPublisher': text(dataset.organization_name),
        'datasetPublisherID': text(dataset.organization_uuid),
        'core': text(dataset.dwc_core_type).upper() if text(dataset.dwc_core_type) else None,
        'source': text(dataset.source),
        'datasetLicense': license_value(dataset.data_license),
        'created': timestamp(dataset.created),
        'modified': timestamp(dataset.mod_date),
    }


def dataset_api(request):
    if request.method != 'GET':
        result = response(request, 405, 'Only GET is supported.')
        result['Allow'] = 'GET'
        return result
    limit = None
    try:
        params = request.GET
        if set(params) - PARAMETERS:
            raise ValueError('Unknown query parameter.')
        if any(len(params.getlist(key)) != 1 for key in params if key not in MULTI_PARAMETERS):
            raise ValueError('Repeated query parameters are not supported.')
        for key, default in [('limit', '100'), ('offset', '0')]:
            if not re.fullmatch(r'[0-9]+', params.get(key, default)):
                raise ValueError(f'{key} must be an integer.')
        limit = min(int(params.get('limit', 100)), 1000)
        offset = int(params.get('offset', 0))
        if limit < 1:
            raise ValueError('limit must be greater than zero.')
        query = Dataset.public_objects.all()
        if 'datasetID' in params:
            try:
                dataset_id = uuid.UUID(params['datasetID'])
            except ValueError:
                raise ValueError('datasetID must be a valid UUID.')
            query = query.filter(taibif_dataset_id=dataset_id)
        if 'datasetName' in params:
            name = params['datasetName'].strip()
            if not name:
                raise ValueError('datasetName must not be empty.')
            query = query.filter(title__contains=name)
        for parameter, field, lookup in [
            ('gbifDatasetID', 'guid', 'exact'),
            ('datasetPublisher', 'organization_name', 'contains'),
            ('datasetPublisherID', 'organization_uuid', 'exact'),
            ('core', 'dwc_core_type', 'exact'),
        ]:
            if parameter in params:
                value = params[parameter]
                if not value.strip():
                    raise ValueError(f'{parameter} must not be empty.')
                if parameter == 'core' and value not in {'SAMPLINGEVENT', 'OCCURRENCE', 'CHECKLIST', 'METADATA'}:
                    raise ValueError('Invalid core controlled vocabulary.')
                query = query.filter(**{f'{field}__{lookup}': value})
        if 'source' in params:
            sources = params.getlist('source')
            if any(value not in {'TaiBIF IPT', 'GBIF'} for value in sources):
                raise ValueError('source must be TaiBIF IPT or GBIF.')
            query = query.filter(source__in=sources)
        if 'datasetLicense' in params:
            licenses = params.getlist('datasetLicense')
            if any(value not in {'CC0', 'CC-BY', 'CC-BY-NC', 'NA'} for value in licenses):
                raise ValueError('Invalid datasetLicense controlled vocabulary.')
            # Preserve v3 filtering against stored license descriptions; NA matches unknown.
            stored = [key for key, value in DATA_MAPPING['rights'].items()
                      if value in licenses and key is not None]
            license_filter = Q(data_license__in=stored)
            if 'NA' in licenses:
                license_filter |= Q(data_license__contains='unknown')
            query = query.filter(license_filter)
        for parameter, field in [('created', 'created'), ('modified', 'mod_date')]:
            if parameter not in params:
                continue
            parts = params[parameter].split(',')
            if len(parts) not in (1, 2) or any(not re.fullmatch(r'[0-9]{8}', part) for part in parts):
                raise ValueError(f'{parameter} must use YYYYMMDD or YYYYMMDD,YYYYMMDD.')
            try:
                dates = [datetime.strptime(part, '%Y%m%d').date() for part in parts]
                start, end = dates[0], dates[-1]
                if start > end:
                    raise ValueError
                lower = datetime.combine(start, time.min, tzinfo=TAIPEI)
                upper = datetime.combine(end + timedelta(days=1), time.min, tzinfo=TAIPEI)
            except (ValueError, OverflowError):
                raise ValueError(f'Invalid {parameter} date range.')
            query = query.filter(**{f'{field}__gte': lower, f'{field}__lt': upper})
        total = query.count()
        datasets = list(query.order_by('taibif_dataset_id')[offset:offset + limit])
        next_url = None
        if offset + limit < total:
            following = params.copy()
            following['limit'] = str(limit)
            following['offset'] = str(offset + limit)
            next_url = request.build_absolute_uri(request.path) + '?' + following.urlencode()
        return response(request, 200, 'Success',
                        [serialize_dataset(item, request) for item in datasets],
                        total, limit, next_url)
    except ValueError as exc:
        return response(request, 400, str(exc), limit=limit)
    except DatabaseError:
        logger.exception('TBIA dataset database query failed')
        return response(request, 500, 'Internal server error.', limit=limit)
