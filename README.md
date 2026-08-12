# Fondsmonitor – WKN A40US6 / ISIN LU2936783674

Eine iPhone-optimierte Progressive Web App (PWA) für den
**Santander Target Maturity Euro IV AD EUR Income**.

## Funktionen
- letzter NAV in EUR
- Veränderung zum vorherigen NAV
- Chart für **1 Tag / 1 Woche / 1 Monat**
- Tief/Hoch und prozentuale Veränderung des gewählten Zeitraums
- installierbar auf dem iPhone-Home-Bildschirm
- API-Key wird nur lokal im Browser (`localStorage`) gespeichert
- kein Tracking, keine Benutzerkonten

## Datenquelle
Die App ist für **Twelve Data** vorbereitet. Das ist sinnvoller als HTML-Scraping,
weil die Oberfläche einer Finanz-Webseite jederzeit geändert werden kann.

1. Bei Twelve Data einen API-Key anlegen.
2. `index.html` öffnen bzw. die Seite hosten.
3. Oben rechts auf **⚙︎** tippen.
4. API-Key eintragen.
5. Als Symbol zunächst `LU2936783674` verwenden.
6. Falls der Anbieter die ISIN nicht direkt auflöst, im Twelve-Data-Dashboard nach
   dem Fonds suchen und das dort angezeigte Symbol einsetzen.

Die App enthält als klar gekennzeichneten Startwert die zuletzt öffentlich
verifizierten Daten, damit die Oberfläche auch ohne API-Key sichtbar ist.

## Am einfachsten auf dem iPhone installieren
Die Dateien müssen über HTTPS erreichbar sein, z. B. über GitHub Pages,
Cloudflare Pages, Netlify oder einen eigenen Webserver.

Danach in Safari:
**Teilen → Zum Home-Bildschirm → Hinzufügen**

Dann startet die Webseite wie eine normale App im Vollbild.

## Lokal testen
In diesem Ordner:
```bash
python3 -m http.server 8080
```
Dann `http://localhost:8080` öffnen.

## Dateien
- `index.html` – komplette Oberfläche und Logik
- `manifest.webmanifest` – PWA-Metadaten
- `sw.js` – Offline-Cache
- `icon.svg` – App-Icon

Hinweis: Dies ist ein persönliches Anzeige-Tool und keine Anlageberatung.
