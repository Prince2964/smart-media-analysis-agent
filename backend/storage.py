"""Private Blob Storage using the configured Azure identity."""
import os
import re
from typing import Protocol
from uuid import uuid4
from urllib.parse import urlsplit

from .auth import get_credential
from azure.storage.blob import BlobServiceClient, ContentSettings


class MediaStorage(Protocol):
    def upload(self, data: bytes, content_type: str) -> str: ...


class AzureBlobStorage:
    def __init__(self, endpoint: str, container: str):
        url = urlsplit(endpoint)
        if (url.scheme != 'https' or not url.hostname or
                not re.fullmatch(r'[a-z0-9]{3,24}\.blob\.core\.windows\.net', url.hostname)
                or url.path not in ('', '/') or url.query or url.fragment or url.username or url.port):
            raise ValueError('Use the plain HTTPS Blob service endpoint, without tokens or a container path.')
        if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{1,61})[a-z0-9]', container) or '--' in container:
            raise ValueError('Invalid container name.')
        self.credential = get_credential(process_timeout=30)
        self.service = BlobServiceClient(endpoint, credential=self.credential,
                                        connection_timeout=30, read_timeout=120, retry_total=3,
                                        max_single_put_size=4 * 1024 * 1024,
                                        max_block_size=4 * 1024 * 1024)
        self.container = self.service.get_container_client(container)

    @classmethod
    def from_env(cls):
        return cls(os.environ['AZURE_STORAGE_ACCOUNT_URL'], os.environ['AZURE_STORAGE_CONTAINER'])

    def upload(self, data: bytes, content_type: str) -> str:
        name = f'media/{uuid4().hex}'
        self.container.upload_blob(name, data, overwrite=False, max_concurrency=2,
                                   content_settings=ContentSettings(content_type=content_type))
        return name

    def verify(self):
        # Never enumerate, overwrite, or delete user-uploaded blobs.
        blob = self.container.get_blob_client(f'connection-tests/{uuid4().hex}.txt')
        payload = b'Smart Media Analysis Agent storage connectivity test'
        created = False
        try:
            blob.upload_blob(payload, overwrite=False)
            created = True
            if blob.download_blob().readall() != payload:
                raise RuntimeError('Storage round-trip content mismatch')
        finally:
            if created:
                blob.delete_blob()

    def close(self):
        self.service.close()
        self.credential.close()
