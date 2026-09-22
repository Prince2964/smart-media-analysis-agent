"""Explicit live API/Blob test; removes only blobs created by this run."""
import io
import time
import httpx
from PIL import Image, ImageDraw
from .storage import AzureBlobStorage


def main():
    image = io.BytesIO()
    picture = Image.new('RGB', (800, 400), 'white')
    ImageDraw.Draw(picture).text((30, 80), 'Workshop starts at 10:30 AM. Room 204.', fill='black', font_size=30)
    picture.save(image, format='PNG')
    payload = image.getvalue()
    storage = AzureBlobStorage.from_env()
    blob_name = None
    try:
        with httpx.Client(base_url='http://127.0.0.1:8000', timeout=60) as client:
            health = client.get('/api/health').json()
            assert health['blob_access_verified']
            response = client.post('/api/uploads', data={'source_type': 'image'},
                                   files={'file': ('connection-test.png', payload, 'image/png')})
            response.raise_for_status()
            for _ in range(660):
                job = client.get('/api/jobs/' + response.json()['id']).json()
                blob_name = job.get('storage_blob')
                if job['status'] in ('complete', 'failed'):
                    break
                time.sleep(.5)
            assert job['status'] == 'complete', 'API job did not complete'
            if health['mode'] in ('azure-image', 'azure-media'):
                assert job['document']['is_mock'] is False
                assert '204' in job['document']['summary']
                assert client.post('/api/jobs/' + job['id'] + '/questions', json={'question': 'What port is shown?'}).status_code == 409
            else:
                assert job['document']['is_mock']
            assert blob_name and storage.container.download_blob(blob_name).readall() == payload
            print('PASS: API upload stored matching bytes; report mode:', health['mode'])
            print('Job:', job['id'])
    finally:
        if blob_name:
            storage.container.delete_blob(blob_name)
            print('Removed only the blob created by this API test.')
        storage.close()


if __name__ == '__main__':
    main()


