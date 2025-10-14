from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.utils import timezone
from .services.hrworks_api import HRworksAPIClient
from .services.rfid_reader import get_rfid_reader
from .models import ChipMapping, BookingLog, Employee
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils.decorators import method_decorator
import json
import logging


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ProcessChipView(View):
    def post(self, request):
        try:
            import json
            data = json.loads(request.body)
            chip_id = data.get('chip_id')
            
            if not chip_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Keine Chip-ID empfangen'
                })
            
            logger.info(f"Chip gescannt: {chip_id}")
            
            # Suche in lokaler Datenbank
            try:
                employee = Employee.objects.get(chip_id=chip_id)
                
                # Speichere in Session
                request.session['chip_id'] = chip_id
                request.session['employee'] = {
                    'personnel_number': employee.personnel_number,
                    'name': employee.name
                }
                
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/booking/'
                })
                
            except Employee.DoesNotExist:
                logger.warning(f"Kein Mitarbeiter für Chip {chip_id} gefunden")
                return JsonResponse({
                    'success': False,
                    'error': 'Chip nicht zugeordnet'
                })
            
        except Exception as e:
            logger.error(f"Fehler bei process_chip: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })




class WaitingView(View):
    #"""
    #Startseite - wartet auf Chip-Scan
    #"""
    template_name = 'time_tracking/waiting.html'
    
    def get(self, request):
        #"""Zeigt die Warteseite an"""
        return render(request, self.template_name)
    
    def post(self, request):
        #"""
        #Wird aufgerufen wenn ein Chip gescannt wurde
        #(z.B. durch JavaScript Polling oder manuellen Scan-Button)
        #"""
        # RFID-Reader initialisieren
        reader = get_rfid_reader()
        
        # Chip lesen
        chip_id = reader.read_chip_id_no_block()
        
        if not chip_id:
            messages.error(request, "Kein Chip erkannt. Bitte erneut versuchen.")
            return redirect('waiting')
        
        # Chip-ID in Session speichern
        request.session['chip_id'] = chip_id
        
        # Mitarbeiter über HRworks API suchen
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
    def post(self, request):
        try:
            booking_type = request.POST.get('booking_type')
            employee = request.session.get('employee')
            
            if not employee:
                return JsonResponse({
                    'success': False,
                    'error': 'Keine Sitzungsdaten'
                })
            
            # Mapping zu HRworks workingTimeType
            type_mapping = {
                'coming': 'start',
                'going': 'end',
                'business_trip': 'business_trip'
            }
            
            hrworks_type = type_mapping.get(booking_type)
            if not hrworks_type:
                return JsonResponse({
                    'success': False,
                    'error': 'Ungültiger Buchungstyp'
                })
            
            # API-Call
            api_client = HRworksAPIClient()
            success = api_client.create_working_time(
                employee['personnel_number'],
                hrworks_type
            )
            
            if success:
                # Session löschen
                request.session.flush()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Zeitbuchung erfolgreich'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Zeitbuchung fehlgeschlagen'
                })
                
        except Exception as e:
            logger.error(f"Fehler bei Zeitbuchung: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })



class SuccessView(View):
    #"""
    #Erfolgsseite - zeigt Bestätigung und leitet zurück zur Warteseite
    #"""
    template_name = 'time_tracking/success.html'
    
    def get(self, request):
        """Zeigt Erfolgs- oder Fehlermeldung an"""
        employee_name = request.session.get('employee_name')
        booking_type = request.session.get('last_booking_type')
        success = request.session.get('last_booking_success', False)
        
        # Buchungstyp für Anzeige übersetzen
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
    #"""
    #Manuelle Scan-Ansicht für Entwicklung/Testing
    #Ermöglicht manuelles Triggern eines Chip-Scans
    #"""
    template_name = 'time_tracking/manual_scan.html'
    
    def get(self, request):
        """Zeigt Formular für manuellen Scan"""
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
        
        # Session füllen
        request.session['personnel_number'] = api_client.get_personnel_number(employee_data)
        request.session['employee_name'] = api_client.get_employee_name(employee_data)
        
        return redirect('booking')
