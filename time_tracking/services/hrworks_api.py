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
        logger.info("🔧 HRworksAPIClient initialisiert")

    def _authenticate(self) -> bool:
        """Holt JWT-Token von HRworks"""
        logger.info("🔑 Authentifizierung bei HRworks wird gestartet...")
        
        try:
            url = f"{self.BASE_URL}/authentication"
            logger.info(f"📡 POST {url}")
            
            payload = {
                "accessKey": self.access_key,
                "secretAccessKey": self.secret_key
            }
            logger.info(f"🔐 AccessKey: {self.access_key[:10]}...")
            
            response = requests.post(
                url,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                timeout=10
            )

            logger.info(f"📥 Status Code: {response.status_code}")
            logger.info(f"📥 Response Text: {response.text[:200]}")

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.token_expiry = datetime.now() + timedelta(minutes=14)
                logger.info(f"✅ Token erhalten: {self.token[:20]}...")
                logger.info(f"⏰ Token gültig bis: {self.token_expiry}")
                return True
            else:
                logger.error(f"❌ Authentifizierung fehlgeschlagen: {response.status_code}")
                logger.error(f"📄 Response: {response.text}")
                return False

        except requests.exceptions.Timeout:
            logger.error("⏱️ Timeout bei Authentifizierung")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 Netzwerkfehler bei Authentifizierung: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"💥 Unerwarteter Fehler bei Authentifizierung: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _get_token(self) -> Optional[str]:
        """Gibt gültigen Token zurück, authentifiziert neu falls nötig"""
        logger.info("🎫 Token wird geprüft...")
        
        if not self.token:
            logger.info("❌ Kein Token vorhanden → Authentifizierung erforderlich")
        elif not self.token_expiry:
            logger.info("❌ Token-Ablaufzeit fehlt → Authentifizierung erforderlich")
        elif datetime.now() >= self.token_expiry:
            logger.info(f"⏰ Token abgelaufen (seit {datetime.now() - self.token_expiry}) → Neue Authentifizierung")
        else:
            logger.info(f"✅ Token noch gültig bis {self.token_expiry}")
            return self.token
        
        if not self._authenticate():
            logger.error("❌ Konnte Token nicht erneuern")
            return None
        return self.token

    def get_personnel_number_by_chip(self, chip_id: str) -> Optional[str]:
        """Findet die Personalnummer anhand der Chip-ID"""
        logger.info(f"🔍 Suche Personalnummer für Chip-ID: '{chip_id}'")
        
        try:
            chip_id = chip_id.strip()
            logger.info(f"🧹 Bereinigte Chip-ID: '{chip_id}'")
            
            mapping = ChipMapping.objects.get(transponder_id=chip_id)
            logger.info(f"✅ Mapping gefunden: {mapping.last_name}, {mapping.first_name} (PN: {mapping.personnel_number})")
            return mapping.personnel_number

        except ChipMapping.DoesNotExist:
            logger.warning(f"❌ Keine Zuordnung für Chip-ID '{chip_id}' gefunden")
            # Debug: Zeige alle vorhandenen Chip-IDs
            all_chips = ChipMapping.objects.values_list('transponder_id', flat=True)
            logger.info(f"📋 Vorhandene Chip-IDs: {list(all_chips)}")
            return None
        except Exception as e:
            logger.error(f"💥 Fehler beim Chip-Lookup: {type(e).__name__}: {str(e)}")
            return None

    def create_working_time(self, personnel_number: str, action: str) -> bool:
        """
        Erstellt eine Zeitbuchung in HRworks

        Args:
            personnel_number: Personalnummer des Mitarbeiters
            action: 'clockIn' oder 'clockOut'
        """
        logger.info(f"⏰ Zeitbuchung wird erstellt...")
        logger.info(f"👤 Personalnummer: {personnel_number}")
        logger.info(f"📝 Action: {action}")
        
        token = self._get_token()
        if not token:
            logger.error("❌ Konnte keinen gültigen Token erhalten")
            return False

        try:
            url = f"{self.BASE_URL}/persons/{personnel_number}/working-times"

            headers = {
                "Authorization": f"Bearer {token[:20]}...",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }

            params = {
                "action": action,
                "type": "workingTime"
            }

            logger.info(f"📡 POST {url}")
            logger.info(f"📋 Query-Parameter: {params}")
            logger.info(f"🔐 Header: Authorization=Bearer {token[:20]}...")

            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",  # Vollständiger Token
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                params=params, 
                timeout=30
            )

            logger.info(f"📥 Status Code: {response.status_code}")
            logger.info(f"📥 Response Headers: {dict(response.headers)}")
            logger.info(f"📥 Response Body: {response.text}")

            if response.status_code in [200, 201, 204]:
                logger.info(f"✅ Zeitbuchung erfolgreich für PN {personnel_number}: {action}")
                return True
            else:
                logger.error(f"❌ Zeitbuchung fehlgeschlagen")
                logger.error(f"Status: {response.status_code}")
                logger.error(f"Body: {response.text}")
                return False

        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Timeout bei HRworks-Request")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 Netzwerkfehler: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"💥 Fehler bei Zeitbuchung: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def book_time(self, chip_id: str, booking_type: str) -> bool:
        """
        Zeitbuchung

        Args:
            chip_id: RFID-Chip-ID
            booking_type: "kommen", "gehen", "dienstgang_start", "dienstgang_ende"
        """
        logger.info("=" * 60)
        logger.info(f"🎯 book_time() aufgerufen")
        logger.info(f"🔑 Chip-ID: {chip_id}")
        logger.info(f"📝 Booking-Type: {booking_type}")
        logger.info("=" * 60)
        
        # Chip-ID → Personalnummer
        personnel_number = self.get_personnel_number_by_chip(chip_id)
        if not personnel_number:
            logger.error(f"❌ Keine Personalnummer für Chip {chip_id} gefunden")
            return False

        # Booking-Type → HRworks-Action (lowercase!)
        action_mapping = {
            "kommen": "clockIn",
            "gehen": "clockOut",  
            "dienstgang_start": "clockIn",
            "dienstgang_ende": "clockOut"
        }

        action = action_mapping.get(booking_type.lower())
        logger.info(f"🔄 Mapping: '{booking_type}' → '{action}'")
        
        if not action:
            logger.error(f"❌ Unbekannter Buchungstyp: '{booking_type}'")
            logger.info(f"📋 Gültige Typen: {list(action_mapping.keys())}")
            return False

        # Zeitbuchung erstellen
        logger.info(f"➡️ Rufe create_working_time() auf...")
        result = self.create_working_time(personnel_number, action)
        logger.info(f"{'✅' if result else '❌'} Ergebnis: {result}")
        logger.info("=" * 60)
        return result
