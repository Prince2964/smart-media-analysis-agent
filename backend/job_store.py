"""Local completed-report persistence. No credentials or uploaded media bytes."""
import os
from pathlib import Path
from .models import Job

ROOT = Path(__file__).resolve().parents[1] / '.local' / 'jobs'

def save_job(job: Job):
    if os.getenv('PYTEST_CURRENT_TEST'):
        return
    ROOT.mkdir(parents=True, exist_ok=True)
    target = ROOT / f'{job.id}.json'
    temp = target.with_suffix('.tmp')
    temp.write_text(job.model_dump_json(), encoding='utf-8')
    temp.replace(target)

def load_jobs():
    if os.getenv('PYTEST_CURRENT_TEST'):
        return {}
    result = {}
    for path in ROOT.glob('*.json'):
        try:
            job = Job.model_validate_json(path.read_text(encoding='utf-8'))
            if job.status in ('complete', 'failed'):
                result[job.id] = job
        except (ValueError, OSError):
            continue
    return result
