from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    # Autenticazione
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Registrazione
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register/gestore/', views.RegisterGestoreView.as_view(), name='register_gestore'),
    path('register/cliente/', views.RegisterClienteView.as_view(), name='register_cliente'),
    
    
    # Profilo utente
    path('profile/', views.ProfileView.as_view(), name='profile'),
    #path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
    #path('profile/update/', views.profile_update, name='profile_update'),
    
    # Dashboard
    path('dashboard/gestore/', views.dashboard_gestore, name='dashboard_gestore'),
    path('dashboard/cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('dashboard/aggiungi', views.aggiungi_struttura, name='aggiungi_struttura'),
    # Gestione strutture
    path('strutture/aggiungi/', views.aggiungi_struttura, name='aggiungi_struttura'),
    path('strutture/<int:struttura_id>/camere/', views.aggiungi_camere, name='aggiungi_camere'),
    path('le-mie-strutture/', views.le_mie_strutture, name='le_mie_strutture'),
    path('strutture/<int:pk>/', views.dettaglio_struttura, name='dettaglio_struttura'),
    path('struttura/<int:pk>/modifica/', views.modifica_struttura, name='modifica_struttura'),
    path('camera/<int:pk>/modifica/', views.modifica_camera, name='modifica_camera'),
    path('struttura/<int:struttura_id>/elimina/', views.elimina_struttura, name='elimina_struttura'),
    path('camera/<int:camera_id>/elimina/', views.elimina_camera, name='elimina_camera'),
    path('struttura/<int:pk>/pubblico/', views.dettaglio_struttura_pubblico, name='dettaglio_struttura_pubblico'),
    path('camera/<int:pk>/pubblico/', views.dettaglio_camera_pubblico, name='dettaglio_camera_pubblico'),
]