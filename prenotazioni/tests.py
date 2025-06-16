from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from account.models import User, GestoreProfile, Struttura
from .models import Booking, WaitingList, Notification, Camera

class BookingTest(TestCase):
    def setUp(self):
        """Setup per i test delle prenotazioni"""
        # Crea cliente
        self.cliente = User.objects.create_user(
            email='cliente@example.com',
            password='cliente123',
            user_type='CLIENTE'
        )
        
        # Crea gestore e profilo
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
        
        # Crea struttura
        self.struttura = Struttura.objects.create(
            gestore=self.gestore_profile,
            nome='Hotel Test',
            descrizione='Test description',
            indirizzo='Via Test 123',
            citta='Test City',
            tipologia='hotel'
        )
        
        # Crea camera
        self.camera = Camera.objects.create(
            struttura=self.struttura,
            numero_camera=101,
            numero_persone=2,
            prezzo_per_notte=100.00
        )
        
        # Date per i test
        self.check_in_date = timezone.now().date()
        self.check_out_date = self.check_in_date + timedelta(days=2)

    def test_booking_creation(self):
        """Test creazione prenotazione"""
        booking = Booking.objects.create(
            user=self.cliente,
            camera=self.camera,
            check_in_date=self.check_in_date,
            check_out_date=self.check_out_date,
            num_people=2,
            status='pending'
        )
        self.assertEqual(booking.user, self.cliente)
        self.assertEqual(booking.camera, self.camera)
        self.assertEqual(booking.status, 'pending')

    def test_booking_status_change(self):
        """Test cambio stato prenotazione"""
        booking = Booking.objects.create(
            user=self.cliente,
            camera=self.camera,
            check_in_date=self.check_in_date,
            check_out_date=self.check_out_date,
            num_people=2,
            status='pending'
        )
        
        # Test approvazione
        booking.status = 'approved'
        booking.save()
        self.assertEqual(booking.status, 'approved')
        
        # Test check-in
        booking.status = 'checked_in'
        booking.actual_check_in = timezone.now()
        booking.save()
        self.assertEqual(booking.status, 'checked_in')
        self.assertIsNotNone(booking.actual_check_in)

class WaitingListTest(TestCase):
    def setUp(self):
        """Setup per i test della lista d'attesa"""
        # Crea cliente
        self.cliente = User.objects.create_user(
            email='cliente@example.com',
            password='cliente123',
            user_type='CLIENTE'
        )
        
        # Crea gestore e struttura
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
            citta='Test City'
        )
        self.camera = Camera.objects.create(
            struttura=self.struttura,
            numero_camera=101,
            numero_persone=2,
            prezzo_per_notte=100.00
        )

    def test_waiting_list_creation(self):
        """Test creazione elemento lista d'attesa"""
        waiting = WaitingList.objects.create(
            user=self.cliente,
            camera=self.camera,
            date=timezone.now().date(),
            num_people=2
        )
        self.assertEqual(waiting.user, self.cliente)
        self.assertEqual(waiting.camera, self.camera)
        self.assertEqual(waiting.num_people, 2)
        self.assertFalse(waiting.notified)

