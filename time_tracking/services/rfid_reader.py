import requests
import logging
from django.conf import settings
import serial
import threading
from typing import Optional, Callable

logger = logging.getLogger(__name__)

#
#Aktuell nicht erforderlich, da über JavaScript ausgelesen wird.
#
class RFIDReader:
    """UART-basierter RFID-Reader (Binärformat)"""

    def __init__(self, port='/dev/serial0', baudrate=9600, callback: Optional[Callable] = None):
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.serial_connection = None
        self.running = False
        self.thread = None

    def start(self):
        """Startet den RFID-Reader"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            logger.info(f"✅ RFID-Reader gestartet auf {self.port}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des RFID-Readers: {e}")
            raise

    def stop(self):
        """Stoppt den RFID-Reader"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            logger.info("✅ RFID-Reader gestoppt")

    def _read_loop(self):
        """Liest kontinuierlich Daten vom Reader"""
        buffer = b''
        
        while self.running:
            try:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    buffer += data
                    
                    # Suche nach STX (0x02) und ETX (0x03)
                    if b'\x02' in buffer and b'\x03' in buffer:
                        start = buffer.find(b'\x02')
                        end = buffer.find(b'\x03', start)
                        
                        if end > start:
                            message = buffer[start:end+1]
                            buffer = buffer[end+1:]  # Rest für nächste Nachricht
                            
                            chip_id = self._parse_chip_id(message)
                            if chip_id and self.callback:
                                self.callback(chip_id)
                                
            except Exception as e:
                logger.error(f"❌ Fehler beim Lesen: {e}")

    def _parse_chip_id(self, data: bytes) -> Optional[str]:
        """
        Extrahiert Chip-ID aus Binärdaten
        
        Format: STX + Chip-ID (7 Bytes) + Checksum + ETX
        """
        try:
            if len(data) < 10:
                logger.warning(f"⚠️ Nachricht zu kurz: {data.hex()}")
                return None
            
            # STX entfernen (erstes Byte)
            # ETX und Checksum entfernen (letzte 2 Bytes)
            chip_bytes = data[1:-2]
            
            # In Hex umwandeln
            chip_hex = chip_bytes.hex()
            
            # In Dezimal umwandeln (für Datenbank)
            chip_decimal = str(int(chip_hex, 16))
            
            logger.info(f"📡 Chip gescannt - Hex: {chip_hex}, Dezimal: {chip_decimal}")
            
            return chip_decimal
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Parsen der Chip-ID: {e}")
            return None

    def read_once(self, timeout: int = 10) -> Optional[str]:
        """Wartet auf einen Chip-Scan (blocking)"""
        if not self.serial_connection or not self.serial_connection.is_open:
            self.start()
        
        buffer = b''
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    buffer += data
                    
                    if b'\x02' in buffer and b'\x03' in buffer:
                        start = buffer.find(b'\x02')
                        end = buffer.find(b'\x03', start)
                        
                        if end > start:
                            message = buffer[start:end+1]
                            return self._parse_chip_id(message)
                            
            except Exception as e:
                logger.error(f"❌ Fehler beim Lesen: {e}")
                return None
        
        return None