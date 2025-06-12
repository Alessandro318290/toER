from django.db import models
from django.conf import settings
from account.models import Camera
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

# Modelli per la gestione delle prenotazioni

class Notification(models.Model):
    """
    Modello per la gestione delle notifiche agli utenti.
    Viene utilizzato per informare gli utenti su:
    - Cambiamenti di stato delle prenotazioni
    - Disponibilità di camere dalla lista d'attesa
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Utente che riceve la notifica
    message = models.TextField()  # Contenuto della notifica
    created_at = models.DateTimeField(auto_now_add=True)  # Data e ora di creazione
    read = models.BooleanField(default=False)  # Indica se la notifica è stata letta
    waiting_list = models.ForeignKey('WaitingList', on_delete=models.CASCADE, null=True)  # Riferimento alla lista d'attesa (se applicabile)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notifica'
        verbose_name_plural = 'Notifiche'

    def __str__(self):
        return f"Notifica per {self.user.email}: {self.message[:50]}..."

# Funzioni helper per le date di default
def get_default_check_in():
    """Restituisce la data corrente come data di default per il check-in"""
    return timezone.now().date()

def get_default_check_out():
    """Restituisce la data corrente + 1 giorno come data di default per il check-out"""
    return timezone.now().date() + timedelta(days=1)

class Booking(models.Model):
    """
    Modello principale per la gestione delle prenotazioni.
    Gestisce tutto il ciclo di vita di una prenotazione, dal momento della creazione
    fino al check-out, includendo tutti gli stati intermedi.
    """
    # Stati possibili per una prenotazione
    STATUS_CHOICES = [
        ('pending', 'In attesa'),      # Prenotazione creata ma non ancora confermata
        ('approved', 'Approvata'),     # Prenotazione confermata
        ('rejected', 'Rifiutata'),     # Prenotazione rifiutata
        ('checked_in', 'Check-in effettuato'),  # Cliente ha effettuato il check-in
        ('checked_out', 'Check-out effettuato'),  # Cliente ha effettuato il check-out
        ('cancelled', 'Cancellata'),   # Prenotazione cancellata
    ]
    
    # Campi principali della prenotazione
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Utente che ha effettuato la prenotazione
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, null=True, blank=True)  # Camera prenotata
    check_in_date = models.DateField(default=get_default_check_in)  # Data prevista di check-in
    check_out_date = models.DateField(default=get_default_check_out)  # Data prevista di check-out
    num_people = models.IntegerField()  # Numero di persone per cui si prenota
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Stato attuale della prenotazione
    notes = models.TextField(blank=True)  # Note aggiuntive sulla prenotazione
    created_at = models.DateTimeField(auto_now_add=True)  # Data e ora di creazione della prenotazione
    actual_check_in = models.DateTimeField(null=True, blank=True)  # Data e ora effettiva del check-in
    actual_check_out = models.DateTimeField(null=True, blank=True)  # Data e ora effettiva del check-out

    def is_available(self):
        """
        Verifica la disponibilità della camera per il periodo richiesto.
        Controlla che non ci siano sovrapposizioni con altre prenotazioni esistenti.
        """
        if not self.camera or not self.check_in_date or not self.check_out_date:
            return False
            
        # Cerca prenotazioni sovrapposte escludendo quelle cancellate o terminate
        overlapping_bookings = Booking.objects.filter(
            camera=self.camera,
            status__in=['pending', 'approved', 'checked_in']
        ).exclude(id=self.id)
        
        # Verifica sovrapposizioni temporali
        overlapping_bookings = overlapping_bookings.filter(
            models.Q(check_in_date__lte=self.check_out_date, check_out_date__gte=self.check_in_date) |
            models.Q(check_in_date__lte=self.check_in_date, check_out_date__gte=self.check_out_date)
        )
        
        return not overlapping_bookings.exists()

    def clean(self):
        """
        Esegue tutte le validazioni necessarie prima del salvataggio della prenotazione.
        Controlla date, disponibilità, capacità e transizioni di stato.
        """
        # Validazioni solo se la prenotazione non è cancellata
        if self.status != 'cancelled':
            today = timezone.localtime(timezone.now()).date()
            
            # Validazione date
            if not self.check_in_date or not self.check_out_date:
                raise ValidationError("Le date di check-in e check-out sono obbligatorie")
            
            if self.check_in_date < today:
                raise ValidationError("Non puoi prenotare per date passate")
                
            if self.check_out_date <= self.check_in_date:
                raise ValidationError("La data di check-out deve essere successiva alla data di check-in")
                
            if (self.check_out_date - self.check_in_date).days > 30:
                raise ValidationError("Non puoi prenotare per più di 30 giorni")
            
            # Validazione camera e disponibilità
            if not self.camera:
                raise ValidationError("Devi specificare una camera")
                
            if not self.is_available():
                raise ValidationError(f"Camera {self.camera.numero_camera} della struttura {self.camera.struttura.nome} non disponibile per il periodo selezionato")
            
            # Validazione capacità camera
            if self.camera and self.num_people > self.camera.numero_persone:
                raise ValidationError(f"Il numero di persone ({self.num_people}) supera la capacità massima della camera ({self.camera.numero_persone})")
        
        # Validazione transizioni di stato per check-in/check-out
        if self.status == 'checked_in':
            if not self.actual_check_in:
                self.actual_check_in = timezone.now()
            if timezone.localtime(timezone.now()).date() != self.check_in_date:
                raise ValidationError("Il check-in può essere effettuato solo nel giorno previsto")
        
        if self.status == 'checked_out':
            if not self.actual_check_in:
                raise ValidationError("Non puoi effettuare il check-out senza aver fatto il check-in")
            if not self.actual_check_out:
                self.actual_check_out = timezone.now()
            if self.actual_check_out < self.actual_check_in:
                raise ValidationError("L'ora di check-out non può essere precedente all'ora di check-in")

    def save(self, *args, **kwargs):
        """
        Gestisce il salvataggio della prenotazione e la notifica agli utenti in lista d'attesa
        in caso di cancellazione.
        """
        self.clean()
        super().save(*args, **kwargs)
        
        # Gestione notifiche per lista d'attesa in caso di cancellazione
        if self.status == 'cancelled':
            waiting_list_entries = WaitingList.objects.filter(
                camera=self.camera,
                date__range=[self.check_in_date, self.check_out_date],
                notified=False
            )
            
            for entry in waiting_list_entries:
                Notification.objects.create(
                    user=entry.user,
                    message=f"La camera {self.camera.numero_camera} della struttura {self.camera.struttura.nome} è ora disponibile per il periodo richiesto!",
                    waiting_list=entry
                )
                entry.notified = True
                entry.save()
    
    def can_be_modified(self):
        """Verifica se la prenotazione può essere modificata (solo stati pending e approved)"""
        return self.status in ['pending', 'approved']
    
    def can_be_cancelled(self):
        """Verifica se la prenotazione può essere cancellata (tutti gli stati tranne checked_in, checked_out e cancelled)"""
        return self.status not in ['checked_in', 'checked_out', 'cancelled']
    
    def can_check_in(self):
        """Verifica se è possibile effettuare il check-in (solo nel giorno previsto e se approvata)"""
        today = timezone.localtime(timezone.now()).date()
        return (
            self.status == 'approved' and 
            self.check_in_date == today and
            not self.actual_check_in
        )
    
    def can_check_out(self):
        """Verifica se è possibile effettuare il check-out (solo dopo il check-in e prima del check-out effettivo)"""
        return (
            self.status == 'checked_in' and 
            self.actual_check_in and
            not self.actual_check_out
        )

    class Meta:
        ordering = ['-check_in_date', '-created_at']
        verbose_name = 'Prenotazione'
        verbose_name_plural = 'Prenotazioni'
        
    def __str__(self):
        return f"Prenotazione {self.id} - {self.user.email} - Camera {self.camera.numero_camera if self.camera else 'N/A'}"

class WaitingList(models.Model):
    """
    Modello per la gestione della lista d'attesa.
    Permette agli utenti di mettersi in coda per una camera quando non è disponibile
    nel periodo desiderato.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Utente in lista d'attesa
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)  # Camera desiderata
    date = models.DateField()  # Data per cui si richiede la camera
    num_people = models.IntegerField()  # Numero di persone
    created_at = models.DateTimeField(auto_now_add=True)  # Data e ora della richiesta
    notified = models.BooleanField(default=False)  # Indica se l'utente è stato notificato della disponibilità
    
    class Meta:
        unique_together = ['user', 'camera', 'date']  # Un utente può essere in lista d'attesa una sola volta per una specifica camera e data
