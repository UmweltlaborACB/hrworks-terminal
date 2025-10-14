import requests
import logging
from typing import Optional
from django.conf import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HRworksAPIClient:
    BASE_URL = "https://api.hrworks.de/v2"

    def __init__(self):
        self.access_key = settings.HRWORKS_ACCESS_KEY
        self.secret_key = settings.HRWORKS_SECRET_KEY
        self.token = None
        self.token_expiry = None

    def _authenticate(self) -> bool:
        """Holt JWT-Token von HRworks"""
        try:
            response = requests.post(
                f"{self.BASE_URL}/authentication",
                json={
                    "accessKey": self.access_key,
                    "secretAccessKey": self.secret_key
                },
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.token_expiry = datetime.now() + timedelta(minutes=14)
                logger.info("HRworks Authentifizierung erfolgreich")
                return True
            else:
                logger.error(f"Authentifizierung fehlgeschlagen: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Fehler bei Authentifizierung: {str(e)}")
            return False

    def _get_token(self) -> Optional[str]:
        """Gibt gültigen Token zurück, authentifiziert neu falls nötig"""
        if not self.token or not self.token_expiry or datetime.now() >= self.token_expiry:
            if not self._authenticate():
                return None
        return self.token

    def get_personnel_number_by_chip(self, chip_id: str) -> Optional[str]:
        """
        Findet die Personalnummer anhand der Chip-ID
        
        Args:
            chip_id: RFID-Chip-ID
            
        Returns:
            Personalnummer oder None
        """
        token = self._get_token()
        if not token:
            logger.error("Konnte keinen gültigen Token erhalten")
            return None
        
        try:
            # Alle Mitarbeiter abrufen
            response = requests.get(
                f"{self.BASE_URL}/persons",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                persons = data.get('data', [])
                
                # Nach Chip-ID suchen
                chip_field = settings.HRWORKS_CHIP_ID_FIELD
                
                for person in persons:
                    # Chip-ID kann in verschiedenen Feldern sein
                    person_chip = person.get(chip_field, '').strip()
                    
                    if person_chip == chip_id:
                        personnel_number = person.get('personnelNumber')
                        logger.info(f"Chip {chip_id} → Personalnummer {personnel_number}")
                        return personnel_number
                
                logger.warning(f"Keine Personalnummer für Chip-ID {chip_id} gefunden")
                return None
            else:
                logger.error(f"Fehler beim Abrufen der Personen: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Fehler bei Chip-Suche: {str(e)}")
            return None

    def create_working_time(self, personnel_number: str, working_time_type: str) -> bool:
        """
        Erstellt eine Zeitbuchung in HRworks

        Args:
            personnel_number: Personalnummer des Mitarbeiters
            working_time_type: Typ der Zeitbuchung (work, businessTrip)

        Returns:
            True bei Erfolg, False bei Fehler
        """
        token = self._get_token()
        if not token:
            logger.error("Konnte keinen gültigen Token erhalten")
            return False

        try:
            now = datetime.now().strftime("%Y%m%dT%H%M%SZ")

            payload = {
                "data": [{
                    "personIdentifier": personnel_number,
                    "beginDateAndTime": now,
                    "workingTimeType": working_time_type
                }]
            }

            response = requests.post(
                f"{self.BASE_URL}/working-times",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code in [200, 201]:
                logger.info(f"Zeitbuchung erfolgreich für PN {personnel_number}: {working_time_type}")
                return True
            else:
                logger.error(f"Zeitbuchung fehlgeschlagen: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Fehler bei Zeitbuchung: {str(e)}")
            return False

    def book_time(self, chip_id: str, booking_type: str) -> bool:
        """
        Vereinfachte Methode: Von Chip-ID zur Zeitbuchung
        
        Args:
            chip_id: RFID-Chip-ID
            booking_type: "Kommen", "Gehen", "Dienstgang"
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        # Chip-ID → Personalnummer
        personnel_number = self.get_personnel_number_by_chip(chip_id)
        if not personnel_number:
            logger.error(f"Keine Personalnummer für Chip {chip_id} gefunden")
            return False
        
        # Booking-Type → HRworks-Type
        type_mapping = {
            "Kommen": "work",
            "Gehen": "work",  # Ende wird automatisch erkannt
            "Dienstgang": "businessTrip"
        }
        
        hrworks_type = type_mapping.get(booking_type)
        if not hrworks_type:
            logger.error(f"Unbekannter Buchungstyp: {booking_type}")
            return False
        
        # Zeitbuchung erstellen
        return self.create_working_time(personnel_number, hrworks_type)
