from django.apps import AppConfig

"""
Configurazione dell'applicazione Django 'prenotazioni'.
Questo file definisce le impostazioni base dell'app, come il tipo di campo ID
automatico da utilizzare e il nome dell'applicazione nel sistema.
"""

class PrenotazioniConfig(AppConfig):
    """
    Classe di configurazione per l'app prenotazioni.
    
    Attributi:
    - default_auto_field: Tipo di campo utilizzato per le chiavi primarie automatiche
    - name: Nome dell'applicazione nel sistema Django
    """
    default_auto_field = 'django.db.models.BigAutoField'  # Usa BigAutoField per supportare un numero maggiore di record
    name = 'prenotazioni'  # Nome dell'applicazione
