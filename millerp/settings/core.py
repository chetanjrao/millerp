from millerp.settings.base import BASE_DIR, INSTALLED_APPS
import os

INSTALLED_APPS += [ 
    'accounts.apps.AccountsConfig',
    'core.apps.CoreConfig',
    'materials.apps.MaterialsConfig',
    'products.apps.ProductsConfig',
    'miscs.apps.MiscsConfig',
    'django.contrib.humanize'
]

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = '/login/'