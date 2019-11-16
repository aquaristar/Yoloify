import os
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
ROOT_PATH = os.path.dirname(PROJECT_PATH)

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'yoloify',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

THUMBNAIL_DEBUG = True

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
    'USERS_COUNT': 50,
    'MAX_FOLLOWERS_COUNT': 20,
    'GOALS_COUNT': 300,
    'GOAL_IMG_MAX_WIDTH': 300,
    'GOAL_IMG_MAX_HEIGHT': 400,
}

# Celery settings
BROKER_URL = 'redis://'
CELERY_RESULT_BACKEND = 'redis://'
