from . import job_store
from .models import Job

def test_reports_survive_reload(tmp_path,monkeypatch):
    monkeypatch.setattr(job_store,'ROOT',tmp_path)
    monkeypatch.delenv('PYTEST_CURRENT_TEST',raising=False)
    job=Job(id='safe-id',source_type='image',source_name='image',status='failed',error='test')
    job_store.save_job(job)
    assert job_store.load_jobs()[job.id].error=='test'
