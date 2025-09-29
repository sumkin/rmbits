# Django settings for webgui project.


DEBUG = True
TEMPLATE_DEBUG = DEBUG


import os.path
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

db_server = config.get('OR_DB','server')
db_port   = config.get('OR_DB','port')
db_user   = config.get('OR_DB','user')
db_pass   = config.get('OR_DB','pass')
db_name   = config.get('OR_DB','name')

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': db_name,                       # Or path to database file if using sqlite3.
        'USER': db_user,                       # Not used with sqlite3.
        'PASSWORD': db_pass,                   # Not used with sqlite3.
        'HOST': db_server,                     # Set to empty string for localhost. Not used with sqlite3.
        'PORT': db_port,                       # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/home/rmpuser/rw.data/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

STATIC_ROOT = '/home/rmpuser/rw.static'

STATIC_URL = '/static/'

STATICFILES_DIRS = {
  '/home/rmpuser/rw.static',
}

STATICFILES_FINDERS = {
  'django.contrib.staticfiles.finders.FileSystemFinder',
  'django.contrib.staticfiles.finders.AppDirectoriesFinder',
}

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

#AUTOCOMPLETE_MEDIA_PREFIX = '/media/autocomplete/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '*g4#=%a0qz80@pz(7tkm*rxzglih8=^_d5=$9te_(puv2y6@&f'

CRISPY_TEMPLATE_PACK = 'bootstrap'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = ('django.core.context_processors.csrf',
                               'django.contrib.auth.context_processors.auth',
                               'django.core.context_processors.debug',
                               'django.core.context_processors.i18n',
                               'django.core.context_processors.media',
                               'django.contrib.messages.context_processors.messages')

MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    config.get('PATHS','django_tmpl') #"C:/rw_root/rw_src/src/webgui/templates"
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    'demand_shift',
    'radata',
    'sigod',
    'crispy_forms',
    #'webgui.southtut',
    #'south',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)




