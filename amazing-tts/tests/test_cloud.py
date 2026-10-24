"""State-machine unit tests; no cloud credentials or paid resources required."""
from copy import deepcopy
import time
import pytest
from amazing_tts import cloud as module


class Snapshot:
    def __init__(self, value): self.value, self.exists = deepcopy(value), value is not None
    def to_dict(self): return deepcopy(self.value)


class Reference:
    def __init__(self, db, path): self.db, self.path = db, path
    def get(self, transaction=None): return Snapshot(self.db.values.get(self.path))


class Collection:
    def __init__(self, db, name): self.db, self.name = db, name
    def document(self, name): return Reference(self.db, self.name+'/'+name)


class FakeDB:
    def __init__(self): self.values = {}
    def collection(self, name): return Collection(self, name)
    def transaction(self): return self
    def set(self, ref, data): self.values[ref.path] = deepcopy(data)
    def update(self, ref, data): self.values[ref.path].update(deepcopy(data))


@pytest.fixture
def cloud(monkeypatch):
    monkeypatch.setattr(module.firestore, 'transactional', lambda f: f)
    monkeypatch.setenv('WORKER_URL','https://private-worker.example.run.app')
    c = object.__new__(module.Cloud)
    c.db = FakeDB()
    c.jobs = c.db.collection('books')
    c.enqueued = []
    c.enqueue = lambda *args: c.enqueued.append(args)
    return c


def test_shared_request_preserves_identity_and_running_lease(cloud):
    first = cloud.request('https://novelping.com/book/a', 1, 'user1')
    job, token = cloud.lease(first['id'], 1, first['run_id'])
    second = cloud.request('https://novelping.com/book/a', 5, 'user2')
    assert first['id'] == second['id']
    assert second['run_id'] == first['run_id'] and second['target'] == 5
    current = cloud.get(first['id'])
    assert current['lease_token'] == token and current['state'] == 'running'
    assert len(cloud.enqueued) == 1


def test_duplicate_worker_cannot_claim_a_live_lease(cloud):
    first = cloud.request('https://novelping.com/book/a', 1, 'user1')
    _, token = cloud.lease(first['id'], 1, first['run_id'])
    with pytest.raises(RuntimeError,match='Another worker'):
        cloud.lease(first['id'], 1, first['run_id'])
    with pytest.raises(RuntimeError,match='no longer belongs'):
        cloud.finish(first['id'], 'wrong-token', {'state':'complete'})
    assert cloud.get(first['id'])['lease_token'] == token


def test_target_extended_before_commit_schedules_next(cloud):
    first = cloud.request('https://novelping.com/book/a', 1, 'user1')
    _, token = cloud.lease(first['id'], 1, first['run_id'])
    cloud.request('https://novelping.com/book/a', 4, 'user2')
    cloud.finish(first['id'],token,{'ready':1,'next':2,'state':'complete'},has_next=True)
    assert cloud.get(first['id'])['state'] == 'queued'


def test_old_task_cannot_claim_resumed_run(cloud):
    first = cloud.request('https://novelping.com/book/a', 2, 'user1')
    _, token = cloud.lease(first['id'], 1, first['run_id'])
    cloud.finish(first['id'], token, {'state':'paused'})
    resumed = cloud.request('https://novelping.com/book/a', 2, 'user1')
    assert resumed['run_id'] != first['run_id']
    assert cloud.lease(first['id'],1,first['run_id'])[0] is None


def test_cached_shared_book_never_enqueues_generation(cloud):
    first = cloud.request('https://novelping.com/book/a', 2, 'user1')
    _, token = cloud.lease(first['id'], 1, first['run_id'])
    cloud.finish(first['id'], token, {'state':'complete','ready':2,'next':3})
    count = len(cloud.enqueued)
    second = cloud.request('https://novelping.com/book/a', 2, 'another-user')
    assert second['ready'] == 2 and len(cloud.enqueued) == count


def test_per_user_new_generation_request_cap(cloud):
    for n in range(3): cloud.request(f'https://novelping.com/book/a-{n}',1,'user')
    with pytest.raises(ValueError,match='Daily generation request limit'):
        cloud.request('https://novelping.com/book/a-fourth',1,'user')


def test_shared_quota_counts_every_attempt(cloud, monkeypatch):
    monkeypatch.setenv('GEMINI_DAILY_BUDGET','2')
    cloud.reserve('model',100)
    cloud.reserve('model',100)
    with pytest.raises(RuntimeError,match='Daily shared'):
        cloud.reserve('model',100)


def test_redelivery_after_commit_recovers_enqueue_gap(cloud):
    first = cloud.request('https://novelping.com/book/a', 3, 'user')
    _, token = cloud.lease(first['id'],1,first['run_id'])
    cloud.finish(first['id'],token,{'state':'queued','ready':1,'next':2})
    cloud.work(first['id'],1,first['run_id'])
    assert cloud.enqueued[-1] == (first['id'],2,first['run_id'])


def test_task_uses_private_oidc_worker_and_stable_name(cloud, monkeypatch):
    first = cloud.request('https://novelping.com/book/a', 1, 'user')
    monkeypatch.setenv('GOOGLE_CLOUD_PROJECT','project')
    monkeypatch.setenv('TASK_SERVICE_ACCOUNT','tasks@project.iam.gserviceaccount.com')
    created=[]
    class Tasks:
        def queue_path(self,*args): return '/'.join(args)
        def create_task(self,**kwargs): created.append(kwargs)
    monkeypatch.setattr(module.tasks_v2,'CloudTasksClient',Tasks)
    module.Cloud.enqueue(cloud,first['id'],1,first['run_id'])
    module.Cloud.enqueue(cloud,first['id'],1,first['run_id'])
    assert created[0]['task']['name'] == created[1]['task']['name']
    request = created[0]['task']['http_request']
    assert request['oidc_token']['service_account_email'].startswith('tasks@')
    assert request['oidc_token']['audience'] == 'https://private-worker.example.run.app'
    assert created[0]['task']['dispatch_deadline']['seconds'] == 1800
