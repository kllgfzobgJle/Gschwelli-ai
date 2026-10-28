# Original User Request

## Initial Request — 2026-10-28T21:31:44Z

Transformiere das bestehende Web-Cockpit in eine universelle, domain-agnostische Agent-Workstation (Operating Canvas) für autonome Agenten ohne Bindung an spezifische Domänen oder vordefinierte Spezial-Szenarien (keine hardcodierten CAD- oder 3D-Druck-Elemente).

Working directory: c:\Users\andym\gschwelli-ai
Integrity mode: development

## Requirements

### R1. Universelles Workspace- & Projekt-Datenmodell (Vollständiges CRUD)
- Dynamischer Workspace-Manager: Ersetze statische Dropdowns durch eine vollwertige Workspace-Verwaltung mit einem `[+ Neuer Workspace]`-Modal zur Definition von Name, Beschreibung/System-Prompt (Mission des Agenten für diesen Kontext) und lokalem Arbeitsverzeichnis. Ermögliche das Umschalten zwischen Projekten ohne Seiten-Reload sowie die Persistierung des Workspace-States (z. B. via `localStorage` oder Backend-JSON/SQLite).
- Reaktives Aufgaben- & Pipeline-System: To-Dos als universelle State-Objekte (`{ id, title, status: ['backlog', 'in_progress', 'agent_delegated', 'blocked', 'done'], priority: ['P1', 'P2', 'P3'], meta }`) mit Statuswechsel per Klick oder Drag-and-Drop, schneller Inline-Erstellung (`Enter`), `[An Agent delegieren]`-Toggle (Blitz/Bot-Icon) für die autonome Ausführungs-Queue und reaktiv mitlaufenden Fortschrittsmetriken (z. B. `3/7 erledigt`, visuelle Progress-Bar).
- Universeller Knowledge & Artifact Browser: Dynamischer Dateibaum basierend auf dem gewählten Workspace-Pfad, Filterung nach Dateitypen (Code, Dokumente, Tabellen, Medien, Configs) und Schnellvorschau per Mausklick in der zentralen Arbeitsbühne.

### R2. Polymorphe Hauptbühne & Drawer-Inspektoren
- Umschaltbarer Viewport-Container (per Tab oder Shortcut) mit vier universellen Viewport-Typen:
  1. Screen & Vision Stream (Set-of-Marks Perception): Universeller Desktop-/Fenster-Viewer für beliebige Zielanwendungen mit Set-of-Marks (SOM) Bounding-Boxes (`[01]`, `[02]`, ...) zur Visualisierung erkannter UI-Elemente (`win32_uia` / Vision) und Toolbar mit Zoom, Pan, Element-Inspektor-Fokus und Koordinaten-Anzeige.
  2. Artifact & Document Studio: Universeller Editor/Viewer mit automatischer MIME-Typ-Erkennung (Markdown/Text mit 2-Spalten-Split aus Raw Editor und formatierter Vorschau, Code/Configs im Monospace-Editor mit Syntax-Highlighting, Tabellen/CSV in dichter Data-Grid-Ansicht).
  3. Task & Reasoning Graph (Blackboard Visualizer): Übersicht des Ausführungspfads bei Multi-Step-Tasks (Graph-/Node-Darstellung Goal → Sub-Tasks → Gates → Artifacts) sowie Live-Variablen und Memory-State des Agenten.
  4. Shell & Execution Sandbox: Multi-Tab Monospace-Terminal für direkte Shell-Ausführungen mit Zeitstempeln, Exit-Codes und Stdout/Stderr-Farbkodierung.
- Split-Screen-Layout für zwei parallele Ansichten sowie beibehaltene Quick-Drawers / Inspektoren für Tools, Memory-Facts (`/api/memory`), Tier-0-Cache (`/api/cache`) und Undo-Stack (`/api/undo`).

