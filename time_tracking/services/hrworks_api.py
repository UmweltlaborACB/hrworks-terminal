import requests
import logging
from typing import Dict, Any, Optional
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
        """Holt JWT-Token von HRworks gemäß API-Spezifikation"""
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
                logger.info("JWT-Token erfolgreich abgerufen")
                return True
            else:
                logger.error(f"Authentifizierung fehlgeschlagen: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Fehler bei Authentifizierung: {str(e)}")
            return False
    
    def _ensure_token(self) -> bool:
        """Stellt sicher, dass ein gültiger Token vorhanden ist"""
        if not self.token or not self.token_expiry or datetime.now() >= self.token_expiry:
            return self._authenticate()
        return True
    
    def _get_headers(self) -> Dict[str, str]:
        """Gibt Header mit JWT-Token zurück"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def create_working_time(self, personnel_number: str, working_time_type: str) -> bool:
        """
        Erstellt eine Zeitbuchung (Start/Ende/Dienstgang)
        
        Args:
            personnel_number: Personalnummer des Mitarbeiters
            working_time_type: 'start', 'end' oder 'business_trip'
        
        Returns:
            bool: True bei Erfolg
        """
        if not self._ensure_token():
            logger.error("Konnte keinen gültigen Token erhalten")
            return False
            
        try:
            # Zeitstempel im korrekten Format: YYYYMMDD"T"HHMMSS"Z"
            now = datetime.utcnow()
            timestamp = now.strftime("%Y%m%dT%H%M%SZ")
            
            # Payload gemäß API-Spezifikation
            payload = {
                "data": [{
                    "personnelNumber": personnel_number,
                    "beginDateAndTime": timestamp,
                    "workingTimeType": working_time_type
                }]
            }
            
            # Falls 'end' - dann auch endDateAndTime setzen
            if working_time_type == 'end':
                payload["data"][0]["endDateAndTime"] = timestamp
            
            logger.info(f"Sende Zeitbuchung: {payload}")
            
            response = requests.post(
                f"{self.BASE_URL}/working-times",
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Zeitbuchung erfolgreich: {working_time_type} für PN {personnel_number}")
                return True
            else:
                logger.error(f"Fehler bei Zeitbuchung: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Fehler bei create_working_time: {str(e)}")
            return False
    
    def get_employee_name(self, employee_data: Dict[str, Any]) -> str:
        """Extrahiert Namen aus lokalen Mitarbeiterdaten"""
        return employee_data.get('name', 'Unbekannt')
    
    def get_personnel_number(self, employee_data: Dict[str, Any]) -> str:
        """Extrahiert Personalnummer aus lokalen Daten"""
        return employee_data.get('personnel_number', '')
