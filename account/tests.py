from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import User, GestoreProfile, Struttura, Camera

class UserModelTest(TestCase):
    def setUp(self):
        """Setup per i test degli utenti"""
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'nome': 'Test',
            'cognome': 'User',
            'telefono': '1234567890'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_creation(self):
        """Test creazione utente base"""
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertEqual(self.user.nome, self.user_data['nome'])
        self.assertEqual(self.user.cognome, self.user_data['cognome'])
        self.assertTrue(self.user.is_cliente())
        self.assertFalse(self.user.is_gestore())

    def test_user_str(self):
        """Test rappresentazione stringa dell'utente"""
        self.assertEqual(str(self.user), "test@example.com (Cliente)")

class GestoreTest(TestCase):
    def setUp(self):
        """Setup per i test dei gestori"""
        self.gestore = User.objects.create_user(
            email='gestore@example.com',
            password='gestore123',
            nome='Gestore',
            cognome='Test',
            user_type='GESTORE'
        )
        self.gestore_profile = GestoreProfile.objects.create(
            user=self.gestore,
            partita_iva='12345678901',
            denominazione_sociale='Hotel Test',
            indirizzo_sede='Via Test 123'
        )

    def test_gestore_creation(self):
        """Test creazione profilo gestore"""
        self.assertTrue(self.gestore.is_gestore())
        self.assertEqual(self.gestore_profile.partita_iva, '12345678901')
        self.assertEqual(self.gestore_profile.denominazione_sociale, 'Hotel Test')

    def test_struttura_creation(self):
        """Test creazione struttura"""
        struttura = Struttura.objects.create(
            gestore=self.gestore_profile,
            nome='Hotel Test',
            descrizione='Test description',
            indirizzo='Via Test 123',
            citta='Test City',
            tipologia='hotel'
        )
        self.assertEqual(struttura.nome, 'Hotel Test')
        self.assertEqual(struttura.gestore, self.gestore_profile)

class AuthenticationTest(TestCase):
    def setUp(self):
        """Setup per i test di autenticazione"""
        self.client = Client()
        self.login_url = reverse('account:login')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_login_success(self):
        """Test login con credenziali valide"""
        response = self.client.post(self.login_url, {
            'username': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect dopo login
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_failure(self):
        """Test login con credenziali non valide"""
        response = self.client.post(self.login_url, {
            'username': 'test@example.com',
            'password': 'wrongpass'
        })
        self.assertFalse(response.wsgi_request.user.is_authenticated)

class StrutturaTest(TestCase):
    def setUp(self):
        """Setup per i test delle strutture"""
        self.gestore = User.objects.create_user(
            email='gestore@example.com',
            password='gestore123',
            user_type='GESTORE'
        )
        self.gestore_profile = GestoreProfile.objects.create(
            user=self.gestore,
            partita_iva='12345678901',
            denominazione_sociale='Hotel Test',
            indirizzo_sede='Via Test 123'
        )
        self.struttura = Struttura.objects.create(
            gestore=self.gestore_profile,
            nome='Hotel Test',
            descrizione='Test description',
            indirizzo='Via Test 123',
            citta='Test City',
            tipologia='hotel'
        )

    def test_camera_creation(self):
        """Test creazione camera"""
        camera = Camera.objects.create(
            struttura=self.struttura,
            numero_persone=2,
            prezzo_per_notte=100.00,
            descrizione='Camera standard'
        )
        self.assertEqual(camera.numero_camera, 1)  # Il primo numero di camera sarà 1
        self.assertEqual(camera.struttura, self.struttura)
        self.assertEqual(camera.numero_persone, 2)

        # Crea una seconda camera per verificare l'auto-incremento
        camera2 = Camera.objects.create(
            struttura=self.struttura,
            numero_persone=3,
            prezzo_per_notte=150.00,
            descrizione='Camera superior'
        )
        self.assertEqual(camera2.numero_camera, 2)  # Il secondo numero di camera sarà 2

    def test_struttura_filters(self):
        """Test filtri struttura"""
        # Crea una seconda struttura per i test
        Struttura.objects.create(
            gestore=self.gestore_profile,
            nome='Hotel Luxury',
            descrizione='Luxury hotel',
            indirizzo='Via Luxury 456',
            citta='Test City',
            tipologia='hotel',
            piscina=True
        )
        
        # Test filtro per città
        strutture_citta = Struttura.objects.filter(citta='Test City')
        self.assertEqual(strutture_citta.count(), 2)
        
        # Test filtro per servizi
        strutture_piscina = Struttura.objects.filter(piscina=True)
        self.assertEqual(strutture_piscina.count(), 1)
        self.assertEqual(strutture_piscina.first().nome, 'Hotel Luxury') 