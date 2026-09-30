"""
Settings Package Initializer
Demonstrates dynamic module loading based on environment variables.
Defaults to 'dev' settings for seamless local development.
"""
import os

env = os.environ.get("ENVIRONMENT", "dev").lower()

if env == "prod" or env == "production":
    from .prod import *
else:
    from .dev import *
