from django.urls import path
from .views import ScanView, BookingView

app_name = 'time_tracking'

urlpatterns = [
    path('', ScanView.as_view(), name='scan'),
    path('booking/', BookingView.as_view(), name='booking'),
]