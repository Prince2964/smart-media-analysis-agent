"""Load backend configuration independently of the terminal's working directory."""
import os
from pathlib import Path
from dotenv import load_dotenv


def load_backend_env():
    # Environment variables supplied by a hosting platform take precedence.
    if os.getenv('BACKEND_LOAD_ENV', 'true').lower() != 'false':
        load_dotenv(Path(__file__).resolve().parent / '.env', override=False)
