import logging
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Employee
from .services.hrworks_api import HRworksAPIClient
from .services.rfid_reader import RFIDReader

logger = logging.getLogger(__name__)


class ScanView(View):
    """Startseite: Bitte Chip auflegen"""
    
    def get(self, request):
        # Session leeren beim Laden der Scan-Seite
        request.session.flush()
        return render(request, 'time_tracking/scan.html')


@method_decorator(csrf_exempt, name='dispatch')
class ProcessChipView(View):
    """AJAX-Endpoint: Chip-ID vom Reader empfangen"""
    
    def post(self, request):
        try:
            # Chip-ID vom RFID-Reader holen
            reader = RFIDReader()
            chip_id = reader.read_chip()
            
            if not chip_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Kein Chip erkannt'
                })
            
            # Mitarbeiter in DB suchen
            try:
                employee = Employee.objects.get(chip_id=chip_id, is_active=True)
            except Employee.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Chip nicht registriert'
                })
            
            # Mitarbeiter in Session speichern
            request.session['employee_id'] = employee.id
            request.session['employee_name'] = employee.name
            request.session['personnel_number'] = employee.personnel_number
            
            return JsonResponse({
                'success': True,
                'redirect': '/booking/'
            })
            
        except Exception as e:
            logger.error(f"Fehler beim Chip-Lesen: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Technischer Fehler: {str(e)}'
            })


class BookingView(View):
    """Buchungsauswahl: Kommen, Gehen, Dienstgang, Pause"""
    
    def get(self, request):
        # Prüfen ob Mitarbeiter in Session
        employee_name = request.session.get('employee_name')
        if not employee_name:
            return render(request, 'time_tracking/scan.html')
        
        context = {
            'employee_name': employee_name
        }
        return render(request, 'time_tracking/booking.html', context)
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Zeitbuchung durchführen"""
        try:
            # Mitarbeiter aus Session
            personnel_number = request.session.get('personnel_number')
            if not personnel_number:
                return JsonResponse({
                    'success': False,
                    'error': 'Keine Session gefunden'
                })
            
            # Buchungstyp aus POST-Daten
            booking_type = request.POST.get('booking_type')
            
            # Mapping zu HRworks WorkingTimeType
            type_mapping = {
                'kommen': 'work',
                'gehen': 'work',
                'dienstgang_start': 'businessTrip',
                'dienstgang_ende': 'businessTrip',
                'pause_start': 'break',
                'pause_ende': 'break'
            }
            
            hrworks_type = type_mapping.get(booking_type)
            if not hrworks_type:
                return JsonResponse({
                    'success': False,
                    'error': 'Ungültiger Buchungstyp'
                })
            
            # API-Call
            api_client = HRworksAPIClient()
            success = api_client.create_working_time(personnel_number, hrworks_type)
            
            if success:
                # Session leeren
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
