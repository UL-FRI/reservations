from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

ENVIRONMENT = env.str("ENVIRONMENT", default="development")
IS_DEV = "dev" in ENVIRONMENT

if "prod" not in ENVIRONMENT:
    SECRET_KEY = "django-insecure-i+@5&9gvi7a8j^_5qm4rfzlb^s-&7iof*v!y$x=cv3x3q-06%2"
else:
    SECRET_KEY = env.str("SECRET_KEY")

DEBUG = env.bool("DEBUG", default=IS_DEV)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"] if DEBUG else [])

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition
INSTALLED_APPS = [
    "django_tomselect",
    "social_django",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "import_export",
    "crispy_forms",
    "crispy_bootstrap5",
    "guardian",
    "adminsortable2",
    "reservations",
    "reservations_connect",
    "reservations_connect.fri_urnik",
    "reservations_connect.rezervacije",
    "reservations_connect.metronik",
    "django_htmx",
    "django_filters",
    "debug_toolbar",
]

MIDDLEWARE = [
    "django_tomselect.middleware.TomSelectMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "reservations_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "reservations_site/templates"
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django_tomselect.context_processors.tomselect",
            ],
        },
    },
]

WSGI_APPLICATION = "reservations_site.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3")
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en"

TIME_ZONE = env.str("TIME_ZONE", default="Europe/Ljubljana")

USE_I18N = True

LANGUAGES = [
    ('en', 'English'),
    ('sl', 'Slovenščina'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = env.str("STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))

MEDIA_URL = "media/"
MEDIA_ROOT = env.str("MEDIA_ROOT", default=str(BASE_DIR / "media"))

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
    "guardian.backends.ObjectPermissionBackend",
)

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "reservations_site.permissions.DjangoObjectPermissionsOrReadOnly",
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 9999,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
}

# Used for Django Debug Toolbar.
INTERNAL_IPS = ["127.0.0.1"]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

TOMSELECT = {
    "DEFAULT_CSS_FRAMEWORK": "bootstrap5",
}

if "OIDC_ENDPOINT" in env:
    SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = env.str("OIDC_ENDPOINT")
    SOCIAL_AUTH_OIDC_KEY = env.str("OIDC_CLIENT_ID")
    SOCIAL_AUTH_OIDC_SECRET = env.str("OIDC_CLIENT_SECRET")


    SOCIAL_AUTH_PIPELINE = [
        'social_core.pipeline.social_auth.social_details',
        'social_core.pipeline.social_auth.social_uid',
        'social_core.pipeline.social_auth.auth_allowed',
        'social_core.pipeline.social_auth.social_user',
        'social_core.pipeline.user.get_username',
        'social_core.pipeline.social_auth.associate_by_email',
        'social_core.pipeline.user.create_user',
        'social_core.pipeline.social_auth.associate_user',
        'social_core.pipeline.social_auth.load_extra_data',
        'social_core.pipeline.user.user_details',
        
        'reservations_site.social.roles_to_groups',
    ]

    SOCIAL_AUTH_OIDC_EXTRA_DATA = [
        ('roles','roles'),
        ('email','email'),
        ('oid','oid'),
    ]

    SOCIAL_AUTH_OIDC_SCOPE = ['openid', 'profile', 'email']
    SOCIAL_AUTH_OIDC_ID_TOKEN_DECRYPTION_KEY = None
    SOCIAL_AUTH_OIDC_USERNAME_KEY = 'upn'
    SOCIAL_AUTH_USER_FIELDS = ['username', 'email']