### R3. Durchgängige Interaktivität & Safety Controls
- Human-in-the-Loop Safety Interceptor: Einheitliches Bestätigungs-Banner für potenziell riskante Aktionen (Dateisystem-Schreibvorgänge, Shell-Befehle, externe Klicks) mit Anzeige von Aktionstyp, Zielpfad/Befehl, Risiko-Badge (`Info`, `Moderate`, `Critical`), `[Approve (Space)]`, `[Edit]`, `[Abort (Esc)]` und `[PANIC KILL & UNDO]` (stoppt alle Agent-Prozesse und triggert den Rollback-Stack via `undo.py`).
- Universal Omnibar (Unterer Input Dock): Reagiert auf Tastatureingaben (`Enter` zum Senden), Slash-Commands (`/workspace`, `/task`, `/run`, `/inspect`, `/undo`, `/clear`) mit Autovervollständigungs-Menü, File-Dropzone für beliebige Dateianhänge, klickbare Audio-Viseme-Pill mit optischem Feedback (Listening vs. Muted) und Model-Selector für lokale Engines und Cloud-Modelle.
- Tastatur-Scope: Globale Tastaturkürzel (`Space`, `Esc`) dürfen nicht auslösen, während der Fokus in einem Eingabefeld (`input`, `textarea`, `contenteditable`) liegt.

### R4. Backend-, WebSocket- & Offline-Integration
- Nahtlose Backend- & WebSocket-Integration (`server/api.py`): Bestehende Endpunkte (`/`, `/api/state`, `/api/route`, `/api/confirm`, `/api/undo`, `/api/tool`, `/api/memory`, `/api/cache`, `/api/voice`, `/api/repl`, `/api/som`, `/ws` WebSocket) weiter unterstützen und mit generischen Fallback-/Default-Daten ausstatten, sodass das Dashboard sofort beim Start via `python main.py --dashboard` unter `http://127.0.0.1:8765` interaktiv funktioniert.
- Zero-Dependency Single-Page-App: Keine externen CDN- oder Remote-Netzwerk-Abhängigkeiten im Frontend; vollständige Offline-Lauffähigkeit.

### R5. UI-Politur, Robustheits-Guardrails & Design-Konsistenz
- Striktes Einhalten der Farb-Tokens der DESIGN.md: `#0A0D12` (Canvas), `#121824` (Panels/Cards), `1px solid #1E293B` (Borders), Akzente in Cyan (`#06B6D4`), Amber (`#F59E0B`) und Crimson (`#EF4444`) mit neutralen Glyphen ohne CAD-/3D-Druck-Spezifika.
- Robuste Ausführung: Null Console-Errors und null unbehandelte JS-Exceptions während der gesamten Interaktion.
- Strikte CSS-Isolation beim View-/Tab-Wechsel, XSS-sichere Input-Sanitisierung bei dynamischen Eingaben (Tasks, Workspaces, Terminal, Chat) und überlappungsfreie SOM-Tag-Positionierung ohne Pointer-Occlusion über verschiedene Viewport-Auflösungen (`1024x768`, `1440x900`, `1920x1080`).
- Vollständige funktionale Bindung aller JavaScript Event-Listener ohne unverbundene Dummy-Elemente im DOM.

## Verification Resources
- Web cockpit files: `ui/dashboard/index.html` served by FastAPI backend `server/api.py`.
- Automated test suites: `tests/test_api.py` and `tests/test_browser_dom.py` (runnable via `uv run --with pytest,playwright pytest ...`).

## Acceptance Criteria

### Workspace & Task Management
- [ ] Der Workspace-Manager erlaubt das Erstellen neuer Workspaces via Modal (Name, Prompt/Mission, lokales Verzeichnis) und das Umschalten zwischen bestehenden Workspaces ohne Neuladen der Seite.
- [ ] Workspaces und Aufgaben werden nach Browser-Neuladen persistent wiederhergestellt.
- [ ] To-Do-Elemente können per Inline-Eingabe (`Enter`) erstellt, im Status (`backlog`, `in_progress`, `agent_delegated`, `blocked`, `done`) umgeschaltet und mit dem Agent-Delegation-Toggle versehen werden.
- [ ] Fortschrittsmetriken (z. B. X/Y erledigt und visuelle Progress-Bar) aktualisieren sich reaktiv bei Statusänderungen.
- [ ] Der Dateibaum zeigt das gewählte Workspace-Verzeichnis an, unterstützt Dateityp-Filterung und öffnet Dateien per Klick in der zentralen Bühne.

