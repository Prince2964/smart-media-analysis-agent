import io
import time
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from . import main
from .storage import AzureBlobStorage


@pytest.mark.parametrize('url', ['http://account.blob.core.windows.net',
    'https://account.blob.core.windows.net/?sig=secret', 'https://example.com',
    'https://account.blob.core.windows.net/container'])
def test_reject_unsafe_endpoint(url):
    with pytest.raises(ValueError):
        AzureBlobStorage(url, 'media-uploads')


@pytest.mark.parametrize('fails', [False, True])
def test_upload_storage_success_or_failure(monkeypatch, fails):
    monkeypatch.setenv('STORAGE_MODE', 'discard')
    fake = Mock()
    if fails:
        fake.upload.side_effect = RuntimeError('private diagnostic must not leak')
    else:
        fake.upload.return_value = 'media/test-id'
    with TestClient(main.app) as client:
        monkeypatch.setattr(main, 'storage', fake)
        # Invalid bytes must never reach storage.
        assert client.post('/api/uploads', data={'source_type': 'image'},
                           files={'file': ('bad.png', b'bad')}).status_code == 415
        fake.upload.assert_not_called()
        image = io.BytesIO()
        Image.new('RGB', (2, 2)).save(image, format='PNG')
        response = client.post('/api/uploads', data={'source_type': 'image'},
                               files={'file': ('test.png', image.getvalue())})
        assert response.status_code == 202
        for _ in range(80):
            result = client.get('/api/jobs/' + response.json()['id']).json()
            if result['status'] in ('complete', 'failed'):
                break
            time.sleep(.03)
        fake.upload.assert_called_once_with(image.getvalue(), 'image/png')
        if fails:
            assert result['status'] == 'failed' and result['document'] is None
            assert 'private diagnostic' not in result['error']
        else:
            assert result['storage_blob'] == 'media/test-id'
            assert result['document']['is_mock'] is True
