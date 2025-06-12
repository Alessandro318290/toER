from django.urls import path
from . import views

"""
Configurazione delle URL per l'app ricerca.
Definisce i percorsi per la ricerca delle strutture e l'autocompletamento.
"""

app_name = 'ricerca'  # Namespace dell'applicazione per evitare conflitti di nomi

urlpatterns = [
    # URL principale per la ricerca delle strutture
    path('', views.ricerca_strutture, name='ricerca_strutture'),  # Gestisce la ricerca e i filtri
    
    # Endpoint API per l'autocompletamento
    path('autocomplete/', views.autocomplete_strutture, name='autocomplete_strutture'),  # Fornisce suggerimenti in tempo reale
]