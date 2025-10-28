#!/usr/bin/env python3
import serial
import os
import sys
import django
from .models import ChipScan




def main():
    print("🚀 RFID Reader gestartet...")
    
    try:
        ser = serial.Serial('/dev/serial0', 9600, timeout=1)
        print("✅ Serieller Port geöffnet")
        
        while True:
            if ser.in_waiting > 0:
                chip_data = ser.readline().decode('utf-8').strip()
                if chip_data:
                    print(f"📡 Chip gescannt: {chip_data}")
                    
                    # In Datenbank schreiben
                    ChipScan.objects.create(chip_id=chip_data)
                    print(f"💾 In DB gespeichert")
                    
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
