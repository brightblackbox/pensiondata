from .base import *


DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '192.168.0.2', '192.168.99.101', '0.0.0.0', 'pensiondata-dev.us-east-1.elasticbeanstalk.com']

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