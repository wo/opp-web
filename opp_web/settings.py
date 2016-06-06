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

    DEBUG = False
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
]

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

