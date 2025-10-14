from django.urls import path
from .views import ScanView, BookingView, ProcessChipView

app_name = 'time_tracking'

urlpatterns = [
    path('', ScanView.as_view(), name='scan'),
    path('booking/', BookingView.as_view(), name='booking'),
    path('process-chip/', ProcessChipView.as_view(), name='process_chip'),
]