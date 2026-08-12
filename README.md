# Fondsmonitor A40US6 – V3 ohne API-Key

Diese Version benötigt **keinen Twelve-Data-API-Key**.

## Prinzip
Die Webseite bleibt eine statische GitHub-Pages-PWA. Ein GitHub-Actions-Workflow
ruft werktags öffentliche NAV-Daten ab und schreibt sie in `data/nav.json`.
Die App liest nur diese Datei aus demselben Repository.

Damit gibt es:
- keinen API-Key auf iPhone/iPad
- keinen dauerhaft laufenden Backend-Server
- dieselben Daten auf allen Endgeräten
- NAV, Nennwert für 390,2153 Stück
- Chart für 1 Tag / 1 Woche / 1 Monat
- Tief, Hoch und Zeitraum-Performance

## Wichtig nach dem Upload
Alle Dateien und Ordner dieses Pakets müssen im Repository landen, insbesondere:

- `.github/workflows/update-nav.yml`
- `scripts/update_nav.py`
- `data/nav.json`
- `index.html`
- `sw.js`

Anschließend in GitHub:
**Actions → NAV aktualisieren → Run workflow**

Beim ersten Lauf versucht der Job, die Historie der letzten ca. 50 Tage
einzulesen. Danach aktualisiert er automatisch werktags zweimal.

## GitHub-Pages
Die Pages-Einstellung bleibt:
- Source: Deploy from a branch
- Branch: main
- Folder: /(root)

## Hinweise
Öffentliche Webseiten können ihre HTML-Struktur ändern. Der Scraper ist deshalb
mit mehreren Fallbacks gebaut und behält vorhandene historische Werte bei.
Wenn eine Quelle dauerhaft ihr Layout ändert, kann `scripts/update_nav.py`
angepasst werden.
