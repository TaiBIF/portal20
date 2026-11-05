"""Link validation and preview URLs for online workshop materials."""
import re
from urllib.parse import parse_qs, urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


validate_web_url = URLValidator(schemes=['http', 'https'])


def validate_material_link(value):
    if value.startswith('/') and not value.startswith('//') and '\\' not in value:
        return
    validate_web_url(value)


def preview_url(value):
    if not value:
        return ''
    try:
        validate_material_link(value)
    except ValidationError:
        return ''
    parts = urlsplit(value)
    host = (parts.hostname or '').lower()
    path = parts.path
    if host in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'):
        if host == 'youtu.be':
            video_id = path.strip('/').split('/')[0]
        elif path == '/watch':
            video_id = parse_qs(parts.query).get('v', [''])[0]
        else:
            match = re.fullmatch(r'/(?:embed|shorts|live)/([\w-]+)', path)
            video_id = match.group(1) if match else ''
        if re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
            return 'https://www.youtube.com/embed/' + video_id
        return ''
    if host == 'drive.google.com':
        match = re.match(r'^/file/d/([A-Za-z0-9_-]+)(?:/|$)', path)
        file_id = match.group(1) if match else parse_qs(parts.query).get('id', [''])[0]
        if re.fullmatch(r'[A-Za-z0-9_-]+', file_id):
            return 'https://drive.google.com/file/d/' + file_id + '/preview'
        return ''
    return value
