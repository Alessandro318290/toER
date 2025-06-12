from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.db import transaction
from django.forms import modelformset_factory
from django.db.models import Q

from .models import User, Struttura, Camera
from .forms import StrutturaForm, CameraForm, StrutturaFilterForm, CameraFilterForm
from .forms import (
    LoginForm, 
    GestoreRegistrationForm, 
    ClienteRegistrationForm,
    UserProfileUpdateForm,
    GestoreProfileUpdateForm,
    ClienteProfileUpdateForm
)


class RegisterView(View):
    """Vista per la scelta del tipo di registrazione"""
    template_name = 'account/register_choice.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, self.template_name)


class RegisterGestoreView(View):
    """Vista per la registrazione degli utenti gestori"""
    form_class = GestoreRegistrationForm
    template_name = 'account/register_gestore.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registrazione completata con successo! Benvenuto nel sistema ToER.')
            return redirect('account:dashboard_gestore')
        return render(request, self.template_name, {'form': form})


class RegisterClienteView(View):
    """Vista per la registrazione degli utenti clienti"""
    form_class = ClienteRegistrationForm
    template_name = 'account/register_cliente.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registrazione completata con successo! Benvenuto nel sistema ToER.')
            return redirect('account:dashboard_cliente')
        return render(request, self.template_name, {'form': form})


class LoginView(View):
    """Vista per il login degli utenti"""
    form_class = LoginForm
    template_name = 'account/login.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_gestore():
                return redirect('account:dashboard_gestore')
            else:
                return redirect('account:dashboard_cliente')
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'next': request.GET.get('next', '')
        })

    def post(self, request, *args, **kwargs):
        form = self.form_class(request=request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Hai effettuato l'accesso come {user.email}")
                # Reindirizza alla pagina next se presente, altrimenti alla dashboard appropriata
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                if user.is_gestore():
                    return redirect('account:dashboard_gestore')
                else:
                    return redirect('account:dashboard_cliente')
            else:
                messages.error(request, "Email o password non validi.")
        else:
            messages.error(request, "Email o password non validi.")
        return render(request, self.template_name, {
            'form': form,
            'next': request.POST.get('next', request.GET.get('next', ''))
        })


@login_required
def logout_view(request):
    """Vista per il logout degli utenti"""
    logout(request)
    messages.info(request, "Hai effettuato il logout con successo!")
    return redirect('home')


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    """Vista per visualizzare e aggiornare il profilo dell'utente"""
    template_name = 'account/profile.html'
    profile_update_template = 'account/profile_update.html'
    
    def get(self, request, *args, **kwargs):
        user = request.user
        if 'edit' in request.GET:
            # Preparazione dei form per la modifica del profilo
            user_form = UserProfileUpdateForm(instance=user)
            if user.is_gestore():
                profile_form = GestoreProfileUpdateForm(instance=user.gestore_profile)
            else:
                profile_form = ClienteProfileUpdateForm(instance=user.cliente_profile)
            
            context = {
                'user_form': user_form,
                'profile_form': profile_form,
                'user': user
            }
            return render(request, self.profile_update_template, context)
        else:
            # Visualizzazione del profilo
            context = {'user': user}
            return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        user_form = UserProfileUpdateForm(request.POST, instance=user)
        
        if user.is_gestore():
            profile_form = GestoreProfileUpdateForm(request.POST, instance=user.gestore_profile)
        else:
            profile_form = ClienteProfileUpdateForm(request.POST, instance=user.cliente_profile)
            
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                profile_form.save()
                
            messages.success(request, 'Profilo aggiornato con successo!')
            return redirect('account:profile')
            
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'user': user
        }
        return render(request, self.profile_update_template, context)


