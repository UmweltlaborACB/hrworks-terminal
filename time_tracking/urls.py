from django.urls import path
from .views import ScanView, BookingView, CheckChipView
from time_tracking import views

urlpatterns = [
    path('', ScanView.as_view(), name='scan'),
    path('api/check-chip/', views.check_new_chip, name='check_chip'),
    path('booking/', BookingView.as_view(), name='booking'),
]
