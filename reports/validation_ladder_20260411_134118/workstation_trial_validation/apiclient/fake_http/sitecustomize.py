import io
import json
import os
from urllib.parse import parse_qs, urlparse
import urllib.request as _urllib_request

_FAKE_LOG = os.getenv('WORKSTATION_APICLIENT_FAKE_LOG', '')
_POLL_COUNTS = {}
_ORIGINAL_URLOPEN = _urllib_request.urlopen


def _append_log(message):
    if not _FAKE_LOG:
        return
    with open(_FAKE_LOG, 'a', encoding='utf-8') as handle:
        handle.write(str(message) + '\n')


class _FakeHTTPResponse:
    def __init__(self, body, *, status=200, headers=None):
        self._body = body if isinstance(body, bytes) else str(body).encode('utf-8')
        self.status = int(status)
        self.code = int(status)
        self.headers = headers or {}

    def read(self, *args, **kwargs):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _request_components(request_or_url, data=None):
    if hasattr(request_or_url, 'full_url'):
        request = request_or_url
        url = request.full_url
        method = getattr(request, 'method', None) or request.get_method()
        headers = dict(getattr(request, 'headers', {}) or {})
        body = getattr(request, 'data', None)
    else:
        url = str(request_or_url)
        method = 'POST' if data is not None else 'GET'
        headers = {}
        body = data
    if isinstance(body, bytes):
        body_text = body.decode('utf-8')
    elif body is None:
        body_text = ''
    else:
        body_text = str(body)
    return url, str(method).upper(), headers, body_text


def _json_response(payload, *, status=200):
    return _FakeHTTPResponse(json.dumps(payload), status=status, headers={'Content-Type': 'application/json'})


def _handle_fake_http(request_or_url, data=None):
    url, method, headers, body_text = _request_components(request_or_url, data=data)
    parsed = urlparse(url)
    host = parsed.netloc.casefold()
    path = parsed.path
    query = parse_qs(parsed.query)
    _append_log(f'{method} {url}')
    if host == 'api.example.com':
        if path == '/items/42' and method == 'GET':
            return _json_response({'id': 42, 'name': 'widget-42'})
        if path == '/search' and method == 'GET':
            return _json_response({'items': ['widget-a', 'widget-b'], 'query': {k: v[-1] for k, v in query.items()}})
        if path == '/users' and method == 'POST':
            return _json_response({'status': 'created', 'payload': json.loads(body_text or '{}')}, status=201)
        if path == '/users/42' and method in {'PUT', 'PATCH'}:
            return _json_response({'status': 'updated', 'method': method, 'payload': json.loads(body_text or '{}')})
        if path == '/users/42' and method == 'DELETE':
            return _FakeHTTPResponse(json.dumps({'status': 'deleted', 'url': url}), status=200, headers={'Content-Type': 'application/json'})
        if path == '/profile' and method == 'GET':
            token = headers.get('Authorization', '')
            return _json_response({'status': 'ok', 'authorization': token, 'profile': {'name': 'demo-user'}})
        if path == '/items' and method == 'GET' and 'page' not in query:
            return _json_response({'items': [1, 2, 3], 'headers': headers})
        if path == '/items' and method == 'GET' and 'page' in query:
            return _json_response({'page': int(query.get('page', ['1'])[-1]), 'per_page': int(query.get('per_page', ['10'])[-1]), 'items': ['item-1', 'item-2']})
        if path == '/token' and method == 'POST':
            form = {k: v[-1] for k, v in parse_qs(body_text).items()}
            return _json_response({'access_token': 'fake-access-token', 'token_type': 'bearer', 'scope': form.get('scope', '')})
        if path == '/jobs/42' and method == 'GET':
            count = _POLL_COUNTS.get(url, 0) + 1
            _POLL_COUNTS[url] = count
            state = 'completed' if count >= 2 else 'running'
            return _json_response({'status': state, 'attempt': count})
    if host == 'example.com' and path == '/report.pdf' and method == 'GET':
        return _FakeHTTPResponse(b'%PDF-1.4\n% workstation fake report\n', status=200, headers={'Content-Type': 'application/pdf'})
    return None


def _fake_urlopen(request_or_url, data=None, *args, **kwargs):
    response = _handle_fake_http(request_or_url, data=data)
    if response is not None:
        return response
    return _ORIGINAL_URLOPEN(request_or_url, data=data, *args, **kwargs)


_urllib_request.urlopen = _fake_urlopen
