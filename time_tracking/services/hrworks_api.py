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
                # Token ist 15 Minuten gültig, wir erneuern nach 14 Min
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
    
    def create_working_time(self, personnel_number: str, working_time_type: str) -> bool:
        """
        Erstellt eine Zeitbuchung in HRworks
        
        Args:
            personnel_number: Personalnummer des Mitarbeiters
            working_time_type: Typ der Zeitbuchung (work, break, businessTrip)
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        token = self._get_token()
        if not token:
            logger.error("Konnte keinen gültigen Token erhalten")
            return False
        
        try:
            # Aktueller Zeitstempel im Format YYYYMMDDTHHMMSSZ
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
