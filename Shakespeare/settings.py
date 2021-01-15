"""
Django settings for Shakespeare project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '*%c(9m9l*@sdb8vc@%+&g^vvgaxvec&951e6q3(hf)v20huztr'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.forms',

    'widget_tweaks',
    'django_bootstrap_breadcrumbs',

    'general.apps.MyAdminConfig',
    'general.apps.ShakespeareGeneralConfig',
    'local_data_storage.apps.LocalDataStorageConfig',
    'Questionaire.apps.QuestionaireConfig',
    'PageDisplay.apps.PagedisplayConfig',
    'reports.apps.ReportsConfig',
    'mailing.apps.MailingConfig',
    'questionaire_mailing',
    'queued_tasks',
    'initiative_enabler',
    'inquirer_settings',
    'data_analysis.apps.DataAnalysisConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Shakespeare.urls'

TEMPLATES = [
    {
        'NAME': 'Default_Template',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'assets/templates'),
                 os.path.join(BASE_DIR, 'assets/../reports/reports')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'Shakespeare.context_processors.questionaire_context'
            ],
            'builtins': [
                'reports.templatetags.pdf_tags_preview',
                'general.templatetags.django_extension_tags',
            ],
        },
    },
    {
        'NAME': 'PDFTemplates',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'assets/../reports/reports')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'Shakespeare.context_processors.questionaire_context',
                'Shakespeare.context_processors.pdf_context',
            ],
            'builtins': ['reports.templatetags.pdf_tags'],
        }
    },
    {
        'NAME': 'EmailTemplates',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'assets/mails')],
        'APP_DIRS': True,
        'OPTIONS': {
            'builtins': ['mailing.templatetags.mail_tags'],
        }
    },
]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

WSGI_APPLICATION = 'Shakespeare.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


STATIC_ROOT = os.path.join(BASE_DIR, "static")

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'assets/static/'),
)


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]
LANGUAGE_CODE = 'nl-nl'

LANGUAGES = [
    ('nl', _('Nederlands')),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

from .run_settings import *

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'

REPORT_ROOT = os.path.join(BASE_DIR, "reports/created_reports/")

MEDIA_ROOT = os.path.join(BASE_DIR, "uploads/")
MEDIA_URL = "/media/"

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Import local settings if that exists
try:
    from Shakespeare.local_settings import *
except ImportError:
    pass