class NotificationTest(TestCase):
    def setUp(self):
        """Setup per i test delle notifiche"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test123'
        )

    def test_notification_creation(self):
        """Test creazione notifica"""
        notification = Notification.objects.create(
            user=self.user,
            message='Test notification'
        )
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.message, 'Test notification')
        self.assertFalse(notification.read)

    def test_notification_marking(self):
        """Test marcatura notifica come letta"""
        notification = Notification.objects.create(
            user=self.user,
            message='Test notification'
        )
        self.assertFalse(notification.read)
        
        notification.read = True
        notification.save()
        self.assertTrue(notification.read)

class BookingViewsTest(TestCase):
    def setUp(self):
        """Setup per i test delle viste delle prenotazioni"""
        self.client = Client()
        # Crea e logga un cliente
        self.cliente = User.objects.create_user(
            email='cliente@example.com',
            password='cliente123',
            user_type='CLIENTE'
        )
        self.client.login(email='cliente@example.com', password='cliente123')
        
        # Crea gestore e struttura
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
            citta='Test City'
        )
        self.camera = Camera.objects.create(
            struttura=self.struttura,
            numero_camera=101,
            numero_persone=2,
            prezzo_per_notte=100.00
        )

    def test_lista_prenotazioni_view(self):
        """Test vista lista prenotazioni"""
        response = self.client.get(reverse('prenotazioni:lista_prenotazioni'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'prenotazioni/lista_prenotazioni.html')

    def test_waiting_list_view(self):
        """Test vista lista d'attesa"""
        response = self.client.get(reverse('prenotazioni:waiting_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'prenotazioni/waiting_list.html')

class BookingAdvancedTest(TestCase):
    """Test avanzati per la gestione delle prenotazioni"""
    
    def setUp(self):
        """Setup iniziale per i test avanzati"""
        self.client = Client()
        
        # Creazione utenti
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            user_type='CLIENTE',
            nome='Test',
            cognome='User'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123',
            user_type='CLIENTE',
            nome='Test2',
            cognome='User2'
        )
        
        # Creazione gestore e profilo
        self.gestore = User.objects.create_user(
            email='gestore@test.com',
            password='testpass123',
            user_type='GESTORE',
            nome='Gestore',
            cognome='Test'
        )
        
        self.gestore_profile = GestoreProfile.objects.create(
            user=self.gestore,
            partita_iva='12345678901',
            denominazione_sociale='Hotel Test',
            indirizzo_sede='Via Test 123'
        )
        
        # Creazione struttura
        self.struttura = Struttura.objects.create(
            gestore=self.gestore_profile,
            nome="Hotel Test",
            descrizione="Test description",
            indirizzo="Via Test 1",
            citta="Bologna",
            tipologia="hotel"
        )
        
        # Creazione camera
        self.camera = Camera.objects.create(
            struttura=self.struttura,
            numero_camera=101,
            numero_persone=2,
            prezzo_per_notte=100.00,
            descrizione="Camera test",
            bagno_privato=True,
            wifi=True
        )

    def test_complex_booking_lifecycle(self):
        """Test del ciclo di vita completo di una prenotazione"""
        check_in_date = timezone.now().date() + timedelta(days=1)
        check_out_date = check_in_date + timedelta(days=2)
        
        # Creazione prenotazione
        booking = Booking.objects.create(
            user=self.user,
            camera=self.camera,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            num_people=2,
            status='pending'
        )
        
        # Test stato iniziale
        self.assertEqual(booking.status, 'pending')
        
        # Test approvazione
        booking.status = 'approved'
        booking.save()
        self.assertEqual(booking.status, 'approved')
        
        # Simula l'arrivo del giorno del check-in
        booking.check_in_date = timezone.now().date()
        booking.save()
        
        # Test check-in
        booking.status = 'checked_in'
        booking.actual_check_in = timezone.now()
        booking.save()
        self.assertEqual(booking.status, 'checked_in')
        self.assertIsNotNone(booking.actual_check_in)
        
        # Test check-out
        booking.status = 'checked_out'
        booking.actual_check_out = timezone.now()
        booking.save()
        self.assertEqual(booking.status, 'checked_out')
        self.assertIsNotNone(booking.actual_check_out)

    def test_concurrent_booking_prevention(self):
        """
        Test per verificare la prevenzione di prenotazioni concorrenti
        sulla stessa camera
        """
        # Date di test
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=2)
        
        # Prima prenotazione
        booking1 = Booking.objects.create(
            user=self.user,
            camera=self.camera,
            check_in_date=check_in,
            check_out_date=check_out,
            num_people=2,
            status='approved'
        )
        
        # Prova a creare una seconda prenotazione sovrapposta
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                user=self.user2,
                camera=self.camera,
                check_in_date=check_in,
                check_out_date=check_out,
                num_people=2,
                status='pending'
            )

    def test_waiting_list_notification(self):
        """
        Test per verificare il sistema di notifiche della lista d'attesa
        quando una prenotazione viene cancellata
        """
        # Crea una prenotazione
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=2)
        
        booking = Booking.objects.create(
            user=self.user,
            camera=self.camera,
            check_in_date=check_in,
            check_out_date=check_out,
            num_people=2,
            status='approved'
        )
        
        # Aggiungi un utente in lista d'attesa
        waiting = WaitingList.objects.create(
            user=self.user2,
            camera=self.camera,
            date=check_in,
            num_people=2
        )
        
        # Cancella la prenotazione
        booking.status = 'cancelled'
        booking.save()
        
        # Verifica che sia stata creata una notifica
        notification = Notification.objects.filter(user=self.user2).first()
        self.assertIsNotNone(notification)
        self.assertIn('disponibile', notification.message)
        
        # Verifica che l'entry in lista d'attesa sia stata marcata come notificata
        waiting.refresh_from_db()
        self.assertTrue(waiting.notified)

    def test_edge_case_date_validations(self):
        """
        Test per verificare la validazione delle date in casi limite
        """
        today = timezone.now().date()
        
        # Test prenotazione con check-out uguale a check-in
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                user=self.user,
                camera=self.camera,
                check_in_date=today + timedelta(days=1),
                check_out_date=today + timedelta(days=1),
                num_people=2,
                status='pending'
            )
        
        # Test prenotazione con durata superiore a 30 giorni
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                user=self.user,
                camera=self.camera,
                check_in_date=today + timedelta(days=1),
                check_out_date=today + timedelta(days=32),
                num_people=2,
                status='pending'
            )
        
        # Test prenotazione con date passate
        with self.assertRaises(ValidationError):
            Booking.objects.create(
                user=self.user,
                camera=self.camera,
                check_in_date=today - timedelta(days=2),
                check_out_date=today - timedelta(days=1),
                num_people=2,
                status='pending'
            )

