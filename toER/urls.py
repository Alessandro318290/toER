"""
Configurazione degli URL principali del progetto toER.

Questo file definisce i pattern URL principali del progetto, inclusi:
- URL amministrazione
- Homepage
- URL delle varie applicazioni (ricerca, account, prenotazioni)

Struttura URL:
- /admin/: Interfaccia di amministrazione Django
- /: Homepage del sito
- /ricerca/: Funzionalità di ricerca strutture
- /account/: Gestione utenti e autenticazione
- /prenotazioni/: Gestione prenotazioni
"""

from django.contrib import admin
from django.urls import path, include
from .views import home  # Vista homepage
from django.conf import settings
from django.conf.urls.static import static  # Per servire file media in sviluppo

urlpatterns = [
    # Interfaccia di amministrazione Django
    # Accessibile solo agli amministratori del sito
    path('admin/', admin.site.urls),
    
    # Homepage del sito
    # Vista principale che mostra la pagina di benvenuto
    path('', home, name='home'),
    
    # URL delle applicazioni del progetto
    # Ogni app ha il suo namespace per evitare conflitti di nomi
    path('ricerca/', include('ricerca.urls', namespace='ricerca')),  # Gestione ricerca strutture
    path('account/', include('account.urls', namespace='account')),  # Gestione utenti e profili
    path('prenotazioni/', include('prenotazioni.urls')),  # Gestione prenotazioni
]

# Configurazione per servire i file media in sviluppo
# NOTA: In produzione, i file media dovrebbero essere serviti da un web server
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

