"""Run explicitly: python -m backend.check_storage. Never prints credentials."""
from azure.core.exceptions import AzureError
from .storage import AzureBlobStorage


def main():
    storage = None
    try:
        storage = AzureBlobStorage.from_env()
        storage.verify()
        print('PASS: uploaded, read back matching bytes, and deleted the unique test blob.')
    except (AzureError, ValueError, KeyError, RuntimeError) as exc:
        print(f'FAIL: {type(exc).__name__}; code={getattr(exc, "error_code", None)}')
        print('Check Azure CLI sign-in, container role, endpoint, and storage network rules.')
        return 1
    finally:
        if storage:
            storage.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
