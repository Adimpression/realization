import json
import os
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

_FAKE_LOG = os.getenv('WORKSTATION_SDKUSER_FAKE_LOG', '')


def _append_log(message):
    if not _FAKE_LOG:
        return
    with open(_FAKE_LOG, 'a', encoding='utf-8') as handle:
        handle.write(str(message) + '\n')


def _register(name, module):
    sys.modules[name] = module
    return module


def _make_openai_module():
    module = ModuleType('openai')
    class _Responses:
        def create(self, *, model, input):
            _append_log(json.dumps({'sdk': 'openai.responses', 'model': model, 'input': input}, sort_keys=True))
            text = 'Hello.' if 'hello' in str(input).casefold() else f'Fake OpenAI response for: {input}'
            return SimpleNamespace(output_text=text, id='resp_fake_openai_1')
    class _Embeddings:
        def create(self, *, model, input):
            _append_log(json.dumps({'sdk': 'openai.embeddings', 'model': model, 'input': input}, sort_keys=True))
            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.11, 0.22, 0.33, 0.44])])
    class OpenAI:
        def __init__(self, *args, **kwargs):
            self.responses = _Responses()
            self.embeddings = _Embeddings()
    module.OpenAI = OpenAI
    return module


def _make_anthropic_module():
    module = ModuleType('anthropic')
    class Anthropic:
        def __init__(self, *args, **kwargs):
            self.messages = self
        def create(self, *, model, max_tokens, messages):
            _append_log(json.dumps({'sdk': 'anthropic.messages', 'model': model, 'max_tokens': max_tokens}, sort_keys=True))
            text = 'API reliability is strongest when retries, backoff, and observability are built in.'
            return SimpleNamespace(content=[SimpleNamespace(type='text', text=text)])
    module.Anthropic = Anthropic
    return module


def _make_boto3_module():
    module = ModuleType('boto3')
    class _S3Client:
        def list_objects_v2(self, *, Bucket, Prefix=''):
            _append_log(json.dumps({'sdk': 'boto3.s3.list_objects_v2', 'bucket': Bucket, 'prefix': Prefix}, sort_keys=True))
            keys = ['reports/daily.json', 'reports/report.txt', 'logs/app.log']
            filtered = [key for key in keys if str(key).startswith(str(Prefix or ''))]
            return {'Contents': [{'Key': key} for key in filtered]}
        def upload_file(self, local_path, bucket, key):
            _append_log(json.dumps({'sdk': 'boto3.s3.upload_file', 'local_path': local_path, 'bucket': bucket, 'key': key}, sort_keys=True))
            return None
    def client(service_name):
        if service_name != 's3':
            raise ValueError(f'Unsupported fake boto3 service: {service_name}')
        return _S3Client()
    module.client = client
    return module


def _make_google_modules():
    google = ModuleType('google')
    cloud = ModuleType('google.cloud')
    storage = ModuleType('google.cloud.storage')
    class _Blob:
        def __init__(self, name):
            self.name = name
        def download_to_filename(self, destination):
            _append_log(json.dumps({'sdk': 'google.cloud.storage.download_to_filename', 'blob_name': self.name, 'destination': destination}, sort_keys=True))
            path = Path(destination)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"status":"ok","source":"fake-gcs"}\n', encoding='utf-8')
    class _Bucket:
        def __init__(self, name):
            self.name = name
        def blob(self, blob_name):
            return _Blob(blob_name)
    class Client:
        def bucket(self, name):
            _append_log(json.dumps({'sdk': 'google.cloud.storage.bucket', 'bucket': name}, sort_keys=True))
            return _Bucket(name)
    storage.Client = Client
    cloud.storage = storage
    google.cloud = cloud
    _register('google', google)
    _register('google.cloud', cloud)
    _register('google.cloud.storage', storage)


def _make_slack_module():
    module = ModuleType('slack_sdk')
    class WebClient:
        def __init__(self, token):
            self.token = token
        def chat_postMessage(self, *, channel, text):
            _append_log(json.dumps({'sdk': 'slack_sdk.chat_postMessage', 'channel': channel, 'text': text}, sort_keys=True))
            return {'ts': '12345.6789'}
    module.WebClient = WebClient
    return module


def _make_github_module():
    module = ModuleType('github')
    class _Issue:
        def __init__(self, number, title):
            self.number = number
            self.title = title
    class _Repo:
        def __init__(self, name):
            self.name = name
        def get_issues(self, *, state='open'):
            _append_log(json.dumps({'sdk': 'github.get_issues', 'repo': self.name, 'state': state}, sort_keys=True))
            return [_Issue(1, 'Fix flaky deploy'), _Issue(2, 'Improve API reliability docs')]
    class Github:
        def __init__(self, token):
            self.token = token
        def get_repo(self, name):
            return _Repo(name)
    module.Github = Github
    return module


def _make_kubernetes_modules():
    kubernetes = ModuleType('kubernetes')
    client = ModuleType('kubernetes.client')
    config = ModuleType('kubernetes.config')
    def load_kube_config():
        _append_log(json.dumps({'sdk': 'kubernetes.load_kube_config'}, sort_keys=True))
        return None
    class CoreV1Api:
        def list_namespaced_pod(self, *, namespace):
            _append_log(json.dumps({'sdk': 'kubernetes.list_namespaced_pod', 'namespace': namespace}, sort_keys=True))
            pods = [SimpleNamespace(metadata=SimpleNamespace(name='api-0')), SimpleNamespace(metadata=SimpleNamespace(name='worker-0'))]
            return SimpleNamespace(items=pods)
    config.load_kube_config = load_kube_config
    client.CoreV1Api = CoreV1Api
    kubernetes.client = client
    kubernetes.config = config
    _register('kubernetes', kubernetes)
    _register('kubernetes.client', client)
    _register('kubernetes.config', config)


def _make_redis_module():
    module = ModuleType('redis')
    class _RedisClient:
        def __init__(self, url):
            self.url = url
        def get(self, key):
            _append_log(json.dumps({'sdk': 'redis.get', 'url': self.url, 'key': key}, sort_keys=True))
            return b'fake-session-value'
    def from_url(url):
        return _RedisClient(url)
    module.from_url = from_url
    return module


def _make_stripe_module():
    module = ModuleType('stripe')
    module.api_key = ''
    class _Customer:
        @staticmethod
        def retrieve(customer_id):
            _append_log(json.dumps({'sdk': 'stripe.Customer.retrieve', 'customer_id': customer_id}, sort_keys=True))
            return {'id': customer_id, 'email': 'customer@example.com'}
    module.Customer = _Customer
    return module


def _make_supabase_module():
    module = ModuleType('supabase')
    class _Query:
        def __init__(self, table):
            self._table = table
        def select(self, *_args, **_kwargs):
            return self
        def execute(self):
            _append_log(json.dumps({'sdk': 'supabase.select', 'table': self._table}, sort_keys=True))
            return SimpleNamespace(data=[{'id': 1, 'name': 'Ada'}, {'id': 2, 'name': 'Linus'}])
    class _Client:
        def __init__(self, url, key):
            self.url = url
            self.key = key
        def table(self, name):
            return _Query(name)
    def create_client(url, key):
        return _Client(url, key)
    module.create_client = create_client
    return module


_register('openai', _make_openai_module())
_register('anthropic', _make_anthropic_module())
_register('boto3', _make_boto3_module())
_make_google_modules()
_register('slack_sdk', _make_slack_module())
_register('github', _make_github_module())
_make_kubernetes_modules()
_register('redis', _make_redis_module())
_register('stripe', _make_stripe_module())
_register('supabase', _make_supabase_module())
