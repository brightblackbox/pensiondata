from .base import *


DEBUG = False
ALLOWED_HOSTS = ['*']


# Celery

BROKER_URL = 'amqp://admin:mypass@rabbit//'
CELERY_RESULT_BACKEND = 'amqp://admin:mypass@rabbit//'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
