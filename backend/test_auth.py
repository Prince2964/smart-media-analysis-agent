import pytest
from . import auth


def test_service_principal_does_not_fall_back_to_personal_login(monkeypatch):
    monkeypatch.setenv('AZURE_AUTH_MODE', 'service-principal')
    for name in ('AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET'):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValueError, match='AZURE_CLIENT_SECRET'):
        auth.get_credential()


def test_service_principal_uses_environment(monkeypatch):
    monkeypatch.setenv('AZURE_AUTH_MODE', 'service-principal')
    for name, value in [('AZURE_TENANT_ID','tenant'), ('AZURE_CLIENT_ID','client'), ('AZURE_CLIENT_SECRET','secret')]:
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(auth, 'ClientSecretCredential', lambda *args: args)
    assert auth.get_credential() == ('tenant', 'client', 'secret')


def test_cli_and_managed_identity_selection(monkeypatch):
    monkeypatch.setenv('AZURE_AUTH_MODE', 'cli')
    monkeypatch.setattr(auth, 'AzureCliCredential', lambda **kw: kw)
    assert auth.get_credential() == {'process_timeout': 30}
    monkeypatch.setenv('AZURE_AUTH_MODE', 'managed-identity')
    monkeypatch.delenv('AZURE_CLIENT_ID', raising=False)
    monkeypatch.setattr(auth, 'ManagedIdentityCredential', lambda **kw: kw)
    assert auth.get_credential() == {}
