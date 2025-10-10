#"""
#RFID Reader Module für USB-basierte Reader
#Unterstützt Reader, die als Keyboard-Eingabegerät arbeiten
#"""

import logging
from typing import Optional
import sys
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class RFIDReader(ABC):
    #"""
    #Abstrakte Basisklasse für RFID-Reader
    #"""
    
    @abstractmethod
    def read_chip_id(self, timeout: int = 30) -> Optional[str]:
        """
        Liest eine Chip-ID mit Timeout
        """
        pass
    
    def read_chip_id_no_block(self) -> Optional[str]:
        """
        Versucht eine Chip-ID zu lesen ohne zu blockieren
        """
        return self.read_chip_id(timeout=1)


class USBKeyboardRFIDReader(RFIDReader):
    #"""
    #RFID-Reader für USB-Geräte, die als Tastatur arbeiten
    #Funktioniert mit neuftech und ähnlichen Readern
    #"""
    
    def __init__(self):
        logger.info("USB Keyboard RFID-Reader initialisiert (neuftech)")
        self.reader = "usb_keyboard"
    
    def read_chip_id(self, timeout: int = 30) -> Optional[str]:
        #"""
        #Liest Chip-ID von USB-Reader (Tastatur-Emulation)
        #Der Reader sendet die ID gefolgt von Enter
        #
        #Args:
        #    timeout: Maximale Wartezeit in Sekunden
        #    
        #Returns:
        #    Chip-ID als String oder None bei Timeout
        #"""
        try:
            logger.info(f"Warte auf Chip-Scan (Timeout: {timeout}s)...")
            
            # In einer Web-Umgebung können wir nicht direkt von stdin lesen
            # Diese Methode ist nur für Testzwecke/CLI
            # In der Web-App wird die Eingabe über JavaScript erfasst
            
            # Für CLI-Tests:
            if sys.stdin.isatty():
                import select
                
                # Prüfe ob Eingabe verfügbar ist (Unix/Linux)
                ready, _, _ = select.select([sys.stdin], [], [], timeout)
                
                if ready:
                    chip_id = sys.stdin.readline().strip()
                    if chip_id:
                        logger.info(f"Chip-ID gelesen: {chip_id}")
                        return chip_id
                else:
                    logger.warning("Timeout beim Warten auf Chip")
                    return None
            
            # In Web-Umgebung: Warnung ausgeben
            logger.warning("USB-Reader im Web-Modus - Eingabe über Browser erforderlich")
            return None
            
        except Exception as e:
            logger.error(f"Fehler beim Lesen der Chip-ID: {e}")
            return None


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
                logger.info(f"Mock Chip-ID eingegeben: {chip_id}")
                return chip_id
            
            return None
            
        except (KeyboardInterrupt, EOFError):
            logger.info("Eingabe abgebrochen")
            return None


def get_reader() -> RFIDReader:
    #"""
    #Factory-Funktion: Gibt den passenden RFID-Reader zurück
    #"""
    from django.conf import settings
    
    reader_type = getattr(settings, 'RFID_READER_TYPE', 'development')
    
    if reader_type == 'usb_keyboard':
        return USBKeyboardRFIDReader()
    elif reader_type == 'development':
        return DevelopmentRFIDReader()
    else:
        raise ValueError(f"Unbekannter Reader-Typ: {reader_type}")
