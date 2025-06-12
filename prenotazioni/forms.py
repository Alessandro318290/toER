from django import forms
from .models import Booking, Camera
from django.utils import timezone
from datetime import timedelta

"""
Modulo contenente i form per la gestione delle prenotazioni.
Implementa la logica di validazione e presentazione dei dati
per la creazione e modifica delle prenotazioni.
"""

class BookingForm(forms.ModelForm):
    """
    Form per la creazione e modifica delle prenotazioni.
    
    Caratteristiche principali:
    - Campo camera nascosto (viene preselezionato)
    - Validazione delle date (no passato, max 30 giorni)
    - Validazione numero persone rispetto alla capacità della camera
    - Supporto per note e richieste speciali
    """
    
    # Campo camera nascosto poiché viene preselezionato dalla vista
    camera = forms.ModelChoiceField(queryset=Camera.objects.all(), widget=forms.HiddenInput(), required=True)
    
    class Meta:
        model = Booking
        fields = ['camera', 'check_in_date', 'check_out_date', 'num_people', 'notes']
        widgets = {
            # Input date per check-in con data minima oggi
            'check_in_date': forms.DateInput(attrs={
                'type': 'date',
                'min': timezone.localtime(timezone.now()).date().isoformat(),
                'class': 'form-control'
            }),
            # Input date per check-out con data minima domani
            'check_out_date': forms.DateInput(attrs={
                'type': 'date',
                'min': (timezone.localtime(timezone.now()).date() + timedelta(days=1)).isoformat(),
                'class': 'form-control'
            }),
            # Input numerico per numero persone (minimo 1)
            'num_people': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            # Area di testo per note aggiuntive
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Inserisci eventuali note o richieste speciali',
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        """
        Inizializzazione del form con gestione dei valori predefiniti.
        Se vengono forniti valori iniziali, li imposta come valori predefiniti
        nei rispettivi campi.
        """
        super().__init__(*args, **kwargs)
        # Se i valori iniziali sono forniti, li impostiamo come valori predefiniti
        if 'initial' in kwargs and kwargs['initial']:
            if 'check_in_date' in kwargs['initial']:
                self.fields['check_in_date'].initial = kwargs['initial']['check_in_date']
            if 'check_out_date' in kwargs['initial']:
                self.fields['check_out_date'].initial = kwargs['initial']['check_out_date']
            if 'num_people' in kwargs['initial']:
                self.fields['num_people'].initial = kwargs['initial']['num_people']
            if 'camera' in kwargs['initial']:
                try:
                    camera = Camera.objects.get(id=kwargs['initial']['camera'])
                    self.fields['camera'].initial = camera
                except Camera.DoesNotExist:
                    pass

    def clean(self):
        """
        Esegue la validazione dei dati inseriti nel form.
        
        Validazioni effettuate:
        1. Date:
           - Check-in non può essere nel passato
           - Check-out deve essere successivo al check-in
           - Durata massima 30 giorni
        
        2. Numero persone:
           - Deve essere almeno 1
           - Non può superare la capacità della camera
        """
        cleaned_data = super().clean()
        check_in_date = cleaned_data.get('check_in_date')
        check_out_date = cleaned_data.get('check_out_date')
        num_people = cleaned_data.get('num_people')
        camera = cleaned_data.get('camera')

        # Validazione date
        if check_in_date and check_out_date:
            today = timezone.localtime(timezone.now()).date()
            
            if check_in_date < today:
                raise forms.ValidationError("La data di check-in non può essere nel passato")
            
            if check_out_date <= check_in_date:
                raise forms.ValidationError("La data di check-out deve essere successiva alla data di check-in")
            
            if (check_out_date - check_in_date).days > 30:
                raise forms.ValidationError("Non puoi prenotare per più di 30 giorni")

        # Validazione numero persone e capacità camera
        if camera and num_people:
            if num_people < 1:
                raise forms.ValidationError("Il numero di persone deve essere almeno 1")
            if num_people > camera.numero_persone:
                raise forms.ValidationError(f"Il numero di persone ({num_people}) supera la capacità massima della camera ({camera.numero_persone})")

        return cleaned_data 