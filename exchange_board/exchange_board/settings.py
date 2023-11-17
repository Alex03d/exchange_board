import os

from decouple import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = config('SECRET_KEY')

DEBUG = False

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'users.apps.UsersConfig',
    'comments.apps.CommentsConfig',
    'offers.apps.OffersConfig',
    'rating.apps.RatingConfig',
    'transactions.apps.TransactionsConfig',
    'exchange_rates.apps.ExchangeRatesConfig',
    'requests_for_transaction.apps.RequestsForTransactionConfig',
    'logging_app.apps.LoggingAppConfig',
    'bank_details.apps.BankDetailsConfig',
    'notifications.apps.NotificationsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'anymail',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'exchange_board.urls'

TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
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

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/ps0jc8heuqta/ashignet.club/media'
STATIC_ROOT = '/home/ps0jc8heuqta/ashignet.club/static'

WSGI_APPLICATION = 'exchange_board.wsgi.application'

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'ashignet',
            'USER': config('MY_SQL_USER'),
            'PASSWORD': config('MY_SQL_PASSWORD'),
            'HOST': 'localhost',
            'PORT': '3306',
        }
    }

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

AUTH_USER_MODEL = 'users.CustomUser'

LANGUAGE_CODE = 'en-us'


# if DEBUG:
#     MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
# else:
#     MEDIA_ROOT = 'home/ps0jc8heuqta/ashignet.club/media'

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Ulaanbaatar'

USE_I18N = True

USE_L10N = True

USE_TZ = True

TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = config('TELEGRAM_CHANNEL_ID')

EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'

ANYMAIL = {
    "MAILGUN_API_KEY": config('MAILGUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": "sharga42.info"
}

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# EMAIL_BACKEND = 'anymail.backends.mailjet.EmailBackend'

# ANYMAIL = {
#     'MAILJET_API_KEY': config('MAILJET_API_KEY'),
#     'MAILJET_SECRET_KEY': config('MAILJET_SECRET_KEY'),
#     'WEBHOOK_SECRET': config('WEBHOOK_SECRET'),
# }

