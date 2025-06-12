from django.urls import path
from . import views

"""
Configurazione delle URL per l'app prenotazioni.
Definisce tutti i percorsi disponibili per la gestione delle prenotazioni,
inclusi quelli per la lista d'attesa e le funzionalità del gestore.
"""

app_name = 'prenotazioni'  # Namespace dell'applicazione per evitare conflitti di nomi

urlpatterns = [
    # URLs per la gestione delle prenotazioni base
    path('', views.lista_prenotazioni, name='lista_prenotazioni'),  # Homepage prenotazioni
    path('nuova/', views.nuova_prenotazione, name='nuova_prenotazione'),  # Creazione nuova prenotazione
    path('modifica/<int:pk>/', views.modifica_prenotazione, name='modifica_prenotazione'),  # Modifica prenotazione esistente
    path('cancella/<int:pk>/', views.cancella_prenotazione, name='cancella_prenotazione'),  # Cancellazione prenotazione
    
    # URLs per funzionalità del gestore
    path('gestisci/<int:pk>/', views.gestisci_prenotazione, name='gestisci_prenotazione'),  # Gestione stato prenotazione (approva/rifiuta/check-in/check-out)
    path('dashboard/prenotazioni/gestore/', views.prenotazioni_gestore, name='prenotazioni_gestore'),  # Dashboard gestore
    
    # URLs per la gestione della lista d'attesa
    path('lista-attesa/', views.waiting_list, name='waiting_list'),  # Visualizzazione lista d'attesa
    path('lista-attesa/aggiungi/<int:camera_id>/', views.add_to_waiting_list, name='add_to_waiting_list'),  # Aggiunta alla lista d'attesa
    path('lista-attesa/rimuovi/<int:pk>/', views.rimuovi_lista_attesa, name='rimuovi_lista_attesa'),  # Rimozione dalla lista d'attesa
    
    # URLs per la gestione delle notifiche
    path('notifica/letta/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),  # Segna notifica come letta
] 