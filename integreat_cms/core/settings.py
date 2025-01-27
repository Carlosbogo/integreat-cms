"""
Django settings for ``integreat-cms``.

This file only contains the options which deviate from the default values.
For the full list of settings and their values, see :doc:`django:ref/settings`.

For production use, the following settings can be set with environment variables (use the prefix ``DJANGO_``):

    * ``DJANGO_SECRET_KEY``: :attr:`~integreat_cms.core.settings.SECRET_KEY`
    * ``DJANGO_DEBUG``: :attr:`~integreat_cms.core.settings.DEBUG`
    * ``DJANGO_LOGFILE``: :attr:`~integreat_cms.core.settings.LOGFILE`
    * ``DJANGO_WEBAPP_URL``: :attr:`~integreat_cms.core.settings.WEBAPP_URL`
    * ``DJANGO_MATOMO_URL``: :attr:`~integreat_cms.core.settings.MATOMO_URL`
    * ``DJANGO_BASE_URL``: :attr:`~integreat_cms.core.settings.BASE_URL`
    * ``DJANGO_STATIC_ROOT``: :attr:`~integreat_cms.core.settings.STATIC_ROOT`
    * ``DJANGO_MEDIA_ROOT``: :attr:`~integreat_cms.core.settings.MEDIA_ROOT`
    * ``DJANGO_XLIFF_ROOT``: :attr:`~integreat_cms.core.settings.XLIFF_ROOT`

Database settings: :attr:`~integreat_cms.core.settings.DATABASES`

    * ``DJANGO_DB_HOST``
    * ``DJANGO_DB_NAME``
    * ``DJANGO_DB_PASSWORD``
    * ``DJANGO_DB_USER``
    * ``DJANGO_DB_PORT``

Email settings:

    * ``DJANGO_EMAIL_HOST``: :attr:`~integreat_cms.core.settings.EMAIL_HOST`
    * ``DJANGO_EMAIL_HOST_PASSWORD``: :attr:`~integreat_cms.core.settings.EMAIL_HOST_PASSWORD`
    * ``DJANGO_EMAIL_HOST_USER``: :attr:`~integreat_cms.core.settings.EMAIL_HOST_USER`
    * ``DJANGO_EMAIL_PORT``: :attr:`~integreat_cms.core.settings.EMAIL_PORT`

Cache settings: :attr:`~integreat_cms.core.settings.CACHES`

    * ``DJANGO_REDIS_CACHE``: Whether or not the Redis cache should be enabled
    * ``DJANGO_REDIS_UNIX_SOCKET``:  If Redis is enabled and available via a unix socket, set this environment variable
      to the location of the socket, e.g. ``/var/run/redis/redis.sock``.
      Otherwise, the connection falls back to a regular TCP connection on port ``6379``.
      For development, this can also be set via the file ``.redis_socket_location``.

"""
import os
import urllib

from .logging_formatter import ColorFormatter


###################
# CUSTOM SETTINGS #
###################

#: Build paths inside the project like this: ``os.path.join(BASE_DIR, ...)``
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if "DJANGO_WEBAPP_URL" in os.environ:
    WEBAPP_URL = os.environ["DJANGO_WEBAPP_URL"]
else:
    #: The URL to our webapp. This is used for urls in the ``sitemap.xml`` (see :mod:`~integreat_cms.sitemap` for more information).
    WEBAPP_URL = "https://integreat.app"

if "DJANGO_MATOMO_URL" in os.environ:
    MATOMO_URL = os.environ["DJANGO_MATOMO_URL"]
else:
    #: The URL to the Matomo statistics server.
    MATOMO_URL = "https://statistics.integreat-app.de"

#: The slug for the legal notice (see e.g. :class:`~integreat_cms.cms.models.pages.imprint_page_translation.ImprintPageTranslation`)
IMPRINT_SLUG = "imprint"

#: The ID of the region "Testumgebung" - prevent sending PNs to actual users in development in
#: :func:`~integreat_cms.cms.views.push_notifications.push_notification_sender.PushNotificationSender.send_pn`
TEST_BLOG_ID = 154

#: URL to the Integreat Website
WEBSITE_URL = "https://integreat-app.de"

#: An alias of :attr:`~integreat_cms.core.settings.WEBAPP_URL`. Used by django-linkcheck to determine whether a link is internal.
SITE_DOMAIN = WEBAPP_URL

