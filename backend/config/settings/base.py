"""
Base Settings for ClinSaarthi AI
Demonstrates 12-factor app configuration: all sensitive credentials and
swappable model parameters are loaded strictly from the environment.
"""
from datetime import timedelta
from pathlib import Path
import environ

# Base directory: backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize environment parser
env = environ.Env()

# Read .env file if it exists
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))

# Security
SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-clinsaarthi-dev-fallback-key-2026')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party packages
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Local application domain apps
    'apps.accounts',
    'apps.documents',
    'apps.notes',
    'apps.qa',
    'apps.study',
    'apps.evaluation',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database Configuration
# Fallback to local SQLite if DATABASE_URL is not set or SQLite is requested
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static and Media Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR.parent / 'data' / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.accounts.authentication.DemoOrJWTAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/min',
        'user': '120/min',
        'ask': '30/min',
        'notes': '20/min',
        'quiz': '40/min',
    }
}

# Baseline Security Headers & Clickjacking Protection
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# SimpleJWT Authentication Settings
JWT_SECRET_KEY = env('JWT_SECRET', default=SECRET_KEY)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': JWT_SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# ==============================================================================
# AI / RAG & MODEL CONFIGURATIONS
# All models are configurable via environment variables for complete flexibility.
# ==============================================================================
HF_TOKEN = env('HF_TOKEN', default='')

# Swappable Model Identifiers
LLM_MODEL_ID = env('LLM_MODEL_ID', default='Qwen/Qwen2.5-7B-Instruct')
EMBEDDING_MODEL_ID = env('EMBEDDING_MODEL_ID', default='BAAI/bge-m3')
RERANKER_MODEL_ID = env('RERANKER_MODEL_ID', default='BAAI/bge-reranker-base')
NLI_MODEL_ID = env('NLI_MODEL_ID', default='MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli')
SPACY_MODEL = env('SPACY_MODEL', default='en_core_sci_md')

# Vector Store Engine ('chroma' or 'faiss')
VECTOR_STORE_PROVIDER = env('VECTOR_STORE_PROVIDER', default='chroma').lower()
CHROMA_PERSIST_DIRECTORY = str(BASE_DIR.parent / 'data' / 'chroma_db')

# RAG Hyperparameters
DEBUG_RAG = env.bool('DEBUG_RAG', default=False)
CONFIDENCE_THRESHOLD = env.float('CONFIDENCE_THRESHOLD', default=0.50)
CHUNK_SIZE_TOKENS = 400
CHUNK_OVERLAP_TOKENS = 60
RETRIEVAL_TOP_K_DENSE = 20
RETRIEVAL_TOP_K_RERANK = 5

# Security Disclaimer Notice
DISCLAIMER_TEXT = (
    "DISCLAIMER: ClinSaarthi AI is an educational clinical knowledge assistant "
    "designed to support medical research and guideline review. It does NOT provide "
    "formal medical advice, definitive diagnoses, or binding treatment prescriptions. "
    "All recommendations must be evaluated and confirmed by licensed healthcare professionals."
)
