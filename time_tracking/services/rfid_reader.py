import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

#
#Aktuell nicht erforderlich, da über JavaScript ausgelesen wird.
#
class RFIDReader:
    def __init__(self):
        self.reader_url = settings.RFID_READER_URL
    
    def read_chip(self) -> str:
        """
        Liest Chip-ID vom RFID-Reader
        
        Returns:
            Chip-ID als String oder None bei Fehler
        """
        try:
            response = requests.get(
                f"{self.reader_url}/read",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                chip_id = data.get('chip_id')
                
                if chip_id:
                    logger.info(f"Chip gelesen: {chip_id}")
                    return chip_id
                else:
                    logger.warning("Kein Chip erkannt")
                    return None
            else:
                logger.error(f"RFID-Reader Fehler: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("RFID-Reader Timeout")
            return None
        except Exception as e:
            logger.error(f"Fehler beim Chip-Lesen: {str(e)}")
            return None
