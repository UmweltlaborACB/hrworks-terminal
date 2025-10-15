# HRworks Zeiterfassungsterminal

Django-basiertes Zeiterfassungsterminal für Raspberry Pi mit RFID-Reader und HRworks API-Integration.

Das aktuelle Projekt läuft zu Testzwecken noch mit einem USB Reader

Aktuell ist das Stempeln von "Kommen", "Gehen" und "Dienstgang" eingeplant.

Im Moment wird der Chip per JavaScript direkt von der Website gelesen, der Leser muss also nicht am Server angeschlossen sein.
Der Leser sollte als HID Gerät funktionieren, damit die ID ausgelesen werden kann.(Ändert sich eventuell noch, je nach Hardwareaufbau) 


Um nicht unnötig API Calls machen zu müssen läuft die Zuordnung Transponder -> Mitarbeiter(Über einen Hinweis ob ich /persons direkt nach einem CustomField durchsuchen kann würde ich mich freuen) 
