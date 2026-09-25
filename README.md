# BNO-EZ Adapter

Adapterplatine für den **BNO085**, um den Sensor über I²C an ältere Fischertechnik-Controllern anzubinden.

## Funktionen

- BNO085 über I²C auslesen
- USB-C für Test- und Programmierzwecke
- RGB-LED zur Statusanzeige
- Kompasswerte auslesen und extern nullen

## Pinbelegung

| Anschluss | Funktion   |
| --------- | ---------- |
| I2 / I1   | I²C        |
| +3.3V     | Versorgung |
| SDA       | I²C Daten  |
| SCL       | I²C Takt   |
| GND       | Masse      |

### I²C-Einstellungen

```text
Geräteadresse: 0x22
Richtungsregister: 0x00
Kompass-Nullpunkt: 0x10
Geschwindigkeit: 400 kHz
```

## Wichtige Hinweise

- Der Adapter darf **nur mit 3,3 V** betrieben werden.
- Die Eingänge sind **nicht 5-V-tolerant**.
- Beim Aufstecken des BNO085 auf die **richtige Orientierung** achten.
- USB-C ist ausschließlich für **Test- und Programmierzwecke** vorgesehen.
- Eine **grün leuchtende RGB-LED** signalisiert einen betriebsbereiten Sensor.

## Testprogramm

Das Testprogramm ermöglicht:

- Sensorwerte auszulesen
- Fehler anzuzeigen
- den Kompass extern zu nullen
- die Kompassrichtung zu visualisieren

### Verbindung

1. COM-Port auswählen.
2. Verbindung herstellen.
3. Sensorwerte prüfen.
4. Bei Bedarf den Kompass nullen.
