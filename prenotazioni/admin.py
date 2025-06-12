from django.contrib import admin
from .models import Booking, WaitingList, Notification

"""
Configurazione dell'interfaccia di amministrazione Django per l'app prenotazioni.
Definisce come i modelli vengono visualizzati e gestiti nell'area admin.
"""

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Configurazione dell'interfaccia admin per le prenotazioni.
    
    Funzionalità:
    - Lista prenotazioni con informazioni principali
    - Filtri per stato, date e struttura
    - Ricerca per utente, camera e note
    - Organizzazione gerarchica per data di check-in
    """
    list_display = ['user', 'camera', 'check_in_date', 'check_out_date', 'num_people', 'status', 'created_at']  # Colonne visualizzate nella lista
    list_filter = ['status', 'check_in_date', 'check_out_date', 'camera__struttura']  # Filtri laterali
    search_fields = ['user__username', 'user__email', 'camera__numero_camera', 'notes']  # Campi di ricerca
    date_hierarchy = 'check_in_date'  # Navigazione gerarchica per data
    raw_id_fields = ['user', 'camera']  # Selezione utente e camera tramite popup di ricerca

@admin.register(WaitingList)
class WaitingListAdmin(admin.ModelAdmin):
    """
    Configurazione dell'interfaccia admin per la lista d'attesa.
    
    Funzionalità:
    - Lista richieste con dettagli principali
    - Filtri per stato notifica, data e struttura
    - Ricerca per utente e camera
    - Organizzazione gerarchica per data richiesta
    """
    list_display = ['user', 'camera', 'date', 'num_people', 'created_at', 'notified']  # Colonne visualizzate nella lista
    list_filter = ['notified', 'date', 'camera__struttura']  # Filtri laterali
    search_fields = ['user__username', 'user__email', 'camera__numero_camera']  # Campi di ricerca
    date_hierarchy = 'date'  # Navigazione gerarchica per data
    raw_id_fields = ['user', 'camera']  # Selezione utente e camera tramite popup di ricerca

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Configurazione dell'interfaccia admin per le notifiche.
    
    Funzionalità:
    - Lista notifiche con dettagli principali
    - Filtri per stato lettura e data
    - Ricerca per utente e contenuto messaggio
    - Organizzazione gerarchica per data creazione
    """
    list_display = ['user', 'message', 'created_at', 'read']  # Colonne visualizzate nella lista
    list_filter = ['read', 'created_at']  # Filtri laterali
    search_fields = ['user__username', 'user__email', 'message']  # Campi di ricerca
    date_hierarchy = 'created_at'  # Navigazione gerarchica per data
    raw_id_fields = ['user', 'waiting_list']  # Selezione utente e lista d'attesa tramite popup di ricerca
