from django.core.management.base import BaseCommand
from django.core.cache import cache
import serial
import time

class Command(BaseCommand):
    help = 'Startet den RFID-Reader im Hintergrund'

    def handle(self, *args, **options):
        PORT = '/dev/serial0'
        BAUDRATE = 9600

        ser = serial.Serial(
            port=PORT,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )

        self.stdout.write(self.style.SUCCESS(f'✅ RFID-Reader gestartet auf {PORT}'))

        buffer = b''
        last_chip_id = None

        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                buffer += data

                if b'\x02' in buffer and b'\x03' in buffer:
                    start = buffer.find(b'\x02')
                    end = buffer.find(b'\x03', start)

                    if end != -1:
                        message = buffer[start:end+1]
                        buffer = buffer[end+1:]

                        hex_data = message.hex()
                        chip_id = self.convert_to_usb_format(hex_data)

                        if chip_id and chip_id != last_chip_id:
                            self.stdout.write(f'📡 Chip gescannt: {chip_id}')

                            # ✅ HIER: Beide Cache-Keys setzen
                            cache.set('last_chip_id', chip_id, timeout=10)
                            cache.set('chip_scanned', True, timeout=10)

                            last_chip_id = chip_id
                            time.sleep(2)  # Debounce

    def convert_to_usb_format(self, hex_data):
        """Konvertiert Binär-Format zu USB-Format"""
        if len(hex_data) >= 18 and hex_data[:2] == '02' and hex_data[-2:] == '03':
            chip_data = hex_data[4:-4]
            relevant_part = chip_data[-8:]
            usb_id = int(relevant_part, 16)
            return str(usb_id).zfill(10)
        return None
