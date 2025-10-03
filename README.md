# Flask HTMX Blog

Eine kleine Blog-Anwendung mit Flask als Backend und HTMX im Frontend. Du kannst neue Beiträge erstellen, Kommentare hinzufügen und bestehende Kommentare wieder löschen.

## Voraussetzungen

- Python 3.11

## Installation & Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install flask
flask --app app run
```

Die Anwendung legt beim ersten Start automatisch eine SQLite-Datenbank `blog.db` im Projektverzeichnis an.
