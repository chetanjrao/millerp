from millerp.settings.base import INSTALLED_APPS


INSTALLED_APPS += [ 
    'accounts.apps.AccountsConfig'
]

AUTH_USER_MODEL = 'accounts.User'