#: URLs to the Integreat blog
BLOG_URLS = {
    "en": f"{WEBSITE_URL}/en/blog/",
    "de": f"{WEBSITE_URL}/blog/",
}

#: URL to the Integreat wiki
WIKI_URL = "https://wiki.integreat-app.de"

#: RSS feed URLs to the Integreat blog
RSS_FEED_URLS = {
    "en": f"{WEBSITE_URL}/en/feed/",
    "de": f"{WEBSITE_URL}/feed/",
}

#: How many days of chat history should be shown
AUTHOR_CHAT_HISTORY_DAYS = 30

#: The time span up to which recurrent events should be returned by the api
API_EVENTS_MAX_TIME_SPAN_DAYS = 31

###############################
# Firebase Push Notifications #
###############################

#: Authentification Token for the Firebase API. This needs to be set for a correct usage of the Messages Feature.
FCM_KEY = None

###########
# GVZ API #
###########

#: Whether or not the GVZ (Gemeindeverzeichnis) API is enabled. This is used to automatically import coordinates and
#: region aliases (see :mod:`~integreat_cms.gvz_api` for more information).
GVZ_API_ENABLED = True

#: The URL to our GVZ (Gemeindeverzeichnis) API. This is used to automatically import coordinates and region aliases
#: (see :mod:`~integreat_cms.gvz_api` for more information).
GVZ_API_URL = "https://gvz.integreat-app.de"


############
# WEBAUTHN #
############

if "DJANGO_BASE_URL" in os.environ:
    HOSTNAME = urllib.parse.urlparse(os.environ["DJANGO_BASE_URL"]).netloc
    BASE_URL = os.environ["DJANGO_BASE_URL"]
else:
    #: Needed for `webauthn <https://pypi.org/project/webauthn/>`__
    #: (this is a setting in case the application runs behind a proxy).
    #: Used in the following views:
    #:
    #: - :class:`~integreat_cms.cms.views.settings.mfa.register_user_mfa_key_view.RegisterUserMfaKeyView`
    #: - :class:`~integreat_cms.cms.views.authentication.mfa.mfa_verify_view.MfaVerifyView`
    BASE_URL = "http://localhost:8000"
    #: Needed for `webauthn <https://pypi.org/project/webauthn/>`__
    #: (this is a setting in case the application runs behind a proxy).
    #: Used in the following views:
    #:
    #: - :class:`~integreat_cms.cms.views.settings.mfa.get_mfa_challenge_view.GetMfaChallengeView`
    #: - :class:`~integreat_cms.cms.views.settings.mfa.register_user_mfa_key_view.RegisterUserMfaKeyView`
    #: - :class:`~integreat_cms.cms.views.authentication.mfa.mfa_assert_view.MfaAssertView`
    #: - :class:`~integreat_cms.cms.views.authentication.mfa.mfa_verify_view.MfaVerifyView`
    HOSTNAME = "localhost"


########################
# DJANGO CORE SETTINGS #
########################

if "DJANGO_DEBUG" in os.environ:
    DEBUG = bool(os.environ["DJANGO_DEBUG"])
else:
    #: A boolean that turns on/off debug mode (see :setting:`django:DEBUG`)
    #:
    #: .. warning::
    #:     Never deploy a site into production with :setting:`DEBUG` turned on!
    DEBUG = True

#: Enabled applications (see :setting:`django:INSTALLED_APPS`)
INSTALLED_APPS = [
    # Installed custom apps
    "integreat_cms.cms",
    "integreat_cms.gvz_api",
    # Installed Django apps
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    # Installed third-party-apps
    "corsheaders",
    "linkcheck",
    "mptt",
    "rules.apps.AutodiscoverRulesConfig",
    "webpack_loader",
    "widget_tweaks",
]

# Install cacheops only if redis cache is available
if "DJANGO_REDIS_CACHE" in os.environ:
    INSTALLED_APPS.append("cacheops")

# The default Django Admin application and debug toolbar will only be activated if the system is in debug mode.
if DEBUG:
    INSTALLED_APPS.append("django.contrib.admin")
    # Comment out the following line if you want to disable the Django debug toolbar
    INSTALLED_APPS.append("debug_toolbar")

#: Activated middlewares (see :setting:`django:MIDDLEWARE`)
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "integreat_cms.cms.middleware.timezone_middleware.TimezoneMiddleware",
]

