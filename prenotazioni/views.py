from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Booking, WaitingList, Notification
from .forms import BookingForm
from django.utils import timezone
from account.models import Camera, User
from django.conf import settings
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError

"""
Questo modulo contiene tutte le viste (views) relative alla gestione delle prenotazioni.
Include funzionalità per:
- Creazione, modifica e cancellazione di prenotazioni
- Gestione della lista d'attesa
- Gestione delle notifiche
- Funzionalità specifiche per i gestori (approvazione, check-in, check-out)
"""

@login_required
def lista_prenotazioni(request):
    """
    Mostra la lista delle prenotazioni.
    Per i gestori: mostra le prenotazioni relative alle loro strutture
    Per i clienti: mostra solo le loro prenotazioni personali
    Include anche la lista d'attesa dell'utente
    """
    if hasattr(request.user, 'gestore'):
        # Se l'utente è un gestore, mostra le prenotazioni delle sue strutture
        prenotazioni = Booking.objects.filter(
            camera__struttura__gestore=request.user
        ).order_by('-check_in_date')
    else:
        # Se l'utente è un cliente, mostra solo le sue prenotazioni
        prenotazioni = Booking.objects.filter(user=request.user).order_by('-check_in_date')
    
    # Recupera anche le prenotazioni in lista d'attesa
    waiting_list = WaitingList.objects.filter(user=request.user, notified=False).order_by('date')
    
    return render(request, 'prenotazioni/lista_prenotazioni.html', {
        'prenotazioni': prenotazioni,
        'waiting_list': waiting_list
    })

@login_required
def nuova_prenotazione(request):
    """
    Gestisce la creazione di una nuova prenotazione.
    
    Processo:
    1. Verifica i parametri di input (camera, date, numero persone)
    2. Controlla la disponibilità della camera
    3. Verifica eventuali sovrapposizioni con altre prenotazioni
    4. Se la camera non è disponibile, offre l'opzione di mettersi in lista d'attesa
    5. Gestisce la creazione della prenotazione in modo atomico per evitare race conditions
    
    Parametri GET richiesti:
    - camera: ID della camera
    - check_in_date: Data di check-in (YYYY-MM-DD)
    - check_out_date: Data di check-out (YYYY-MM-DD)
    - num_people: Numero di persone
    """
    camera_id = request.GET.get('camera')
    check_in_date = request.GET.get('check_in_date')
    check_out_date = request.GET.get('check_out_date')
    num_people = request.GET.get('num_people')

    # Verifica che tutti i parametri necessari siano presenti
    if not all([camera_id, check_in_date, check_out_date, num_people]):
        messages.error(request, f'Parametri mancanti: camera={camera_id}, check_in_date={check_in_date}, check_out_date={check_out_date}, num_people={num_people}')
        return redirect('home')
    
    try:
        camera = get_object_or_404(Camera, id=camera_id)
        num_people = int(num_people)
        
        # Converti le date da stringa a oggetto date
        try:
            from datetime import datetime
            check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, f'Formato data non valido. Usa il formato YYYY-MM-DD')
            return redirect('home')
        
        # Verifica che il numero di persone non superi la capacità della camera
        if num_people > camera.numero_persone:
            messages.error(request, f'Questa camera può ospitare al massimo {camera.numero_persone} persone.')
            return redirect('home')
        
        # Verifica se l'utente ha già prenotazioni sovrapposte
        if Booking.objects.filter(
            user=request.user,
            check_in_date__lte=check_out,
            check_out_date__gte=check_in,
            status__in=['pending', 'approved', 'checked_in']
        ).exists():
            messages.error(request, 'Hai già una prenotazione che si sovrappone a queste date!')
            return redirect('home')
        
        # Verifica se la camera è già prenotata per quelle date
        if Booking.objects.filter(
            camera=camera,
            check_in_date__lte=check_out,
            check_out_date__gte=check_in,
            status__in=['pending', 'approved', 'checked_in']
        ).exists():
            # Offri la possibilità di mettersi in lista d'attesa
            if request.method == 'POST' and request.POST.get('waiting_list'):
                WaitingList.objects.get_or_create(
                    user=request.user,
                    camera=camera,
                    date=check_in,  # Usiamo la data di check-in per la lista d'attesa
                    num_people=num_people
                )
                messages.success(request, 'Sei stato aggiunto alla lista d\'attesa!')
                return redirect('prenotazioni:lista_prenotazioni')
            
            return render(request, 'prenotazioni/camera_non_disponibile.html', {
                'camera': camera,
                'check_in_date': check_in,
                'check_out_date': check_out,
                'num_people': num_people
            })
        
        # Gestione del form di prenotazione
        if request.method == 'POST':
            form = BookingForm(request.POST)
            if form.is_valid():
                try:
                    # Utilizzo di una transazione atomica per evitare race conditions
                    with transaction.atomic():
                        # Blocca la camera per evitare prenotazioni simultanee
                        camera = Camera.objects.select_for_update().get(id=camera_id)
                        
                        # Ricontrolliamo la disponibilità all'interno della transazione con il lock
                        if Booking.objects.filter(
                            camera=camera,
                            check_in_date__lte=check_out,
                            check_out_date__gte=check_in,
                            status__in=['pending', 'approved', 'checked_in']
                        ).exists():
                            messages.error(request, 'Questa camera è stata appena prenotata da un altro utente!')
                            return redirect('home')
                        
                        # Crea e salva la prenotazione
                        prenotazione = form.save(commit=False)
                        prenotazione.user = request.user
                        prenotazione.camera = camera
                        prenotazione.check_in_date = check_in
                        prenotazione.check_out_date = check_out
                        prenotazione.num_people = num_people
                        prenotazione.save()
                        
                        messages.success(request, 'Prenotazione creata con successo! In attesa di approvazione dal gestore.')
                        return redirect('prenotazioni:lista_prenotazioni')
                except ValidationError as e:
                    messages.error(request, str(e))
                    return redirect('home')
                except Exception as e:
                    messages.error(request, f'Si è verificato un errore durante la prenotazione: {str(e)}')
                    return redirect('home')
        else:
            # Inizializza il form con i dati della richiesta
            initial_data = {
                'camera': camera.id,
                'check_in_date': check_in,
                'check_out_date': check_out,
                'num_people': num_people
            }
            form = BookingForm(initial=initial_data)
        
        return render(request, 'prenotazioni/form_prenotazione.html', {
            'form': form,
            'titolo': f'Nuova Prenotazione - Camera {camera.numero_camera} ({camera.struttura.nome})',
            'camera': camera
        })
    except ValueError as e:
        messages.error(request, f'Parametri non validi: {str(e)}')
        return redirect('home')
    except Camera.DoesNotExist:
        messages.error(request, f'Camera non trovata.')
        return redirect('home')
    except Exception as e:
        messages.error(request, f'Errore imprevisto: {str(e)}')
        return redirect('home')