# Dashboard per gli utenti registrati
@login_required
def dashboard_gestore(request):
    if not request.user.is_gestore():
        # Se non è gestore, reindirizza o mostra errore
        messages.error(request, "Non hai i permessi per accedere a questa pagina")
        return redirect('home')
    
    # Inizializza il form dei filtri con i dati della richiesta
    filter_form = StrutturaFilterForm(request.GET)
    strutture = request.user.gestore_profile.strutture.prefetch_related('camere').all()
    
    if filter_form.is_valid():
        # Ricerca per nome o città
        if filter_form.cleaned_data['search']:
            search_query = filter_form.cleaned_data['search']
            strutture = strutture.filter(
                Q(nome__icontains=search_query) | 
                Q(citta__icontains=search_query)
            )
        
        # Filtro per tipologia
        if filter_form.cleaned_data['tipologia']:
            strutture = strutture.filter(tipologia__in=filter_form.cleaned_data['tipologia'])
        
        # Filtri booleani
        if filter_form.cleaned_data['parcheggio']:
            strutture = strutture.filter(parcheggio=True)
        if filter_form.cleaned_data['piscina']:
            strutture = strutture.filter(piscina=True)
        if filter_form.cleaned_data['ristorante']:
            strutture = strutture.filter(ristorante=True)
        if filter_form.cleaned_data['animali_ammessi']:
            strutture = strutture.filter(animali_ammessi=True)
        
        # Ordinamento
        if filter_form.cleaned_data['ordina_per']:
            strutture = strutture.order_by(filter_form.cleaned_data['ordina_per'])
    
    # Prepara le informazioni per ogni struttura
    strutture_info = []
    for struttura in strutture:
        camere_disponibili = struttura.camere.filter(disponibilita=True).count()
        camere_non_disponibili = struttura.camere.filter(disponibilita=False).count()
        strutture_info.append({
            'struttura': struttura,
            'camere_disponibili': camere_disponibili,
            'camere_non_disponibili': camere_non_disponibili,
        })
    
    return render(request, 'account/dashboard_gestore.html', {
        'strutture_info': strutture_info,
        'filter_form': filter_form,
    })


@login_required
def dashboard_cliente(request):
    """Dashboard per gli utenti clienti"""
    if not request.user.is_cliente():
        messages.error(request, "Non hai i permessi per accedere a questa pagina")
        return redirect('home')
    return render(request, 'account/dashboard_cliente.html')

@login_required
def aggiungi_struttura(request):
    """Aggiungi una nuova struttura"""
    if request.method == 'POST':
        form = StrutturaForm(request.POST, request.FILES)
        if form.is_valid():
            struttura = form.save(commit=False)
            struttura.gestore = request.user.gestore_profile
            struttura.save()
            return redirect('account:aggiungi_camere', struttura_id=struttura.id)
    else:
        form = StrutturaForm()
    return render(request, 'account/struttura_form.html', {'form': form})

@login_required
def le_mie_strutture(request):
    """Le strutture gestite dall'utente"""
    if not request.user.is_gestore():
        messages.error(request, "Non hai i permessi per accedere a questa pagina")
        return redirect('home')
    strutture = request.user.gestore_profile.strutture.all()
    return render(request, 'account/le_mie_strutture.html', {'strutture': strutture})

@login_required
def aggiungi_camere(request, struttura_id):
    struttura = get_object_or_404(Struttura, id=struttura_id, gestore=request.user.gestore_profile)
    num_camere = struttura.numero_camere if hasattr(struttura, 'numero_camere') else 1
    CameraFormSet = modelformset_factory(Camera, form=CameraForm, extra=num_camere)
    if request.method == 'POST':
        formset = CameraFormSet(request.POST, request.FILES, queryset=Camera.objects.none())
        if formset.is_valid():
            for camera_form in formset:
                if camera_form.cleaned_data:
                    camera = camera_form.save(commit=False)
                    camera.struttura = struttura
                    camera.save()
            messages.success(request, "Camere aggiunte con successo!")
            return redirect('account:dashboard_gestore')
    else:
        formset = CameraFormSet(queryset=Camera.objects.none())
    return render(request, 'account/camera_form.html', {'formset': formset, 'struttura': struttura})

@login_required
def dettaglio_struttura(request, pk):
    struttura = get_object_or_404(Struttura, pk=pk)
    camere = struttura.camere.all()
    return render(request, 'account/dettaglio_struttura.html', {
        'struttura': struttura,
        'camere': camere,
    })

def modifica_struttura(request, pk):
    struttura = get_object_or_404(Struttura, pk=pk)
    if request.method == 'POST':
        form = StrutturaForm(request.POST, request.FILES, instance=struttura)
        if form.is_valid():
            form.save()
            return redirect('account:dettaglio_struttura', pk=pk)
    else:
        form = StrutturaForm(instance=struttura)
    return render(request, 'account/modifica_struttura.html', {'form': form, 'struttura': struttura})

def modifica_camera(request, pk):
    camera = get_object_or_404(Camera, pk=pk)
    if request.method == 'POST':
        form = CameraForm(request.POST, request.FILES, instance=camera)
        if form.is_valid():
            form.save()
            return redirect('account:dettaglio_struttura', pk=camera.struttura.id)
    else:
        form = CameraForm(instance=camera)
    return render(request, 'account/modifica_camera.html', {'form': form, 'camera': camera})

