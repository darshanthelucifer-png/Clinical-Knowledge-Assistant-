"""
ASGI config for ClinSaarthi AI backend.
Enables asynchronous request handling and SSE (Server-Sent Events) streaming.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
