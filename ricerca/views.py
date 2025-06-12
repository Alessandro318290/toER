from django.shortcuts import render, redirect
from django.http import JsonResponse
from account.models import Struttura
from django.contrib import messages
from django.db.models import Q
from account.forms import StrutturaFilterForm

"""
Modulo delle viste per la funzionalità di ricerca strutture.
Implementa la ricerca avanzata delle strutture ricettive con filtri
e l'autocompletamento per la ricerca rapida.
"""

def ricerca_strutture(request):
    """
    Vista principale per la ricerca delle strutture ricettive.
    
    Funzionalità:
    - Ricerca per città o nome struttura
    - Filtro per numero di persone
    - Filtri avanzati (tipologia, servizi, etc.)
    - Ordinamento risultati
    
    Limitazioni:
    - Non accessibile agli account gestore
    - Richiede almeno un criterio di ricerca
    """
    # Blocca la ricerca ai gestori per evitare conflitti di interesse
    if request.user.is_authenticated and hasattr(request.user, 'user_type') and request.user.user_type == "GESTORE":
        messages.error(request, "Gli account gestore non possono effettuare ricerche.")
        return redirect('account:dashboard_gestore')

    # Inizializza il form dei filtri con i dati della richiesta GET
    filter_form = StrutturaFilterForm(request.GET)
    strutture = Struttura.objects.all()
    
    # Estrae i parametri di base dalla query string
    citta = request.GET.get('citta')
    num_people = request.GET.get('num_people')
    check_in_date = request.GET.get('check_in_date')
    check_out_date = request.GET.get('check_out_date')

    # Applica i filtri di base
    if num_people:
        # Filtra strutture con camere disponibili per il numero di persone richiesto
        strutture = strutture.filter(camere__disponibilita=True, camere__numero_persone__gte=num_people).distinct()
    
    if citta:
        # Ricerca per corrispondenza parziale su nome struttura o città
        strutture = strutture.filter(Q(nome__icontains=citta) | Q(citta__icontains=citta))

    # Applica i filtri avanzati se il form è valido
    if filter_form.is_valid():
        # Ricerca per nome o città (se non già filtrato dal parametro citta)
        if filter_form.cleaned_data['search'] and not citta:
            search_query = filter_form.cleaned_data['search']
            strutture = strutture.filter(
                Q(nome__icontains=search_query) | 
                Q(citta__icontains=search_query)
            )
        
        # Filtro per tipologia di struttura (hotel, B&B, etc.)
        if filter_form.cleaned_data['tipologia']:
            strutture = strutture.filter(tipologia__in=filter_form.cleaned_data['tipologia'])
        
        # Filtri per servizi disponibili
        if filter_form.cleaned_data['parcheggio']:
            strutture = strutture.filter(parcheggio=True)
        if filter_form.cleaned_data['piscina']:
            strutture = strutture.filter(piscina=True)
        if filter_form.cleaned_data['ristorante']:
            strutture = strutture.filter(ristorante=True)
        if filter_form.cleaned_data['animali_ammessi']:
            strutture = strutture.filter(animali_ammessi=True)
        
        # Applica l'ordinamento selezionato
        if filter_form.cleaned_data['ordina_per']:
            strutture = strutture.order_by(filter_form.cleaned_data['ordina_per'])
            
    # Prepara il contesto per il template
    context = {
        'strutture': strutture,
        'filter_form': filter_form,
        'citta': citta,
        'num_people': num_people,
        'check_in_date': check_in_date,
        'check_out_date': check_out_date,
    }
    return render(request, 'ricerca/risultati.html', context)

def autocomplete_strutture(request):
    """
    API per l'autocompletamento nella ricerca strutture.
    
    Funzionalità:
    - Ricerca in tempo reale mentre l'utente digita
    - Suggerisce sia strutture che città
    - Evita duplicati nelle città suggerite
    
    Parametri:
    - term: stringa di ricerca (min. 2 caratteri)
    
    Risposta:
    JSON con array di risultati, ogni risultato contiene:
    - id: identificativo struttura o città
    - nome: nome della struttura (vuoto per città)
    - citta: nome della città
    - type: 'struttura' o 'city'
    - display_text: testo da mostrare nel suggerimento
    """
    # Ottiene il termine di ricerca dalla query string
    term = request.GET.get('term', '').strip()
    
    # Richiede almeno 2 caratteri per iniziare la ricerca
    if len(term) < 2:
        return JsonResponse([], safe=False)
    
    # Cerca strutture che corrispondono al termine (max 10 risultati)
    strutture = Struttura.objects.filter(
        Q(nome__icontains=term) | Q(citta__icontains=term)
    ).distinct()[:10]
    
    results = []
    cities_added = set()  # Set per tenere traccia delle città già aggiunte
    
    for struttura in strutture:
        # Aggiunge la struttura ai risultati
        results.append({
            'id': struttura.id,
            'nome': struttura.nome,
            'citta': struttura.citta,
            'type': 'struttura',
            'display_text': f"{struttura.nome} - {struttura.citta}"
        })
        
        # Aggiunge la città ai risultati se non già presente e se corrisponde al termine
        if struttura.citta not in cities_added and term.lower() in struttura.citta.lower():
            results.append({
                'nome': '',
                'id': f"city_{struttura.citta}",
                'citta': struttura.citta,
                'type': 'city',
                'display_text': struttura.citta
            })
            cities_added.add(struttura.citta)
    
    return JsonResponse(results, safe=False)