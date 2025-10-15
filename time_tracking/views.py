from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from .services.hrworks_api import HRworksAPIClient
from .models import ChipMapping
import logging

logger = logging.getLogger(__name__)

class ScanView(View):
    """Startseite - Warten auf RFID-Chip"""
    
    def get(self, request):
        return render(request, 'time_tracking/scan.html')

    
class BookingView(View):
    """Zeigt Buchungsoptionen nach erfolgreichem Scan"""
    
    def get(self, request):
        chip_id = request.GET.get('chip_id')
        
        if not chip_id:
            messages.error(request, 'Keine Chip-ID erkannt!')
            return redirect('scan')
        
        # Chip-ID im Session speichern
        request.session['chip_id'] = chip_id
        
        # Chip-Mapping holen
        try:
            chip_mapping = ChipMapping.objects.get(transponder_id=chip_id)
            full_name = f"{chip_mapping.first_name} {chip_mapping.last_name}" if chip_mapping.first_name else chip_mapping.last_name
        except ChipMapping.DoesNotExist:
            full_name = None
            logger.warning(f"Kein Mapping für Chip-ID {chip_id} gefunden")
        
        logger.info(f"Chip erkannt: {chip_id} ({full_name})")
        
        context = {
            'chip_id': chip_id,
            'full_name': full_name,
            'first_name': chip_mapping.first_name if chip_mapping else None,
        }
        return render(request, 'time_tracking/booking.html', context)