# The Django debug toolbar middleware will only be activated if the debug_toolbar app is installed
if "debug_toolbar" in INSTALLED_APPS:
    # The debug toolbar middleware should be put first (see :doc:`django-debug-toolbar:installation`)
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

#: Default URL dispatcher (see :setting:`django:ROOT_URLCONF`)
ROOT_URLCONF = "integreat_cms.core.urls"

#: Config for HTML templates (see :setting:`django:TEMPLATES`)
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "integreat_cms.core.context_processors.region_slug_processor",
            ],
            "debug": DEBUG,
        },
    },
]

#: WSGI (Web Server Gateway Interface) config (see :setting:`django:WSGI_APPLICATION`)
WSGI_APPLICATION = "integreat_cms.core.wsgi.application"


############
# DATABASE #
############

if (
    "DJANGO_DB_HOST" in os.environ
    and "DJANGO_DB_NAME" in os.environ
    and "DJANGO_DB_PASSWORD" in os.environ
    and "DJANGO_DB_USER" in os.environ
    and "DJANGO_DB_PORT" in os.environ
):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.environ["DJANGO_DB_NAME"],
            "USER": os.environ["DJANGO_DB_USER"],
            "PASSWORD": os.environ["DJANGO_DB_PASSWORD"],
            "HOST": os.environ["DJANGO_DB_HOST"],
            "PORT": os.environ["DJANGO_DB_PORT"],
        }
    }
else:
    #: A dictionary containing the settings for all databases to be used with this Django installation
    #: (see :setting:`django:DATABASES`)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "integreat",
            "USER": "integreat",
            "PASSWORD": "password",
            "HOST": "localhost",
            "PORT": "5432",
        }
    }

#: Directory for initial database contents (see :setting:`django:FIXTURE_DIRS`)
FIXTURE_DIRS = (os.path.join(BASE_DIR, "integreat_cms.cms/fixtures/"),)

#: Default primary key field type to use for models that don’t have a field with
#: :attr:`primary_key=True <django.db.models.Field.primary_key>`. (see :setting:`django:DEFAULT_AUTO_FIELD`)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


############
# SECURITY #
############

if "DJANGO_BASE_URL" in os.environ:
    ALLOWED_HOSTS = [urllib.parse.urlparse(os.environ["DJANGO_BASE_URL"]).netloc]
else:
    #: This is a security measure to prevent HTTP Host header attacks, which are possible even under many seemingly-safe
    #: web server configurations (see :setting:`django:ALLOWED_HOSTS` and :ref:`django:host-headers-virtual-hosting`)
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

#: A list of IP addresses, as strings, that allow the :func:`~django.template.context_processors.debug` context
#: processor to add some variables to the template context.
INTERNAL_IPS = ["localhost", "127.0.0.1"]

if "DJANGO_SECRET_KEY" in os.environ:
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
else:
    #: The secret key for this particular Django installation (see :setting:`django:SECRET_KEY`)
    #:
    #: .. warning::
    #:     Change the key in production and keep it secret!
    SECRET_KEY = "-!v282$zj815_q@htaxcubylo)(l%a+k*-xi78hw*#s2@i86@_"

#: A dotted path to the view function to be used when an incoming request is rejected by the CSRF protection
#: (see :setting:`django:CSRF_FAILURE_VIEW`)
CSRF_FAILURE_VIEW = "integreat_cms.cms.views.error_handler.csrf_failure"


################
# CORS HEADERS #
################

#: Allow access to all domains by setting the following variable to ``True``
#: (see `django-cors-headers/ <https://pypi.org/project/django-cors-headers/>`__)
CORS_ORIGIN_ALLOW_ALL = True

#: Extend default headers with development header to differentiate dev traffic in statistics
#: (see `django-cors-headers/ <https://pypi.org/project/django-cors-headers/>`__)
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-integreat-development",
]


##################
# AUTHENTICATION #
##################

#: The model to use to represent a User (see :setting:`django:AUTH_USER_MODEL` and :ref:`django:auth-custom-user`)
AUTH_USER_MODEL = "cms.User"

#: A list of authentication backend classes (as strings) to use when attempting to authenticate a user
#: (see :setting:`django:AUTHENTICATION_BACKENDS` and :ref:`django:authentication-backends`)
AUTHENTICATION_BACKENDS = (
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",  # this is default
)

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "integreat_cms.cms.auth.WPBCryptPasswordHasher",
]


