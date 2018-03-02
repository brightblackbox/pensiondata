from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

BASE_URL = 'http://127.0.0.1:8000'

# BROKER_URL = os.environ.get("CLOUDAMQP_URL", "django://")
# CELERY_RESULT_BACKEND = 'rpc'

BROKER_URL = 'amqp://admin:mypass@localhost:5672/rabbit'
CELERY_RESULT_BACKEND = 'amqp://admin:mypass@localhost:5672/rabbit'

# Update database configuration with $DATABASE_URL.
import dj_database_url
db_from_env = dj_database_url.config()
DATABASES['default'].update(db_from_env)