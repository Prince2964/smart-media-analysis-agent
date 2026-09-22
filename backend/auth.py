"""Explicit authentication selection shared by every Azure integration."""
import os
from azure.identity import AzureCliCredential, ClientSecretCredential, ManagedIdentityCredential


def key_mode():
    return os.getenv('AZURE_AUTH_MODE', 'cli').strip().lower() == 'api-key'


def required_key(name):
    value = os.getenv(name, '').strip()
    if not value:
        raise ValueError('Missing backend configuration: ' + name)
    return value


def service_headers(key_name, scope, factory=None, key_header='api-key'):
    if key_mode():
        return {key_header: required_key(key_name)}
    with (factory or get_credential)() as credential:
        return {'Authorization': 'Bearer ' + credential.get_token(scope).token}


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
