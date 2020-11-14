from millerp.settings.base import BASE_DIR, INSTALLED_APPS
import os

INSTALLED_APPS += [ 
    'accounts.apps.AccountsConfig',
    'core.apps.CoreConfig',
    'materials.apps.MaterialsConfig',
    'products.apps.ProductsConfig',
    'miscs.apps.MiscsConfig',
    'django.contrib.humanize',
    'mathfilters'
]

CACHES = {
    'default':{
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = '/login/'