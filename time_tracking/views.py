from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.conf import settings
from .services.hrworks_api import HRworksAPIClient
from .models import ChipMapping
import logging

logger = logging.getLogger(__name__)

    
class ScanView(View):
    """Startseite - Chip scannen"""

    #Firmennamen aus settings holen
    def get(self, request):
        context = {
            'company_name': settings.COMPANY_NAME,
        }
        return render(request, 'time_tracking/scan.html', context)

    
class BookingView(View):
    """Zeigt Buchungsoptionen nach erfolgreichem Scan"""
    
    def get(self, request):
        chip_id = request.GET.get('chip_id')
        
        if not chip_id:
            messages.error(request, 'Keine Chip-ID erkannt!')
            return redirect('scan')
        
        # Chip-ID im Session speichern
        request.session['chip_id'] = chip_id

        # Chip-Mapping holen um den Namen zur Begrüßung anzuzeigen
        try:
            chip_mapping = ChipMapping.objects.get(transponder_id=chip_id)
            name = f"{chip_mapping.first_name}" if chip_mapping.first_name else chip_mapping.last_name
        except ChipMapping.DoesNotExist:
            name = None
            logger.warning(f"Kein Mapping für Chip-ID {chip_id} gefunden")
            messages.error(request, 'Kein Mapping für Chip-ID {chip_id} gefunden')
            return redirect('scan')
        
        logger.info(f"Chip erkannt: {chip_id}")
        
        context = {
            'chip_id': chip_id,
            'full_name': name,
            'first_name': name,
        }

       #context = {
       #     'chip_id': chip_id,
       #     'full_name': full_name,
       #     'first_name': chip_mapping.first_name if chip_mapping else None,
       #}

        return render(request, 'time_tracking/booking.html', context)
    
    def post(self, request):
        """Verarbeitet die Buchung"""
        chip_id = request.session.get('chip_id')
        booking_type = request.POST.get('booking_type')
        
        if not chip_id:
            messages.error(request, 'Chip-ID verloren gegangen!')
            return redirect('scan')
        
        if not booking_type:
            messages.error(request, 'Bitte Buchungsart wählen!')
            return redirect('booking')
        
        try:
            # HRworks API aufrufen
            hrworks_client = HRworksAPIClient()  
            result = hrworks_client.book_time(chip_id, booking_type)
            
            if result:
                messages.success(request, f'✅ {booking_type} erfolgreich gebucht!')
            else:
                messages.error(request, '❌ Buchung fehlgeschlagen!')
            
        except Exception as e:
            logger.error(f"Fehler bei Buchung: {str(e)}")
            messages.error(request, f'❌ Fehler: {str(e)}')
        
        # Session aufräumen
        if 'chip_id' in request.session:
            del request.session['chip_id']
        
        # Zurück zur Scan-Seite
        return redirect('scan')