@login_required
def modifica_prenotazione(request, pk):
    """
    Permette la modifica di una prenotazione esistente.
    
    Limitazioni:
    - Solo le prenotazioni in stato 'pending' o 'approved' possono essere modificate
    - Le nuove date devono essere disponibili
    - Solo l'utente proprietario può modificare la prenotazione
    """
    prenotazione = get_object_or_404(Booking, pk=pk, user=request.user)
    
    # Verifica se la prenotazione può essere modificata
    if prenotazione.status in ['checked_in', 'checked_out', 'cancelled']:
        messages.error(request, 'Non puoi modificare questa prenotazione!')
        return redirect('prenotazioni:lista_prenotazioni')
    
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=prenotazione)
        if form.is_valid():
            # Verifica se le nuove date sono disponibili
            nuova_prenotazione = form.save(commit=False)
            if nuova_prenotazione.is_available():
                nuova_prenotazione.save()
                messages.success(request, 'Prenotazione modificata con successo!')
                return redirect('prenotazioni:lista_prenotazioni')
            else:
                messages.error(request, 'Le nuove date non sono disponibili!')
    else:
        form = BookingForm(instance=prenotazione)
    
    return render(request, 'prenotazioni/modifica_prenotazione.html', {
        'form': form,
        'prenotazione': prenotazione
    })

@login_required
def rimuovi_lista_attesa(request, pk):
    """
    Rimuove un utente dalla lista d'attesa per una specifica camera e data.
    """
    waiting = get_object_or_404(WaitingList, pk=pk, user=request.user)
    waiting.delete()
    messages.success(request, 'Rimosso dalla lista d\'attesa!')
    return redirect('prenotazioni:lista_prenotazioni')

def is_manager(user):
    """Verifica se l'utente è un gestore"""
    return user.is_gestore()

@login_required
@user_passes_test(is_manager)
def prenotazioni_gestore(request):
    """
    Dashboard per i gestori che mostra:
    - Lista delle prenotazioni filtrabili per stato
    - Statistiche giornaliere (check-in/check-out previsti)
    - Lista d'attesa
    """
    today = timezone.localtime(timezone.now()).date()
    status = request.GET.get('status')
    
    # Filtra le prenotazioni in base allo stato
    prenotazioni = Booking.objects.all().order_by('-check_in_date')
    if status:
        prenotazioni = prenotazioni.filter(status=status)
    
    # Statistiche giornaliere
    stats = {
        'pending': Booking.objects.filter(status='pending').count(),
        'checkin_today': Booking.objects.filter(status='approved', check_in_date=today).count(),
        'checkout_today': Booking.objects.filter(status='checked_in', check_out_date=today).count(),
        'waiting_list': Booking.objects.filter(status='waiting').count(),
    }
    
    # Lista d'attesa
    waiting_list = Booking.objects.filter(status='waiting').order_by('created_at')
    
    context = {
        'prenotazioni': prenotazioni,
        'stats': stats,
        'waiting_list': waiting_list,
        'status': status,
    }
    
    return render(request, 'prenotazioni/prenotazioni_gestore.html', context)

