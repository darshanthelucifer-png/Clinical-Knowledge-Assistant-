"""
Development Settings for ClinSaarthi AI
"""
from .base import *

DEBUG = True

# Allow all origins for local development with Vite dev server (port 5173, etc.)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Development email backend prints to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
