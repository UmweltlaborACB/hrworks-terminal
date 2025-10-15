import requests
import logging
from typing import Optional
from django.conf import settings
from datetime import datetime, timedelta
from ..models import ChipMapping

logger = logging.getLogger(__name__)

class HRworksAPIClient:
    BASE_URL = settings.HRWORKS_API_URL

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
                logger.info("✅ HRworks Authentifizierung erfolgreich")
                return True
            else:
                logger.error(f"❌ Authentifizierung fehlgeschlagen: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Fehler bei Authentifizierung: {str(e)}")
            return False

    def _get_token(self) -> Optional[str]:
        """Gibt gültigen Token zurück, authentifiziert neu falls nötig"""
        if not self.token or not self.token_expiry or datetime.now() >= self.token_expiry:
            if not self._authenticate():
                return None
        return self.token

    def get_personnel_number_by_chip(self, chip_id: str) -> Optional[str]:
        """Findet die Personalnummer anhand der Chip-ID"""
        try:
            chip_id = chip_id.strip()
            mapping = ChipMapping.objects.get(transponder_id=chip_id)
            logger.info(f"✅ Chip {chip_id} → {mapping.last_name} ({mapping.personnel_number})")
            return mapping.personnel_number

        except ChipMapping.DoesNotExist:
            logger.warning(f"❌ Keine Zuordnung für Chip-ID '{chip_id}' gefunden")
            return None

    def create_working_time(self, personnel_number: str, action: str) -> bool:
        """
        Erstellt eine Zeitbuchung in HRworks
        
        Args:
            personnel_number: Personalnummer des Mitarbeiters
            action: 'clockIn' oder 'clockOut'
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        token = self._get_token()
        if not token:
            logger.error("❌ Konnte keinen gültigen Token erhalten")
            return False

        try:
            url = f"{self.BASE_URL}/persons/{personnel_number}/working-times"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            params = {
                "action": action,
                "type": "ACB AZ"
            }
            
            logger.info(f"🔵 API Request: POST {url}?action={action}")
            
            response = requests.post(
                url,
                headers=headers,
                params=params,  # ✅ Nur Query-Parameter!
                timeout=30
            )
            
            logger.info(f"📥 Status: {response.status_code}")
            logger.info(f"📥 Response: {response.text}")

            if response.status_code in [200, 201, 204]:
                logger.info(f"✅ Zeitbuchung erfolgreich für PN {personnel_number}: {action}")
                return True
            else:
                logger.error(f"❌ Zeitbuchung fehlgeschlagen: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Fehler bei Zeitbuchung: {str(e)}")
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
            logger.error(f"❌ Keine Personalnummer für Chip {chip_id} gefunden")
            return False

        # Booking-Type → HRworks-Action
        action_mapping = {
            "Kommen": "clockIn",
            "Gehen": "clockOut",  
            "Dienstgang": "clockIn"  # ✅ Dienstgang ist auch ein clockIn
        }

        action = action_mapping.get(booking_type)
        if not action:
            logger.error(f"❌ Unbekannter Buchungstyp: {booking_type}")
            return False

        # Zeitbuchung erstellen
        return self.create_working_time(personnel_number, action)