@login_required
@user_passes_test(is_manager)
def gestisci_prenotazione(request, pk):
    """
    Permette ai gestori di:
    - Approvare o rifiutare prenotazioni in attesa
    - Effettuare check-in (solo nel giorno previsto)
    - Effettuare check-out
    
    Le azioni possibili dipendono dallo stato attuale della prenotazione
    e dalle condizioni temporali (es: check-in solo nel giorno previsto)
    """
    prenotazione = get_object_or_404(Booking, id=pk)
    
    if request.method == 'POST':
        azione = request.POST.get('azione')
        
        if azione == 'approva' and prenotazione.status == 'pending':
            prenotazione.status = 'approved'
            messages.success(request, 'Prenotazione approvata con successo.')
            
        elif azione == 'rifiuta' and prenotazione.status == 'pending':
            prenotazione.status = 'rejected'
            messages.success(request, 'Prenotazione rifiutata.')
            
        elif azione == 'check_in' and prenotazione.status == 'approved':
            if prenotazione.check_in_date == timezone.localtime(timezone.now()).date():
                prenotazione.status = 'checked_in'
                prenotazione.actual_check_in = timezone.now()
                messages.success(request, 'Check-in effettuato con successo.')
            else:
                messages.error(request, 'Il check-in può essere effettuato solo il giorno della prenotazione.')
                
        elif azione == 'check_out' and prenotazione.status == 'checked_in':
            prenotazione.status = 'checked_out'
            prenotazione.actual_check_out = timezone.now()
            messages.success(request, 'Check-out effettuato con successo.')
            
        prenotazione.save()
    
    return redirect('prenotazioni:prenotazioni_gestore')

@login_required
def cancella_prenotazione(request, pk):
    """
    Permette la cancellazione di una prenotazione.
    
    Effetti:
    - La prenotazione viene marcata come 'cancelled'
    - Gli utenti in lista d'attesa vengono notificati della disponibilità
    
    Limitazioni:
    - Non si possono cancellare prenotazioni con check-in già effettuato
    - Solo l'utente proprietario può cancellare la prenotazione
    """
    prenotazione = get_object_or_404(Booking, pk=pk, user=request.user)
    
    if not prenotazione.can_be_cancelled():
        messages.error(request, 'Non puoi cancellare questa prenotazione!')
        return redirect('prenotazioni:lista_prenotazioni')
    
    prenotazione.status = 'cancelled'
    prenotazione.save()  # Il signal nel modello gestirà le notifiche alla lista d'attesa
    
    messages.success(request, 'Prenotazione cancellata con successo!')
    return redirect('prenotazioni:lista_prenotazioni')

@login_required
def add_to_waiting_list(request, camera_id):
    """
    Aggiunge un utente alla lista d'attesa per una camera.
    
    La lista d'attesa viene utilizzata quando:
    - La camera desiderata non è disponibile nelle date richieste
    - L'utente vuole essere notificato se la camera diventa disponibile
    """
    camera = get_object_or_404(Camera, id=camera_id)
    check_in_date = request.POST.get('check_in_date')
    num_people = request.POST.get('num_people')
    
    try:
        WaitingList.objects.create(
            user=request.user,
            camera=camera,
            date=check_in_date,
            num_people=num_people
        )
        messages.success(request, 'Aggiunto alla lista d\'attesa con successo!')
    except Exception as e:
        messages.error(request, f'Errore durante l\'aggiunta alla lista d\'attesa: {str(e)}')
    
    return redirect('prenotazioni:lista_prenotazioni')

@login_required
def waiting_list(request):
    """
    Mostra la lista d'attesa dell'utente corrente.
    Include tutte le richieste non ancora notificate.
    """
    waiting_list = WaitingList.objects.filter(
        user=request.user,
        notified=False
    ).order_by('date')
    
    return render(request, 'prenotazioni/waiting_list.html', {
        'waiting_list': waiting_list
    })

@login_required
def mark_notification_as_read(request, notification_id):
    """
    Marca una notifica come letta.
    Utilizzato per gestire le notifiche di disponibilità dalla lista d'attesa.
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.read = True
    notification.save()
    return redirect('prenotazioni:lista_prenotazioni')
