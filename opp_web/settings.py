"""
We use the presence of settings_production.py to figure out
whether we're in production or development. settings_production.py
only sets the sensitive values SECRET_KEY and DATABASES.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    # PRODUCTION SETTINGS
    
    from .settings_production import *

    DEBUG = True
    ALLOWED_HOSTS = ['philosophicalprogress.org', 'www.philosophicalprogress.org']
    STATIC_ROOT = '/home/wo/opp-web/static/'
    
except ImportError:
    # DEVELOPMENT SETTINGS

    SECRET_KEY = '0az&sox64yzpaasldfkjl8104*)#%%%%%na@ax33qicqh5j(y4z'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'opptools',
            'USER': 'opp',
            'PASSWORD': 'opp',
            'HOST': 'localhost'
        }
    }
    
    DEBUG = True
    ALLOWED_HOSTS = []
    
    SUPERFEEDR_USER = ''
    SUPERFEEDR_PASSWORD = ''

STATIC_URL = '/static/'
LOGIN_REDIRECT_URL = 'website.views.index'
LOGIN_URL = 'django.contrib.auth.views.login'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap3',
    'accounts',
    'accesslogger',
    'feedhandler',
    'website',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accesslogger.middleware.AccessLoggerMiddleware',
]

# for accesslogger:
NO_STATS_URLS = ['/media', '/static', '/feed.xml']
NO_STATS_USERAGENTS = ['dotbot']

ROOT_URLCONF = 'opp_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'opp_web.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = False

USE_L10N = True

USE_TZ = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False, # keep Django's default loggers
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'timestampthread': {
            'format': "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] [%(name)-20.20s]  %(message)s",
        },
    },
    'handlers': {
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'log', 'opp_web.log'),
            'maxBytes': 50 * 10**6, # 50 MB
            'backupCount': 3, # keep this many extra historical files
            'formatter': 'timestampthread'
        },
        'console': {
            'level': 'DEBUG', # DEBUG or higher goes to the console
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': { # configure all of Django's loggers
            'handlers': ['logfile', 'console'],
            'level': 'INFO', # set to debug to see e.g. database queries
            'propagate': False, # don't propagate further, to avoid duplication
        },
        '': {
            'handlers': ['logfile', 'console'],
            'level': 'DEBUG',
        },
    },
}
