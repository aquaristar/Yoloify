import os
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
ROOT_PATH = os.path.dirname(PROJECT_PATH)

ALLOWED_HOSTS = ['yoloify.com', 'www.yoloify.com', 'localhost', '127.0.0.1']
SESSION_COOKIE_DOMAIN = '.yoloify.com'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'yoloify',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'yoloify',
        'PASSWORD': '2eqob1F5gugumeM',
        'HOST': 'localhost',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '5432',                      # Set to empty string for default.
    }
}

#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
MANDRILL_API_KEY = "6IutBPsrlE9KoSEhiJB4mA"
EMAIL_BACKEND = "djrill.mail.backends.djrill.DjrillBackend"

THUMBNAIL_DEBUG = True
COMPRESS_URL = '/static/'
COMPRESS_ROOT = '/home/yoloify/virtual/yoloify/static/'

CACHES = {
    'default': {
        'BACKEND': 'johnny.backends.memcached.MemcachedCache',
        'LOCATION': ['127.0.0.1:11211'],
        'JOHNNY_CACHE': True,
    }
}
JOHNNY_MIDDLEWARE_KEY_PREFIX = 'jc_yoloify'
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600
CACHE_MIDDLEWARE_KEY_PREFIX = 'yoloify'

TEST_POPULATION = {
    'USERS_FIRST_NAME_PREFIX': 'user',
    'USERS_LAST_NAME': 'test',
    'USERS_COUNT': 300,
    'MAX_FOLLOWERS_COUNT': 120,
    'GOALS_COUNT': 1000,
    'GOAL_IMG_MAX_WIDTH': 300,
    'GOAL_IMG_MAX_HEIGHT': 400,
}