#: The list of validators that are used to check the strength of user’s passwords
#: (see :setting:`django:AUTH_PASSWORD_VALIDATORS` and :ref:`django:password-validation`)
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

#: The URL where requests are redirected for login (see :setting:`django:LOGIN_URL`)
LOGIN_URL = "/login"

#: The URL where requests are redirected after login (see :setting:`django:LOGIN_REDIRECT_URL`)
LOGIN_REDIRECT_URL = "/"

#: The URL where requests are redirected after logout (see :setting:`django:LOGOUT_REDIRECT_URL`)
LOGOUT_REDIRECT_URL = "/login"


###########
# LOGGING #
###########

#: The log level for integreat-cms django apps
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

#: The log level for the syslog
SYS_LOG_LEVEL = "INFO"

#: The log level for dependencies
DEPS_LOG_LEVEL = "INFO" if DEBUG else "WARN"

#: The default location of the logfile
DEFAULT_LOGFILE = "/var/log/integreat-cms.log"

if "DJANGO_LOGFILE" in os.environ and os.access(os.environ["DJANGO_LOGFILE"], os.W_OK):
    LOGFILE = os.environ["DJANGO_LOGFILE"]
elif DEBUG or not os.access(DEFAULT_LOGFILE, os.W_OK):
    #: The file path of the logfile. Needs to be writable by the application.
    #: Defaults to :attr:`~integreat_cms.core.settings.DEFAULT_LOGFILE`.
    LOGFILE = os.path.join(BASE_DIR, "integreat-cms.log")
else:
    LOGFILE = DEFAULT_LOGFILE

