from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('Email deve essere specificata')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve avere is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve avere is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with email as the unique identifier."""

    # Tipi di utente
    class UserType(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        GESTORE = 'GESTORE', _('Gestore')
        CLIENTE = 'CLIENTE', _('Cliente')

    username = None
    first_name = None
    last_name = None
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.CLIENTE,
        help_text=_('Specifica se l\'utente è un gestore o un cliente'),
    )
    # Campi aggiuntivi per informazioni personali
    nome = models.CharField(max_length=100, blank=True)
    cognome = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"
    
    def is_gestore(self):
        return self.user_type == self.UserType.GESTORE
    
    def is_cliente(self):
        return self.user_type == self.UserType.CLIENTE


class GestoreProfile(models.Model):
    """Profilo aggiuntivo per utenti gestori"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gestore_profile')
    partita_iva = models.CharField(max_length=20, blank=True)
    denominazione_sociale = models.CharField(max_length=200, blank=True)
    indirizzo_sede = models.CharField(max_length=250, blank=True)
    
    def __str__(self):
        return f"Profilo gestore di {self.user.email}"


class ClienteProfile(models.Model):
    """Profilo aggiuntivo per utenti clienti"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente_profile')
    indirizzo = models.CharField(max_length=250, blank=True)
    citta = models.CharField(max_length=100, blank=True)
    data_nascita = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Profilo cliente di {self.user.email}"

class Struttura(models.Model):
    TIPI_STRUTTURA = [
        ('hotel', 'Hotel'),
        ('b&b', 'Bed & Breakfast'),
        ('casa_vacanze', 'Casa Vacanze'),
        ('ostello', 'Ostello'),
        # aggiungi altre tipologie se vuoi
    ]
    gestore = models.ForeignKey(GestoreProfile, on_delete=models.CASCADE, related_name='strutture')
    nome = models.CharField(max_length=200)
    descrizione = models.TextField()
    indirizzo = models.CharField(max_length=250)
    def struttura_image_upload_path(instance, filename):
        struttura_nome = instance.nome.replace(" ", "_")
        return f"strutture/{struttura_nome}/{filename}"

    immagine = models.ImageField(upload_to=struttura_image_upload_path, blank=True, null=True)
    disponibilita = models.BooleanField(default=True)
    tipologia = models.CharField(max_length=30, choices=TIPI_STRUTTURA, default='hotel')
    parcheggio = models.BooleanField(default=False)
    piscina = models.BooleanField(default=False)
    ristorante = models.BooleanField(default=False)
    animali_ammessi = models.BooleanField(default=False)
    citta = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    numero_camere = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.nome

class Camera(models.Model):
    struttura = models.ForeignKey(Struttura, on_delete=models.CASCADE, related_name='camere')
    numero_camera = models.PositiveIntegerField(default=1)
    prezzo_per_notte = models.DecimalField(max_digits=7, decimal_places=2, default=50.00)
    
    def camera_image_upload_path(instance, filename):
        # Usa il nome della struttura e il numero camera per creare il percorso
        struttura_nome = instance.struttura.nome.replace(" ", "_")
        camera_nome = f"camera_{instance.numero_camera}"
        return f"strutture/camere/{struttura_nome}/{camera_nome}/{filename}"

    immagine = models.ImageField(upload_to=camera_image_upload_path, blank=True, null=True)
    disponibilita = models.BooleanField(default=True)
    numero_persone = models.PositiveIntegerField()
    descrizione = models.TextField(blank=True)  
    bagno_privato = models.BooleanField(default=True)
    aria_condizionata = models.BooleanField(default=False)
    wifi = models.BooleanField(default=True)
    tv = models.BooleanField(default=False)
    balcone = models.BooleanField(default=False)
    vista = models.CharField(max_length=100, blank=True, help_text="Es: mare, montagna, città")
    letto_matrimoniale = models.BooleanField(default=False)
    letti_singoli = models.PositiveIntegerField(default=0)
    accessibile_disabili = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk and self.struttura:
            last_camera = Camera.objects.filter(struttura=self.struttura).order_by('-numero_camera').first()
            self.numero_camera = (last_camera.numero_camera + 1) if last_camera else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Camera {self.numero_camera} ({self.numero_persone} persone)"

class CameraImmagine(models.Model):
    camera = models.ForeignKey('Camera', on_delete=models.CASCADE, related_name='immagini')
    immagine = models.ImageField(upload_to='camere/')
    didascalia = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Immagine per Camera {self.camera.numero_camera}"