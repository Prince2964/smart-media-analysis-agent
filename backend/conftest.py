import os

# Unit tests must not load the developer's Azure settings or contact Azure.
os.environ['BACKEND_LOAD_ENV'] = 'false'
