from millerp.settings.base import INSTALLED_APPS


INSTALLED_APPS += [ 
    'accounts.apps.AccountsConfig',
    'core.apps.CoreConfig',
    'materials.apps.MaterialsConfig',
    'products.apps.ProductsConfig'
]

AUTH_USER_MODEL = 'accounts.User'