@login_required
def elimina_struttura(request, struttura_id):
    struttura = get_object_or_404(Struttura, id=struttura_id)
    if request.method == "POST":
        struttura.delete()  # Elimina anche tutte le camere collegate
        return redirect('account:dashboard_gestore')
    return redirect('account:dashboard_gestore')  # Corretto l'errore di battitura

@login_required
def elimina_camera(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    if request.method == "POST":
        camera.delete()
        return redirect('account:dashboard_gestore')  # O dove vuoi reindirizzare
    return redirect('account:dashboard_gestore')  # O dove vuoi reindirizzare

def dettaglio_struttura_pubblico(request, pk):
    struttura = get_object_or_404(Struttura, pk=pk)
    filter_form = CameraFilterForm(request.GET)
    camere = struttura.camere.filter(disponibilita=True)
    
    if filter_form.is_valid():
        # Applica i filtri
        if filter_form.cleaned_data['min_prezzo']:
            camere = camere.filter(prezzo_per_notte__gte=filter_form.cleaned_data['min_prezzo'])
        if filter_form.cleaned_data['max_prezzo']:
            camere = camere.filter(prezzo_per_notte__lte=filter_form.cleaned_data['max_prezzo'])
        if filter_form.cleaned_data['numero_persone']:
            camere = camere.filter(numero_persone=filter_form.cleaned_data['numero_persone'])
        if filter_form.cleaned_data['bagno_privato']:
            camere = camere.filter(bagno_privato=True)
        if filter_form.cleaned_data['aria_condizionata']:
            camere = camere.filter(aria_condizionata=True)
        if filter_form.cleaned_data['wifi']:
            camere = camere.filter(wifi=True)
        if filter_form.cleaned_data['tv']:
            camere = camere.filter(tv=True)
        if filter_form.cleaned_data['balcone']:
            camere = camere.filter(balcone=True)
        if filter_form.cleaned_data['letto_matrimoniale']:
            camere = camere.filter(letto_matrimoniale=True)
        if filter_form.cleaned_data['accessibile_disabili']:
            camere = camere.filter(accessibile_disabili=True)
        
        # Ordinamento
        if filter_form.cleaned_data['ordina_per']:
            camere = camere.order_by(filter_form.cleaned_data['ordina_per'])
    
    return render(request, 'account/dettaglio_struttura_pubblico.html', {
        'struttura': struttura,
        'camere': camere,
        'filter_form': filter_form,
        'check_in_date': request.GET.get('check_in_date'),
        'check_out_date': request.GET.get('check_out_date'),
        'num_people': request.GET.get('num_people')
    })

def home(request):
    filter_form = StrutturaFilterForm(request.GET)
    strutture = Struttura.objects.all()
    
    if filter_form.is_valid():
        # Ricerca per nome o città
        if filter_form.cleaned_data['search']:
            search_query = filter_form.cleaned_data['search']
            strutture = strutture.filter(
                Q(nome__icontains=search_query) | 
                Q(citta__icontains=search_query)
            )
        
        # Filtro per tipologia
        if filter_form.cleaned_data['tipologia']:
            strutture = strutture.filter(tipologia__in=filter_form.cleaned_data['tipologia'])
        
        # Filtri booleani
        if filter_form.cleaned_data['parcheggio']:
            strutture = strutture.filter(parcheggio=True)
        if filter_form.cleaned_data['piscina']:
            strutture = strutture.filter(piscina=True)
        if filter_form.cleaned_data['ristorante']:
            strutture = strutture.filter(ristorante=True)
        if filter_form.cleaned_data['animali_ammessi']:
            strutture = strutture.filter(animali_ammessi=True)
        
        # Ordinamento
        if filter_form.cleaned_data['ordina_per']:
            strutture = strutture.order_by(filter_form.cleaned_data['ordina_per'])
    
    return render(request, 'account/home.html', {
        'strutture': strutture,
        'filter_form': filter_form,
    })

from .models import Camera

def dettaglio_camera_pubblico(request, pk):
    """Vista pubblica del dettaglio di una camera"""
    camera = get_object_or_404(Camera, pk=pk)
    # Preserva i parametri della ricerca
    context = {
        'camera': camera,
        'request': request,  # Passa l'oggetto request al template
        'check_in_date': request.GET.get('check_in_date'),
        'check_out_date': request.GET.get('check_out_date'),
        'num_people': request.GET.get('num_people')
    }
    return render(request, 'account/dettaglio_camera_pubblico.html', context)