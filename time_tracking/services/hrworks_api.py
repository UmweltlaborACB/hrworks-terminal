import requests
from django.conf import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class HRworksAPIClient:
    """
    Client für die HRworks API v2
    """
    
    def __init__(self):
        self.api_url = settings.HRWORKS_API_URL
        self.access_token = settings.HRWORKS_ACCESS_TOKEN
        self.chip_id_field = settings.HRWORKS_CHIP_ID_FIELD
        
        if not self.api_url or not self.access_token:
            raise ValueError("HRworks API URL und Access Token müssen in .env konfiguriert sein")
    
    def _get_headers(self) -> Dict[str, str]:
        """Erstellt die Header für API-Requests"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
    
    def find_employee_by_chip_id(self, chip_id: str) -> Optional[Dict[str, Any]]:
        """
        Sucht einen Mitarbeiter anhand der Chip-ID
        
        Args:
            chip_id: Die RFID-Chip-ID
            
        Returns:
            Dictionary mit Mitarbeiterdaten oder None wenn nicht gefunden
        """
        try:
            # HRworks API v2 - Persons Endpoint
            url = f"{self.api_url}/persons"
            
            # Filter nach dem Custom-Field mit der Chip-ID
            params = {
                'filter': f'{self.chip_id_field}=={chip_id}'
            }
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Prüfen ob Mitarbeiter gefunden wurde
            if data and len(data) > 0:
                employee = data[0]
                logger.info(f"Mitarbeiter gefunden: {employee.get('firstName')} {employee.get('lastName')}")
                return employee
            else:
                logger.warning(f"Kein Mitarbeiter mit Chip-ID {chip_id} gefunden")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler bei der API-Anfrage: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unerwarteter Fehler: {str(e)}")
            return None
    
    def create_time_booking(self, personnel_number: str, booking_type: str) -> bool:
        """
        Erstellt eine Zeitbuchung in HRworks
        
        Args:
            personnel_number: Die Personalnummer des Mitarbeiters
            booking_type: Art der Buchung ('come', 'go', 'business_trip')
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Mapping der Buchungstypen zu HRworks-Typen
            type_mapping = {
                'come': 'come',
                'go': 'go',
                'business_trip': 'business_trip'
            }
            
            hrworks_type = type_mapping.get(booking_type)
            if not hrworks_type:
                logger.error(f"Ungültiger Buchungstyp: {booking_type}")
                return False
            
            # HRworks API v2 - Time Tracking Endpoint
            url = f"{self.api_url}/time-trackings"
            
            payload = {
                'personnelNumber': personnel_number,
                'type': hrworks_type,
                # Zeitstempel wird serverseitig gesetzt
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            logger.info(f"Buchung erfolgreich für Personalnummer {personnel_number}: {booking_type}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Erstellen der Buchung: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"API-Antwort: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Buchen: {str(e)}")
            return False
    
    def get_employee_name(self, employee_data: Dict[str, Any]) -> str:
        """
        Extrahiert den vollständigen Namen aus den Mitarbeiterdaten
        
        Args:
            employee_data: Mitarbeiterdaten von der API
            
        Returns:
            Vollständiger Name
        """
        first_name = employee_data.get('firstName', '')
        last_name = employee_data.get('lastName', '')
        return f"{first_name} {last_name}".strip()
    
    def get_personnel_number(self, employee_data: Dict[str, Any]) -> str:
        """
        Extrahiert die Personalnummer aus den Mitarbeiterdaten
        
        Args:
            employee_data: Mitarbeiterdaten von der API
            
        Returns:
            Personalnummer
        """
        return employee_data.get('personnelNumber', '')
