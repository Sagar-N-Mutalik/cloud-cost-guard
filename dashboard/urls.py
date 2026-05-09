from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register, name='register'),
    path('delete/<int:account_id>/', views.delete_account, name='delete_account'),
    path('scan/<int:account_id>/', views.manual_scan, name='manual_scan'),
]