class WaitingListAdvancedTest(TestCase):
    """Test avanzati per la gestione della lista d'attesa"""
    
    def setUp(self):
        self.client = Client()
        
        # Creazione utenti
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            user_type='CLIENTE'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123',
            user_type='CLIENTE'
        )
        self.user3 = User.objects.create_user(
            email='user3@test.com',
            password='testpass123',
            user_type='CLIENTE'
        )
        
        # Creazione gestore e profilo
        self.gestore = User.objects.create_user(
            email='gestore@test.com',
            password='testpass123',
            user_type='GESTORE'
        )
        
        self.gestore_profile = GestoreProfile.objects.create(
            user=self.gestore,
            partita_iva='12345678901',
            denominazione_sociale='Hotel Test',
            indirizzo_sede='Via Test 123'
        )
        
        #  Creazione struttura
        self.struttura = Struttura.objects.create(
            gestore=self.gestore_profile,  # Usa il profilo del gestore
            nome="Hotel Test",
            descrizione="Test desscrizione",  
            citta="Bologna",
            indirizzo="Via Test 1",
            tipologia="hotel"
        )
        
        # Create room
        self.camera = Camera.objects.create(
            struttura=self.struttura,
            numero_camera=101, 
            numero_persone=2,
            prezzo_per_notte=100.00, 
            descrizione="Camera test"
        )

    def test_multiple_waiting_list_entries(self):
        """
        Test per verificare la gestione di multiple richieste
        in lista d'attesa per la stessa camera
        """
        date = timezone.now().date() + timedelta(days=1)
        
        # Crea tre entry in lista d'attesa per la stessa data
        entries = []
        for user in [self.user1, self.user2, self.user3]:
            entries.append(WaitingList.objects.create(
                user=user,
                camera=self.camera,
                date=date,
                num_people=2
            ))
        
        # Crea e cancella una prenotazione per quella data
        booking = Booking.objects.create(
            user=User.objects.create_user(
                email='another@test.com',
                password='testpass123',
                user_type='CLIENTE'
            ),
            camera=self.camera,
            check_in_date=date,
            check_out_date=date + timedelta(days=1),
            num_people=2,
            status='approved'
        )
        
        booking.status = 'cancelled'
        booking.save()
        
        # Verifica che tutti gli utenti in lista d'attesa abbiano ricevuto una notifica
        for entry in entries:
            notification = Notification.objects.filter(user=entry.user).first()
            self.assertIsNotNone(notification)
            self.assertTrue(notification.waiting_list.notified)

    def test_waiting_list_unique_constraint(self):
        """
        Test per verificare il vincolo di unicità sulla lista d'attesa
        """
        date = timezone.now().date() + timedelta(days=1)
        
        # Crea prima entry
        WaitingList.objects.create(
            user=self.user1,
            camera=self.camera,
            date=date,
            num_people=2
        )
        
        # Prova a creare una seconda entry per lo stesso utente, camera e data
        with self.assertRaises(Exception):  # Potrebbe essere IntegrityError o ValidationError
            WaitingList.objects.create(
                user=self.user1,
                camera=self.camera,
                date=date,
                num_people=1  # Anche con numero persone diverso
            )