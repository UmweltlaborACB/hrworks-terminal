from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.utils import timezone
from .services.hrworks_api import HRworksAPIClient
from .services.rfid_reader import get_rfid_reader
from .models import ChipMapping, BookingLog
import logging

logger = logging.getLogger(__name__)


class WaitingView(View):
    """
    Startseite - wartet auf Chip-Scan
    """
    template_name = 'time_tracking/waiting.html'
    
    def get(self, request):
        """Zeigt die Warteseite an"""
        return render(request, self.template_name)
    
    def post(self, request):
        """
        Wird aufgerufen wenn ein Chip gescannt wurde
        (z.B. durch JavaScript Polling oder manuellen Scan-Button)
        """
        # RFID-Reader initialisieren
        reader = get_rfid_reader()
        
        # Chip lesen
        chip_id = reader.read_chip_id_no_block()
        
        if not chip_id:
            messages.error(request, "Kein Chip erkannt. Bitte erneut versuchen.")
            return redirect('waiting')
        
        # Chip-ID in Session speichern
        request.session['chip_id'] = chip_id
        
        # Mitarbeiter �ber HRworks API suchen
        api_client = HRworksAPIClient()
        employee_data = api_client.find_employee_by_chip_id(chip_id)
        
        if not employee_data:
            messages.error(request, "Chip nicht zugeordnet. Bitte wenden Sie sich an die Personalabteilung.")
            logger.warning(f"Unbekannte Chip-ID: {chip_id}")
            return redirect('waiting')
        
        # Mitarbeiterdaten in Session speichern
        request.session['personnel_number'] = api_client.get_personnel_number(employee_data)
        request.session['employee_name'] = api_client.get_employee_name(employee_data)
        
        # Zur Buchungsseite weiterleiten
        return redirect('booking')


class BookingView(View):
    """
    Buchungsseite - zeigt Kommen/Gehen/Dienstgang Buttons
    """
    template_name = 'time_tracking/booking.html'
    
    def get(self, request):
        """Zeigt die Buchungsseite mit Buttons an"""
        # Pr�fen ob Mitarbeiter authentifiziert ist
        employee_name = request.session.get('employee_name')
        
        if not employee_name:
            messages.warning(request, "Bitte zuerst Chip scannen.")
            return redirect('waiting')
        
        context = {
            'employee_name': employee_name,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        """
        Verarbeitet die Zeitbuchung
        """
        # Session-Daten holen
        chip_id = request.session.get('chip_id')
        personnel_number = request.session.get('personnel_number')
        employee_name = request.session.get('employee_name')
        
        if not all([chip_id, personnel_number, employee_name]):
            messages.error(request, "Session abgelaufen. Bitte erneut scannen.")
            return redirect('waiting')
        
        # Buchungstyp aus POST-Daten
        booking_type = request.POST.get('booking_type')
        
        if booking_type not in ['come', 'go', 'business_trip']:
            messages.error(request, "Ung�ltiger Buchungstyp.")
            return redirect('booking')
        
        # Buchung durchf�hren
        api_client = HRworksAPIClient()
        success = api_client.create_time_booking(personnel_number, booking_type)
        
        # Buchung loggen
        BookingLog.objects.create(
            chip_id=chip_id,
            personnel_number=personnel_number,
            employee_name=employee_name,
            booking_type=booking_type,
            timestamp=timezone.now(),
            success=success,
            error_message=None if success else "API-Fehler"
        )
        
        # Ergebnis speichern f�r Success-Seite
        request.session['last_booking_type'] = booking_type
        request.session['last_booking_success'] = success
        
        return redirect('success')


class SuccessView(View):
    """
    Erfolgsseite - zeigt Best�tigung und leitet zur�ck zur Warteseite
    """
    template_name = 'time_tracking/success.html'
    
    def get(self, request):
        """Zeigt Erfolgs- oder Fehlermeldung an"""
        employee_name = request.session.get('employee_name')
        booking_type = request.session.get('last_booking_type')
        success = request.session.get('last_booking_success', False)
        
        # Buchungstyp f�r Anzeige �bersetzen
        booking_type_display = {
            'come': 'Kommen',
            'go': 'Gehen',
            'business_trip': 'Dienstgang'
        }.get(booking_type, 'Unbekannt')
        
        context = {
            'employee_name': employee_name,
            'booking_type': booking_type_display,
            'success': success,
        }
        
        # Session bereinigen
        request.session.flush()
        
        return render(request, self.template_name, context)


class ManualScanView(View):
    """
    Manuelle Scan-Ansicht f�r Entwicklung/Testing
    Erm�glicht manuelles Triggern eines Chip-Scans
    """
    template_name = 'time_tracking/manual_scan.html'
    
    def get(self, request):
        """Zeigt Formular f�r manuellen Scan"""
        return render(request, self.template_name)
    
    def post(self, request):
        """Verarbeitet manuellen Scan"""
        chip_id = request.POST.get('chip_id', '').strip()
        
        if not chip_id:
            messages.error(request, "Bitte Chip-ID eingeben.")
            return redirect('manual_scan')
        
        # Chip-ID in Session speichern und wie normaler Scan behandeln
        request.session['chip_id'] = chip_id
        
        # Mitarbeiter suchen
        api_client = HRworksAPIClient()
        employee_data = api_client.find_employee_by_chip_id(chip_id)
        
        if not employee_data:
            messages.error(request, f"Kein Mitarbeiter mit Chip-ID {chip_id} gefunden.")
            return redirect('manual_scan')
        
        # Session f�llen
        request.session['personnel_number'] = api_client.get_personnel_number(employee_data)
        request.session['employee_name'] = api_client.get_employee_name(employee_data)
        
        return redirect('booking')
