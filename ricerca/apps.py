from django.apps import AppConfig

"""
Configurazione dell'applicazione Django 'ricerca'.
Gestisce le impostazioni di base dell'app dedicata alla ricerca
delle strutture ricettive nel sistema.
"""

class RicercaConfig(AppConfig):
    """
    Classe di configurazione per l'app ricerca.
    
    Funzionalità principali dell'app:
    - Ricerca avanzata delle strutture
    - Filtri personalizzati
    - Autocompletamento
    """
    default_auto_field = 'django.db.models.BigAutoField'  # Tipo di campo ID automatico
    name = 'ricerca'  # Nome dell'applicazione nel sistema Django
