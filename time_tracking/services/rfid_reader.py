import logging
from typing import Optional
try:
    from mfrc522 import SimpleMFRC522
    import RPi.GPIO as GPIO
    RFID_AVAILABLE = True
except ImportError:
    RFID_AVAILABLE = False
    logging.warning("RFID-Bibliotheken nicht verfügbar. Entwicklungsmodus aktiv.")

logger = logging.getLogger(__name__)


class RFIDReader:
    #"""
    #Wrapper für den MFRC522 RFID-Reader
    #"""
    
    def __init__(self):
        self.reader = None
        if RFID_AVAILABLE:
            try:
                self.reader = SimpleMFRC522()
                logger.info("RFID-Reader erfolgreich initialisiert")
            except Exception as e:
                logger.error(f"Fehler beim Initialisieren des RFID-Readers: {str(e)}")
                self.reader = None
        else:
            logger.warning("RFID-Reader im Entwicklungsmodus - keine Hardware verfügbar")
    
    def read_chip_id(self, timeout: int = 30) -> Optional[str]:
        #"""
        #Liest die Chip-ID vom RFID-Reader
        #
        #Args:
        #    timeout: Timeout in Sekunden (nicht implementiert bei SimpleMFRC522)
        #    
        #Returns:
        #    Chip-ID als String oder None bei Fehler
        #"""
        if not self.reader:
            logger.error("RFID-Reader nicht verfügbar")
            return None
        
        try:
            logger.info("Warte auf RFID-Chip...")
            chip_id, text = self.reader.read()
            
            # Chip-ID in String umwandeln
            chip_id_str = str(chip_id).strip()
            logger.info(f"Chip gelesen: {chip_id_str}")
            
            return chip_id_str
            
        except Exception as e:
            logger.error(f"Fehler beim Lesen des Chips: {str(e)}")
            return None
    
    def read_chip_id_no_block(self) -> Optional[str]:
        #"""
        #Versucht einen Chip zu lesen ohne zu blockieren
        #Prüft nur einmal, ob ein Chip vorhanden ist
       # 
       # Returns:
       #     Chip-ID als String oder None wenn kein Chip vorhanden
       # """
        if not self.reader:
            return None
        
        try:
            # Versuche Chip zu lesen
            chip_id, text = self.reader.read_no_block()
            
            if chip_id:
                chip_id_str = str(chip_id).strip()
                logger.info(f"Chip gelesen (non-blocking): {chip_id_str}")
                return chip_id_str
            
            return None
            
        except AttributeError:
            # SimpleMFRC522 hat möglicherweise kein read_no_block
            # Fallback auf normales read mit kurzer Wartezeit
            logger.warning("read_no_block nicht verfügbar, verwende read()")
            return self.read_chip_id()
        except Exception as e:
            logger.error(f"Fehler beim Non-Blocking-Lesen: {str(e)}")
            return None
    
    def cleanup(self):
        #"""Räumt GPIO-Pins auf"""
        if RFID_AVAILABLE:
            try:
                GPIO.cleanup()
                logger.info("GPIO-Cleanup durchgeführt")
            except Exception as e:
                logger.error(f"Fehler beim GPIO-Cleanup: {str(e)}")
    
    def __del__(self):
        #"""Destruktor - räumt automatisch auf"""
        self.cleanup()


class DevelopmentRFIDReader(RFIDReader):
    #"""
    #Mock-RFID-Reader für Entwicklung ohne Hardware
    #Simuliert Chip-Scans über Tastatureingabe
    #"""
    
    def __init__(self):
        logger.info("Development RFID-Reader initialisiert")
        self.reader = "mock"
    
    def read_chip_id(self, timeout: int = 30) -> Optional[str]:
        #"""
        #Simuliert Chip-Scan durch Tastatureingabe
        #"""
        print("\n" + "="*50)
        print("ENTWICKLUNGSMODUS: Chip-ID eingeben")
        print("Beispiel: 123456789")
        print("="*50)
        
        try:
            chip_id = input("Chip-ID: ").strip()
            if chip_id:
                logger.info(f"Mock-Chip gelesen: {chip_id}")
                return chip_id
            return None
        except KeyboardInterrupt:
            return None
    
    def read_chip_id_no_block(self) -> Optional[str]:
        #"""Im Development-Modus nicht sinnvoll, gibt None zurück"""
        return None
    
    def cleanup(self):
        #"""Kein Cleanup nötig im Development-Modus"""
        pass


def get_rfid_reader() -> RFIDReader:
    #"""
    #Factory-Funktion für RFID-Reader
    #Gibt je nach Verfügbarkeit den echten oder Mock-Reader zurück
    #"""
    if RFID_AVAILABLE:
        return RFIDReader()
    else:
        return DevelopmentRFIDReader()
