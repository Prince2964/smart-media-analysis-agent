"""Explicit authentication selection shared by every Azure integration."""
import os
from azure.identity import AzureCliCredential, ClientSecretCredential, ManagedIdentityCredential


def get_credential(process_timeout=30):
    mode = os.getenv('AZURE_AUTH_MODE', 'cli').strip().lower()
    if mode == 'cli':
        return AzureCliCredential(process_timeout=process_timeout)
    if mode == 'service-principal':
        names = ('AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET')
        missing = [name for name in names if not os.getenv(name, '').strip()]
        if missing:
            raise ValueError('Service principal configuration missing: ' + ', '.join(missing))
        return ClientSecretCredential(*(os.environ[name] for name in names))
    if mode == 'managed-identity':
        client_id = os.getenv('AZURE_CLIENT_ID', '').strip()
        return ManagedIdentityCredential(**({'client_id': client_id} if client_id else {}))
    raise ValueError('AZURE_AUTH_MODE must be cli, service-principal or managed-identity.')