#: Logging configuration dictionary (see :setting:`django:LOGGING`)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "{asctime} \x1b[1m{levelname}\x1b[0m {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
        "console-colored": {
            "()": ColorFormatter,
            "format": "{asctime} {levelname} {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
        "logfile": {
            "format": "{asctime} {levelname:7} {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
        "syslog": {
            "format": "INTEGREAT CMS - {levelname}: {message}",
            "style": "{",
        },
        "email": {
            "format": "Date and time: {asctime}\nSeverity: {levelname}\nLogger: {name}\nMessage: {message}\nFile: {funcName}() in {pathname}:{lineno}",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "console-colored": {
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "console-colored",
        },
        "logfile": {
            "class": "logging.FileHandler",
            "filename": LOGFILE,
            "formatter": "logfile",
        },
        "authlog": {
            "filters": ["require_debug_false"],
            "class": "logging.handlers.SysLogHandler",
            "address": "/dev/log",
            "facility": "auth",
            "formatter": "syslog",
        },
        "syslog": {
            "filters": ["require_debug_false"],
            "class": "logging.handlers.SysLogHandler",
            "address": "/dev/log",
            "facility": "syslog",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "formatter": "email",
        },
    },
    "loggers": {
        # Loggers of integreat-cms django apps
        "integreat_cms.api": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        "integreat_cms.backend": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        "integreat_cms.cms": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        "integreat_cms.gvz_api": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        "integreat_cms.sitemap": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        "integreat_cms.xliff": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        # Syslog for authentication
        "auth": {
            "handlers": ["console", "logfile", "authlog", "syslog"],
            "level": SYS_LOG_LEVEL,
        },
        # Loggers of dependencies
        "aiohttp.client": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "django": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "linkcheck": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "PIL": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "requests": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "rules": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "urllib3": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "xhtml2pdf": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
    },
}


##########
# EMAILS #
##########

if DEBUG:
    #: The backend to use for sending emails (see :setting:`django:EMAIL_BACKEND` and :doc:`django:topics/email`)
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

#: Default email address to use for various automated correspondence from the site manager(s)
#: (see :setting:`django:DEFAULT_FROM_EMAIL`)
DEFAULT_FROM_EMAIL = "keineantwort@integreat-app.de"

#: The email address that error messages come from, such as those sent to :attr:`~integreat_cms.core.settings.ADMINS`.
#: (see :setting:`django:SERVER_EMAIL`)
SERVER_EMAIL = "keineantwort@integreat-app.de"

#: A list of all the people who get code error notifications. When :attr:`~integreat_cms.core.settings.DEBUG` is ``False``,
#: Django emails these people the details of exceptions raised in the request/response cycle.
ADMINS = [("Integreat Helpdesk", "tech@integreat-app.de")]

if "DJANGO_EMAIL_HOST" in os.environ:
    EMAIL_HOST = os.environ["DJANGO_EMAIL_HOST"]
else:
    #: The host to use for sending email.
    EMAIL_HOST = "localhost"

if "DJANGO_EMAIL_HOST_PASSWORD" in os.environ:
    EMAIL_HOST_PASSWORD = os.environ["DJANGO_EMAIL_HOST_PASSWORD"]
else:
    #: Password to use for the SMTP server defined in :attr:`~integreat_cms.core.settings.EMAIL_HOST`.
    #: If empty, Django won’t attempt authentication.
    EMAIL_HOST_PASSWORD = ""

if "DJANGO_EMAIL_HOST_USER" in os.environ:
    EMAIL_HOST_USER = os.environ["DJANGO_EMAIL_HOST_USER"]
else:
    #: Username to use for the SMTP server defined in :attr:`~integreat_cms.core.settings.EMAIL_HOST`.
    #: If empty, Django won’t attempt authentication.
    EMAIL_HOST_USER = ""

if "DJANGO_EMAIL_PORT" in os.environ:
    EMAIL_PORT = os.environ["DJANGO_EMAIL_PORT"]
else:
    #: Port to use for the SMTP server defined in :attr:`~integreat_cms.core.settings.EMAIL_HOST`.
    EMAIL_PORT = 25


########################
# INTERNATIONALIZATION #
########################

#: A list of all available languages (see :setting:`django:LANGUAGES` and :doc:`topics/i18n/index`)
LANGUAGES = (
    ("en", "English"),
    ("de", "Deutsch"),
)

#: A list of directories where Django looks for translation files
#: (see :setting:`django:LOCALE_PATHS` and :doc:`topics/i18n/index`)
LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

#: A string representing the language slug for this installation
#: (see :setting:`django:LANGUAGE_CODE` and :doc:`topics/i18n/index`)
LANGUAGE_CODE = "de"

#: A string representing the time zone for this installation
#: (see :setting:`django:TIME_ZONE` and :doc:`topics/i18n/index`)
TIME_ZONE = "UTC"

#: A string representing the time zone that is used for rendering
CURRENT_TIME_ZONE = "Europe/Berlin"

#: A boolean that specifies whether Django’s translation system should be enabled
#: (see :setting:`django:USE_I18N` and :doc:`topics/i18n/index`)
USE_I18N = True

#: A boolean that specifies if localized formatting of data will be enabled by default or not
#: (see :setting:`django:USE_L10N` and :doc:`topics/i18n/index`)
USE_L10N = True

#: A boolean that specifies if datetimes will be timezone-aware by default or not
#: (see :setting:`django:USE_TZ` and :doc:`topics/i18n/index`)
USE_TZ = True


################
# STATIC FILES #
################

#: This setting defines the additional locations the :mod:`django.contrib.staticfiles` app will traverse to collect
#: static files for deployment or to serve them during development (see :setting:`django:STATICFILES_DIRS` and
#: :doc:`Managing static files <django:howto/static-files/index>`).
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static/dist")]

if "DJANGO_STATIC_ROOT" in os.environ:
    STATIC_ROOT = os.environ["DJANGO_STATIC_ROOT"]
else:
    #: The absolute path to the output directory where :mod:`django.contrib.staticfiles` will put static files for
    #: deployment (see :setting:`django:STATIC_ROOT` and :doc:`Managing static files <django:howto/static-files/index>`)
    #: In debug mode, this is not required since :mod:`django.contrib.staticfiles` can directly serve these files.
    STATIC_ROOT = None

#: URL to use in development when referring to static files located in :setting:`STATICFILES_DIRS`
#: (see :setting:`django:STATIC_URL` and :doc:`Managing static files <django:howto/static-files/index>`)
STATIC_URL = "/static/"

#: The list of finder backends that know how to find static files in various locations
#: (see :setting:`django:STATICFILES_FINDERS`)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)


#################
# MEDIA LIBRARY #
#################

#: URL that handles the media served from :setting:`MEDIA_ROOT` (see :setting:`django:MEDIA_URL`)
MEDIA_URL = "/media/"

if "DJANGO_MEDIA_ROOT" in os.environ:
    MEDIA_ROOT = os.environ["DJANGO_MEDIA_ROOT"]
else:
    #: Absolute filesystem path to the directory that will hold user-uploaded files (see :setting:`django:MEDIA_ROOT`)
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

#: The maximum size of media thumbnails in pixels
MEDIA_THUMBNAIL_SIZE = 300

#: Whether thumbnails should be cropped (resulting in square thumbnails regardless of the aspect ratio of the image)
MEDIA_THUMBNAIL_CROP = False

#: Enables the possibility to upload further file formats (e.g. DOC, GIF).
LEGACY_FILE_UPLOAD = False


#########
# CACHE #
#########

#: Configuration for caches (see :setting:`django:CACHES` and :doc:`django:topics/cache`).
#: Use a ``LocMemCache`` for development and a ``RedisCache`` whenever available.
#: Additionally, a ``FileBasedCache`` is used for PDF caching.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "pdf": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(BASE_DIR, "cache/pdf"),
    },
}