### Polymorphe Hauptbühne & Quick-Drawers
- [ ] Alle vier Viewports (Screen & Vision Stream, Artifact & Document Studio, Task & Reasoning Graph, Shell Sandbox) lassen sich per Tab oder Shortcut umschalten.
- [ ] View 1 visualisiert Set-of-Marks Bounding-Boxes/Labels (überlappungsfrei positioniert, ohne Klick-Events auf UI-Elemente zu blockieren) und bietet funktionale Toolbar-Controls (Zoom, Pan, Koordinaten).
- [ ] View 2 rendert Markdown als 2-Spalten-Split (Raw / Preview), Code mit Syntax-Highlighting und Tabellen/CSV in einer Data-Grid-Ansicht.
- [ ] View 3 visualisiert Knoten/Pfade (Goal → Sub-Tasks → Gates → Artifacts) und Agent-Variablen.
- [ ] View 4 stellt ein Multi-Tab-Terminal mit Zeitstempeln, Exit-Codes und Stdout/Stderr-Farbkodierung bereit.
- [ ] Die Split-Screen-Funktion ermöglicht das parallele Anzeigen von zwei Views nebeneinander.
- [ ] Quick-Drawers / Inspektoren für Tools, Memory-Facts (`/api/memory`), Cache (`/api/cache`) und Undo-Stack (`/api/undo`) lassen sich öffnen und zeigen konsistente Daten an.

### Safety Interceptor & Omnibar
- [ ] Der Safety Interceptor fängt riskante Aktionen ab, zeigt Risiko-Level an und reagiert auf Tastenkürzel (`Space` für Approve, `Esc` für Abort, Editier-Funktion sowie Panic Kill).
- [ ] Tastaturkürzel (`Space`, `Esc`) triggern nicht, während der Fokus in einem Eingabefeld (`input`, `textarea`, `contenteditable`) liegt.
- [ ] Die Omnibar verarbeitet Eingaben bei `Enter`, blendet Autovervollständigung für Slash-Commands (`/workspace`, `/task`, `/run`, `/inspect`, `/undo`, `/clear`) ein, reagiert auf Klicks auf die Audio-Pill und erlaubt Model-Auswahl.
- [ ] Alle Benutzereingaben (Workspaces, Tasks, Chat, Terminal) werden vor dem Rendern im DOM XSS-sicher bereinigt.

### Backend-Integration, Zero-Dependency & Robustheit
- [ ] Alle bestehenden FastAPI-Endpunkte (`/`, `/api/state`, `/api/route`, `/api/confirm`, `/api/undo`, `/api/tool`, `/api/memory`, `/api/cache`, `/api/voice`, `/api/repl`, `/api/som`, `/ws`) antworten korrekt mit generischen Default-Daten und das Dashboard startet sofort unter `http://127.0.0.1:8765` (`python main.py --dashboard`).
- [ ] Das Frontend lädt keine externen CDN-Ressourcen (Fonts, Skripte, Stylesheets) und funktioniert vollständig offline.
- [ ] Beim Laden, Bedienen und Wechseln aller Ansichten treten null ungefangene JavaScript-Exceptions und null Console-Errors auf.
- [ ] Das Layout bleibt bei den Auflösungen `1024x768`, `1440x900` und `1920x1080` stabil und visuell konsistent gemäß den Farb-Tokens (`#0A0D12`, `#121824`, `#1E293B`, `#06B6D4`, `#F59E0B`, `#EF4444`).
- [ ] Alle interaktiven Buttons besitzen aktive Event-Listener ohne unverbundene Dummy-Elemente im DOM.
- [ ] Die bestehenden Test-Suites werden erweitert und `uv run --with pytest,playwright pytest tests/test_browser_dom.py tests/test_api.py` läuft vollständig fehlerfrei durch.
