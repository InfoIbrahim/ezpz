from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),  # New URL for Admin Dashboard
    path('logout/', views.logout_view, name='logout'),
    path('ledger/', views.ledger_view, name='ledger_view'), #Added November 9, 2024 for Ledger View (nfc_data+.json to django)
]