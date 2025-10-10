from django.urls import path
from .views import WaitingView, BookingView, SuccessView, ManualScanView, ProcessChipView

urlpatterns = [
    path('', WaitingView.as_view(), name='waiting'),
    path('booking/', BookingView.as_view(), name='booking'),
    path('success/', SuccessView.as_view(), name='success'),
    path('manual-scan/', ManualScanView.as_view(), name='manual_scan'),
    path('process-chip/', ProcessChipView.as_view(), name='process_chip'),  # NEU für USB-Reader
]
