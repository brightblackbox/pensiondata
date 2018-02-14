import sys

from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    '192.168.0.2',
    '192.168.99.101',
    '0.0.0.0',
    'pensiondata-dev.us-east-1.elasticbeanstalk.com'
]

BASE_URL = 'http://127.0.0.1:8000'

# INTERNAL_IPS = ['127.0.0.1', '0.0.0.0', '172.18.0.1']
INTERNAL_IPS = ['127.0.0.1', '0.0.0.0']

INSTALLED_APPS += ['debug_toolbar']

DEBUG_TOOLBAR_CONFIG = {
    # Add in this line to disable the panel
    'DISABLE_PANELS': {
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.templates.TemplatesPanel'
    },
}

# MIDDLEWARE_CLASSES += ['debug_toolbar.middleware.DebugToolbarMiddleware']

IS_TESTING = sys.argv[1:2] == ['test']

if IS_TESTING:
    # In-memory DB for testing.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': None  # os.path.join(BASE_DIR, 'test_db.sqlite3'),
        }
    }

    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )


# Email settings

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery

# my local triubleshot - http://docs.celeryproject.org/en/latest/getting-started/brokers/rabbitmq.html
# BROKER_URL = 'amqp://admin:mypass@localhost:5672/rabbit'
# CELERY_RESULT_BACKEND = 'amqp://admin:mypass@localhost:5672/rabbit'
# sudo rabbitmqctl add_user myuser mypassword
# sudo rabbitmqctl add_vhost myvhost
# sudo rabbitmqctl set_user_tags myuser mytag
# sudo rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"
BROKER_URL = 'amqp://admin:mypass@rabbit//'
CELERY_RESULT_BACKEND = 'amqp://admin:mypass@rabbit//'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
