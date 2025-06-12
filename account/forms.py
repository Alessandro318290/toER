from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import User, GestoreProfile, ClienteProfile, Struttura, Camera
from django.forms import modelformset_factory


class LoginForm(AuthenticationForm):
    """Form per il login degli utenti"""
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label="Password"
    )


class UserRegistrationForm(UserCreationForm):
    """Form base per la registrazione degli utenti"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    nome = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'})
    )
    cognome = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cognome'})
    )
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefono'})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        label="Conferma password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Conferma password'})
    )
    
    class Meta:
        model = User
        fields = ('email', 'nome', 'cognome', 'telefono', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Questa email è già registrata nel sistema.")
        return email


class GestoreRegistrationForm(UserRegistrationForm):
    """Form per la registrazione di un utente gestore"""
    partita_iva = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Partita IVA'})
    )
    denominazione_sociale = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Denominazione sociale'})
    )
    indirizzo_sede = forms.CharField(
        max_length=250,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Indirizzo sede'})
    )
    

    class Meta(UserRegistrationForm.Meta):
        fields = UserRegistrationForm.Meta.fields + ('partita_iva', 'denominazione_sociale', 'indirizzo_sede')

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = User.UserType.GESTORE
        if commit:
            user.save()
            gestore_profile = GestoreProfile.objects.create(
                user=user,
                partita_iva=self.cleaned_data.get('partita_iva'),
                denominazione_sociale=self.cleaned_data.get('denominazione_sociale'),
                indirizzo_sede=self.cleaned_data.get('indirizzo_sede')
            )
        return user


class ClienteRegistrationForm(UserRegistrationForm):
    """Form per la registrazione di un utente cliente"""
    indirizzo = forms.CharField(
        max_length=250,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Indirizzo'})
    )
    citta = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Città'})
    )
    data_nascita = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text="Formato: YYYY-MM-DD"
    )

    class Meta(UserRegistrationForm.Meta):
        fields = UserRegistrationForm.Meta.fields + ('indirizzo', 'citta', 'data_nascita')

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = User.UserType.CLIENTE
        if commit:
            user.save()
            cliente_profile = ClienteProfile.objects.create(
                user=user,
                indirizzo=self.cleaned_data.get('indirizzo'),
                citta=self.cleaned_data.get('citta'),
                data_nascita=self.cleaned_data.get('data_nascita')
            )
        return user


class UserProfileUpdateForm(forms.ModelForm):
    """Form per aggiornare i dati dell'utente base"""
    class Meta:
        model = User
        fields = ('nome', 'cognome', 'telefono')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cognome': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }


class GestoreProfileUpdateForm(forms.ModelForm):
    """Form per aggiornare i dati del profilo gestore"""
    
    class Meta:
        model = GestoreProfile
        fields = ('partita_iva', 'denominazione_sociale', 'indirizzo_sede')
        widgets = {
            'partita_iva': forms.TextInput(attrs={'class': 'form-control'}),
            'denominazione_sociale': forms.TextInput(attrs={'class': 'form-control'}),
            'indirizzo_sede': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ClienteProfileUpdateForm(forms.ModelForm):
    """Form per aggiornare i dati del profilo cliente"""
    class Meta:
        model = ClienteProfile
        fields = ('indirizzo', 'citta', 'data_nascita')
        widgets = {
            'indirizzo': forms.TextInput(attrs={'class': 'form-control'}),
            'citta': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascita': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        
class StrutturaForm(forms.ModelForm):
    class Meta:
        model = Struttura
        fields = [
            'nome',
            'descrizione',
            'indirizzo',
            'citta',
            'telefono',  
            'immagine',
            'tipologia',
            'parcheggio',
            'piscina',
            'ristorante',
            'animali_ammessi',
            'numero_camere',
        ]
        widgets = {
            'immagine': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'citta': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control'}),
            'indirizzo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipologia': forms.Select(attrs={'class': 'form-control'}),
            'parcheggio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'piscina': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ristorante': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'animali_ammessi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'numero_camere': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class CameraForm(forms.ModelForm):
    class Meta:
        model = Camera
        fields = [
            'numero_camera',
            'prezzo_per_notte',
            'immagine',
            'disponibilita',
            'numero_persone',
            'descrizione',
            'bagno_privato',
            'aria_condizionata',
            'wifi',
            'tv',
            'balcone',
            'vista',
            'letto_matrimoniale',
            'letti_singoli',
            'accessibile_disabili',
        ]
        widgets = {
            'numero_camera': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'prezzo_per_notte': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'numero_persone': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'disponibilita': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control'}),
            'bagno_privato': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'aria_condizionata': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'wifi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'balcone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'vista': forms.TextInput(attrs={'class': 'form-control'}),
            'letto_matrimoniale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'letti_singoli': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'accessibile_disabili': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'immagine': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            
        }

CameraFormSet = modelformset_factory(Camera, form=CameraForm, extra=1, can_delete=True)

class StrutturaEditForm(forms.ModelForm):
    class Meta:
        model = Struttura
        fields = '__all__'

class CameraEditForm(forms.ModelForm):
    class Meta:
        model = Camera
        fields = '__all__'

class StrutturaFilterForm(forms.Form):
    ORDINA_PER = [
        ('nome', 'Nome (A-Z)'),
        ('-nome', 'Nome (Z-A)'),
        ('citta', 'Città (A-Z)'),
        ('-citta', 'Città (Z-A)'),
    ]
    
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Cerca per nome o città...'
    }))
    tipologia = forms.MultipleChoiceField(
        choices=Struttura.TIPI_STRUTTURA,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    parcheggio = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    piscina = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    ristorante = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    animali_ammessi = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    ordina_per = forms.ChoiceField(
        choices=ORDINA_PER,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class CameraFilterForm(forms.Form):
    ORDINA_PER = [
        ('prezzo_per_notte', 'Prezzo (crescente)'),
        ('-prezzo_per_notte', 'Prezzo (decrescente)'),
        ('numero_persone', 'Numero persone (crescente)'),
        ('-numero_persone', 'Numero persone (decrescente)'),
    ]
    
    min_prezzo = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Prezzo minimo'
    }))
    max_prezzo = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Prezzo massimo'
    }))
    numero_persone = forms.IntegerField(required=False, min_value=1, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Numero persone'
    }))
    bagno_privato = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    aria_condizionata = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    wifi = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    tv = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    balcone = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    letto_matrimoniale = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    accessibile_disabili = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    ordina_per = forms.ChoiceField(
        choices=ORDINA_PER,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )