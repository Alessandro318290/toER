"""
Views principali del progetto toER.

Questo file contiene le views di base del progetto, in particolare la homepage.
Le altre funzionalità specifiche sono gestite nelle rispettive app:
- account: gestione utenti e strutture
- ricerca: ricerca e filtro strutture
- prenotazioni: gestione prenotazioni
"""

from django.shortcuts import render

def home(request):
    """
    View per la homepage del sito.
    
    Questa vista è il punto di ingresso principale del sito e:
    - Fornisce una panoramica del servizio
    - Mostra i principali punti di accesso (ricerca, login, etc.)
    - Presenta le caratteristiche principali del portale
    
    Template: home.html
    Context:
    - title: Titolo della pagina
    - description: Breve descrizione del progetto
    """
    context = {
        'title': 'Benvenuto su toER',  # Titolo principale della pagina
        'description': 'Il tuo portale per scoprire e prenotare le attrazioni turistiche dell\'Emilia-Romagna'  # Descrizione del servizio
    }
    return render(request, 'home.html', context)  # Renderizza il template con il contesto