# Use RedisCache when activated
if os.getenv("DJANGO_REDIS_CACHE"):
    unix_socket = os.getenv("DJANGO_REDIS_UNIX_SOCKET")
    if unix_socket:
        # Use unix socket if available (and also tell cacheops about it)
        redis_location = CACHEOPS_REDIS = f"unix://{unix_socket}?db=1"
    else:
        # If not, fall back to normal TCP connection
        redis_location = "redis://127.0.0.1:6379/1"
    CACHES["default"] = {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": redis_location,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # Don't throw exceptions when redis is not available
        },
    }

#: Default cache timeout for cacheops
CACHEOPS_DEFAULTS = {"timeout": 60 * 60}

#: Which database tables should be cached
CACHEOPS = {
    "auth.*": {"ops": "all"},
    "cms.*": {"ops": "all"},
    "linkcheck.*": {"ops": "all"},
    "*.*": {},
}

#: Degrade gracefully on redis fail
CACHEOPS_DEGRADE_ON_FAILURE = True


##############
# PAGINATION #
##############

#: Number of entries displayed per pagination chunk
#: see :class:`~django.core.paginator.Paginator`
PER_PAGE = 16


####################
# DJANGO LINKCHECK #
####################

#: Disable linkcheck listeners e.g. when the fixtures are loaded
if "LINKCHECK_DISABLE_LISTENERS" in os.environ:
    LINKCHECK_DISABLE_LISTENERS = True


#############################
# Push Notification Channel #
#############################

#: The available push notification channels
CHANNELS = (("News", "News"),)


#########################
# DJANGO WEBPACK LOADER #
#########################

#: Overwrite default bundle directory
WEBPACK_LOADER = {
    "DEFAULT": {
        "BUNDLE_DIR_NAME": "",
        "STATS_FILE": os.path.join(BASE_DIR, "webpack-stats.json"),
    }
}


########################
# DJANGO DEBUG TOOLBAR #
########################

#: This setting specifies the full Python path to each panel that you want included in the toolbar.
#:  (see :doc:`django-debug-toolbar:configuration`)
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
]


#######################
# XLIFF SERIALIZATION #
#######################

#: A dictionary of modules containing serializer definitions (provided as strings),
#: keyed by a string identifier for that serialization type (see :setting:`django:SERIALIZATION_MODULES`).
SERIALIZATION_MODULES = {
    "xliff": "integreat_cms.xliff.generic_serializer",
    "xliff-1.2": "integreat_cms.xliff.xliff1_serializer",
    "xliff-2.0": "integreat_cms.xliff.xliff2_serializer",
}

#: The xliff version to be used for exports
XLIFF_EXPORT_VERSION = "xliff-1.2"

#: The default fields to be used for the XLIFF serialization
XLIFF_DEFAULT_FIELDS = ("title", "text")

#: A mapping for changed field names to preserve backward compatibility after a database field was renamed
XLIFF_LEGACY_FIELDS = {"body": "text"}

if "DJANGO_XLIFF_ROOT" in os.environ:
    XLIFF_ROOT = os.environ["DJANGO_XLIFF_ROOT"]
else:
    #: The directory where xliff files are stored
    XLIFF_ROOT = os.path.join(BASE_DIR, "xliff")

#: The directory to which xliff files should be uploaded (this should not be reachable by the webserver)
XLIFF_UPLOAD_DIR = os.path.join(XLIFF_ROOT, "upload")

#: The directory from which xliff files can be downloaded (this should be publicly available under the url specified in
#: :attr:`~integreat_cms.core.settings.XLIFF_URL`)
XLIFF_DOWNLOAD_DIR = os.path.join(XLIFF_ROOT, "download")

#: The URL path where XLIFF files are served for download
XLIFF_URL = "/xliff/"
