# SBB-Zugaenglichkeit-Haltestellen-Public
Server Client Projekt im Rahmen der Bachelor Thesis "SBB interaktive Visualisierung der Zugänglichkeit von Haltestellen" des Institutes Geomatik an der FHNW Muttenz

**Frontend:** Angular, MapLibre und SBB Angular

**Backend:** FastAPI

## Requirements
- Git
- Integrierte Entwicklungsumgebung (z.B. Visual Studio Code)
- Anaconda Distribution oder Miniconda
- Node.js und npm (https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)

## Git Projekt mit Visual Studio Code lokal klonen
Öffne ein neues Visual Studio Code Fenster und wähle unter Start Clone Git Repository. Alternativ öffne die Command Palette in VS Code CTRL+Shift+P (View / Command Palette) und wähle Git: clone. Füge die Git web URL https://github.com/HauserSara/SBB-Zugaenglichkeit-Haltestellen ein und bestätige die Eingabe mit Enter. Wähle einen Ordner in welchen das Repository geklont werden soll.

## Frontend installieren
Öffne ein Terminal (Command Prompt in VS Code) und wechsle in den *client* Ordner in diesem Projekt

``` shell
cd client
npm install
```

Starten die Applikation mit dem Befehl:
``` shell
ng serve
```

## Backend installieren
Öffne ein Terminal und wechsle in den *server* Ordner.
1. Virtuelle Umgebung für Python erstellen

2. Folgende Bibliotheken installieren:
    - requests [2.31.0]
    - pyproj [3.6.1]
    - fastapi [0.110.2]
    - pydantic [2.7.1]
    - pandas [2.2.2]
    - folium [0.16.0]
    - folium [0.16.0]

6. Backend ausführen, virtuelle Umgebung starten und server *uvicorn* starten. Öffne http://localhost:8000/api/docs im Browser und verifiziere, ob das Backend läuft.
``` shell
# navigiere zum server Ordner im Verzeichnis
cd server
# aktiviere die erstellte Umgebung
conda activate [your_enviroment]
# start server auf localhost aus dem Ordner "server"
uvicorn main:app --reload
# Öffne die angegebene URL im Browser und verifiziere, ob das Backend läuft.
```

## API Dokumentation
Fast API kommt mit vorinstallierter Swagger UI. Wenn der Fast API Backend Server läuft, ist die Dokumentation der API über Swagger UI auf http://localhost:8000/api/docs verfügbar.
