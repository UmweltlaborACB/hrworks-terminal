from django.urls import path
from .views import ScanView, BookingView, CheckChipView

urlpatterns = [
    path('', ScanView.as_view(), name='scan'),
    path('check-chip/', CheckChipView.as_view(), name='check_chip'),
    path('booking/', BookingView.as_view(), name='booking'),
]
