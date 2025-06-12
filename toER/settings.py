"""
Configurazioni Django per il progetto toER.

Questo file contiene tutte le configurazioni principali del progetto,
incluse le impostazioni per il database, le applicazioni installate,
e le configurazioni di sicurezza.

Struttura delle configurazioni:
1. Impostazioni di base e sicurezza
2. Applicazioni installate e middleware
3. Configurazioni di autenticazione e template
4. Database e validazione password
5. Internazionalizzazione
6. File statici e media
"""

import os
from pathlib import Path

# Directory base del progetto - punto di riferimento per tutti i percorsi
BASE_DIR = Path(__file__).resolve().parent.parent

# Configurazioni di sicurezza

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-*n&o0$06mt)oqq_u^1w2khlx1x0b5f2xbsd(i-5sf!(ezyl#09'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Host consentiti - da configurare in produzione
ALLOWED_HOSTS = []

# Applicazioni Django installate
INSTALLED_APPS = [
    # App di sistema Django
    'django.contrib.admin',          # Interfaccia di amministrazione
    'django.contrib.auth',           # Sistema di autenticazione
    'django.contrib.contenttypes',   # Framework per i tipi di contenuto
    'django.contrib.sessions',       # Framework per le sessioni
    'django.contrib.messages',       # Framework per i messaggi
    'django.contrib.staticfiles',    # Gestione file statici
    
    # Librerie di terze parti
    'crispy_forms',                  # Miglioramento rendering dei form
    'crispy_bootstrap5',             # Tema Bootstrap 5 per i form
    
    # App personalizzate del progetto
    'account',                       # Gestione utenti e strutture
    'ricerca',                       # Ricerca strutture
    'prenotazioni',                  # Gestione prenotazioni
]

# Configurazioni per il rendering dei form con crispy-forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"  # Tema consentito
CRISPY_TEMPLATE_PACK = "bootstrap5"           # Tema predefinito

# Configurazioni per l'autenticazione personalizzata
AUTH_USER_MODEL = 'account.User'              # Modello utente personalizzato
LOGIN_URL = 'account:login'                   # URL per il login
LOGIN_REDIRECT_URL = 'home'                   # Redirect dopo il login
LOGOUT_REDIRECT_URL = 'home'                  # Redirect dopo il logout

# Middleware - componenti che processano le richieste/risposte
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',         # Sicurezza
    'django.contrib.sessions.middleware.SessionMiddleware',  # Gestione sessioni
    'django.middleware.common.CommonMiddleware',            # Funzionalità comuni
    'django.middleware.csrf.CsrfViewMiddleware',            # Protezione CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Autenticazione
    'django.contrib.messages.middleware.MessageMiddleware',    # Messaggi
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Protezione clickjacking
]

# Configurazione URL principale
ROOT_URLCONF = 'toER.urls'

# Sistema di template
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Engine Django
        'DIRS': [BASE_DIR / 'toER/templates'],  # Directory template progetto
        'APP_DIRS': True,  # Cerca template nelle app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',    # Variabili debug
                'django.template.context_processors.request',  # Oggetto request
                'django.contrib.auth.context_processors.auth', # Dati autenticazione
                'django.contrib.messages.context_processors.messages',  # Messaggi
            ],
        },
    },
]

# Configurazione WSGI per il deployment
WSGI_APPLICATION = 'toER.wsgi.application'

# Configurazione sistema messaggi
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Configurazione email (modalità sviluppo - visualizza email nella console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' 

# Database - SQLite per sviluppo
# In produzione considerare PostgreSQL o MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Validatori password - regole per password sicure
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  # No dati utente
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  # Lunghezza minima
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # No password comuni
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # No solo numeri
    },
]

# Configurazioni internazionalizzazione
LANGUAGE_CODE = 'it-it'     # Lingua italiana
TIME_ZONE = 'Europe/Rome'   # Fuso orario italiano
USE_I18N = True            # Attiva traduzione
USE_TZ = True             # Gestione fusi orari

# Configurazione file statici (CSS, JavaScript, immagini)
STATIC_URL = 'static/'    # URL base per i file statici

# Configurazione file media (upload utenti)
MEDIA_URL = '/media/'     # URL base per i file media
MEDIA_ROOT = BASE_DIR / 'media'  # Directory fisica per i file media

# Tipo di chiave primaria predefinito per i modelli
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'  # Supporta grandi numeri di record
