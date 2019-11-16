# Django settings for faststart project.

import os
from datetime import timedelta
from django.core.urlresolvers import reverse_lazy
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
ROOT_PATH = os.path.dirname(PROJECT_PATH)

DEFAULT_FROM_EMAIL = 'no-reply@yoloify.com'

REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],

    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),

    'DEFAULT_RENDERER_CLASSES': [
                'rest_framework.renderers.JSONRenderer',
    ],
}

SOUTH_TESTS_MIGRATE = False

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

AUTH_PROFILE_MODULE = 'signup.Profile'

USERPIC_SIZE = "50x50"
USERPIC_LARGE_SIZE = "263x263"
USERPIC_SMALL_SIZE = "45x45"
CITYPIC_SIZE = "450x278"
CATEGORYPIC_SIZE = "350x216"

PIN_SIZE = "740"
PIN_THUMB_SIZE = "263"
LOGIN_REDIRECT_URL = '/'

CRISPY_TEMPLATE_PACK = 'bootstrap3'

# Minimum interval for resending confirmation-like emails (in minutes)
EMAIL_RESEND_INTERVAL = 5

# TODO
EMAIL_CONFIRMATION_DAYS = 7

COMPRESS_OUTPUT_DIR = ''

COMPRESS_PRECOMPILERS = (
    ('text/coffeescript', 'coffee --compile --stdio'),
    ('text/less', 'lessc {infile}'),
)

COMPRESS_ENABLED = True

PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'

DEBUG = False
THUMBNAIL_DEBUG = TEMPLATE_DEBUG = DEBUG

ADMINS = ('agrove87@gmail.com',)

MANAGERS = ADMINS

ADMIN_SIGNUP_NOTIFICATION = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(ROOT_PATH, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(ROOT_PATH, 'static_collected')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(ROOT_PATH, 'static'),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'compressor.finders.CompressorFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '#w20-0bt3fa^bp4g#=n2y3a9ynf4nb_zd2$lyde!l7bxk!evli'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'johnny.middleware.LocalStoreClearMiddleware',
    #'johnny.middleware.QueryCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'yoloify.signup.middleware.LastActivityMiddleware',
    'yoloify.pinboard.middleware.CurrentUsersMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'yoloify.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'yoloify.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, 'templates'),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of processors used by RequestContext to populate the context.
# Each one should be a callable that takes the request object as its
# only parameter and returns a dictionary to add to the context.
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'yoloify.signup.context_processors.auth_forms',
    'yoloify.pinboard.context_processors.pinboard_settings',
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect'
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.webdesign',
    'django.contrib.messages',
    'django.contrib.comments',
    'django.contrib.gis',
    'compressor',
    'sorl.thumbnail',
    'crispy_forms',
    'localflavor',
    'haystack',

    'yoloify.pages',
    'yoloify.signup',
    'yoloify.pinboard',
    'yoloify.stats',
    'yoloify.opening_hours',

    'rest_framework',
    'south',
    'social.apps.django_app.default',
    'tinymce',
    'djcelery',
    'djrill',
)

AUTHENTICATION_BACKENDS = (
    'social.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend'
)

SOCIAL_AUTH_FACEBOOK_KEY = '680458435349320'
SOCIAL_AUTH_FACEBOOK_SECRET = '7c8805124d6109f5123c9e9b92196952'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/local/?ref=signup'

SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.social_auth.associate_by_email',
    'social.pipeline.user.get_username',
    'social.pipeline.user.create_user',
    'yoloify.signup.social_auth.create_profile',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'yoloify.signup.social_auth.user_details',
    'yoloify.signup.social_auth.save_profile_picture'
)

MANDRILL_API_KEY = "6pLVN_w1tFFpI7VjY5Rteg"
EMAIL_BACKEND = "djrill.mail.backends.djrill.DjrillBackend"

SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email', 'first_name', 'last_name']
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
COMMENT_MAX_LENGTH = 500

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'yoloify': {
            'handlers': ['console'],
            'level': 'DEBUG'
        }
    }
}

PINBOARD_PART_SIZE = 25
PINBOARD_CACHE_UPDATE_PERIOD = 60 # in seconds

TINYMCE_DEFAULT_CONFIG = {
    'theme' : 'advanced',
    'theme_advanced_buttons1' : 'bold,italic,underline,separator,bullist,numlist,separator,link,unlink,fontsizeselect,fontselect,formatselect,removeformat',
    'theme_advanced_buttons2' : '',
    'theme_advanced_buttons3' : '',
    'theme_advanced_toolbar_location' : 'top',
    'theme_advanced_toolbar_align': 'left',
    'paste_text_sticky': True,
    'paste_text_sticky_default' : True,
    'valid_styles' : 'font-weight,font-style,text-decoration',
    'content_css': '/static/css/tinymce.css'
}

# Override messages tags representation to match the Bootstrap alert
# classes.
from django.contrib import messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# Maxumum allowable file size to upload, 10MB. Used in client-side
# file size validation with JavaScript
UPLOAD_FILE_MAX_SIZE = 8 * 1024 * 1024

# Extensions of supported image file formats. This will be used
# in JavaScript verification for the supported file types.
SUPPORTED_IMAGE_FORMATS = (
    'bmp',
    'eps',
    'gif',
    'im',
    'jpg',
    'jpe',
    'jpeg',
    'pcx',
    'png',
    'ppm',
    'tif',
    'tiff',
    'xbm',
)

BROKER_URL = 'redis://'
CELERY_RESULT_BACKEND = 'redis://'
CELERY_DEFAULT_QUEUE = 'default-queue'
CELERY_TIMEZONE = TIME_ZONE
CELERYD_PREFETCH_MULTIPLIER = 2
CELERY_TASK_RESULT_EXPIRES = 61
CELERY_ALWAYS_EAGER = False

CELERY_IMPORTS = ('yoloify.pinboard.tasks', 'yoloify.stats.tasks', )
CELERYBEAT_SCHEDULE = {
    'periodic_cache_updates': {
        'task': 'yoloify.pinboard.tasks.periodic_cache_updates',
        'schedule': timedelta(seconds=30),
        'options': {'queue': 'cache-queue'},
    },
    'calculate_usage_stats': {
        'task': 'yoloify.stats.tasks.aggregate_daily_usage_stats',
        'schedule': timedelta(hours=12),
        'options': {'queue': 'default-queue'},
    },
    'update_index': {
        'task': 'yoloify.pinboard.tasks.update_index',
        'schedule': timedelta(minutes=1),
        'options': {'queue': 'default-queue'},
    },
    'update_pin_like_bookmark_count': {
        'task': 'yoloify.pinboard.tasks.update_pin_like_bookmark_count',
        'schedule': timedelta(hours=3),
        'options': {'queue': 'default-queue'},
    },
    'ping_google': {
        'task': 'yoloify.pinboard.tasks.ping_google',
        'schedule': timedelta(hours=12),
        'options': {'queue': 'default-queue'},
    }
}
FEEDLY_REDIS_CONFIG = {
    'default': {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0,
        'password': None
    },
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join('/home/yoloify/data/', 'whoosh_index'),
    }
}

try:
    from local_settings import *
except ImportError:
    pass
