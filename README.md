# MINARAM CUP — Elite eSports Platform
## Full-Stack Website + Live Tournament Management Software Integration

The official digital competition platform for the **Minaram Cup** eFootball Championship at TKM College of Engineering. This system pairs a modern offline-first desktop management suite (Python & CustomTkinter) with a high-performance public live website (React, TypeScript, Vite, Tailwind CSS), a real-time event broadcaster (Server-Sent Events), and an automated image processing pipeline for tournament assets.

---

## 🌟 Architecture & Key Capabilities

```
                      +-----------------------------------+
                      |      MINARAM CUP TOURNAMENT       |
                      |   Authoritative Database (SQLite) |
                      |       data/minaram_cup.db         |
                      +-----------------+-----------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
+----------------------------------+          +----------------------------------+
|   DESKTOP MANAGEMENT SOFTWARE    |          |       FASTAPI BACKEND API        |
|      (CustomTkinter Desktop)     |          |       (Uvicorn on Port 8000)     |
| • Full tournament administrator  |          | • Public Read-Only Endpoints     |
| • Registrations & WhatsApp parser|          | • Real-time SSE Stream (/events) |
| • Berger round-robin fixtures    |          | • JWT Authenticated Admin API    |
| • Live match scoring & audits    |          | • Serves production SPA frontend |
| • Master Excel & CSV exports     |          +-----------------+----------------+
| • Broadcasts events via thread   |                            |
+----------------+-----------------+                            | Server-Sent Events
                 |                                              | (Real-time sync)
                 +-----------------> [ Broadcaster ] <----------+
                                             |
                                             v
                              +------------------------------+
                              |      PUBLIC LIVE WEBSITE     |
                              |  (React + Tailwind + Vite)   |
                              | • Strictly read-only public  |
                              | • Live scoreboard ticker     |
                              | • Group standings tables     |
                              | • Knockout playoff brackets  |
                              | • Zero phone numbers leaked  |
                              +------------------------------+
```

### 1. Distinctive Editorial Web Design
- **Visual Identity:** Deep pitch dark theme (`#080808`), European football editorial aesthetic, condensed typography (`Bebas Neue`), tabular monospace numerals for standings and scores, and dynamic accent red badges (`#B3121B`).
- **Original Asset Pipeline:** Non-destructive enhancement pipeline (`tools/asset_pipeline.py`) that extracted clean transparent logos and optimized web-ready backgrounds from `Logo/` and `Bgs/`. Original assets remain 100% untouched.
- **Sponsor & Identity:** Features title sponsor **AKHADHA** with clean anti-aliased transparency, and organizer credit to **minarathintememe**.

### 2. Public Read-Only Security & Privacy
- **Strictly Read-Only for Visitors:** Public visitors can browse fixtures, live scores, group standings, playoff brackets, and team profiles without requiring an account. No create, edit, or delete buttons are visible in the public interface.
- **Privacy Enforcement:** All public endpoints (`/api/public/...`) strictly strip participant phone numbers, raw WhatsApp messages, and internal notes.
- **JWT Admin Security:** Administrative operations via the web interface (`/admin`) require secure HMAC-SHA256 Bearer tokens.

### 3. Automatic Registration-to-Team Integration
- Whenever a registration is parsed from WhatsApp, added manually, or imported via Excel/CSV, the system automatically registers the squad in the `teams` table and links them together.
- A startup reconciler (`reconcile_registrations_to_teams`) ensures no registered participant is left without a team entry.

### 4. Real-Time Live Desktop-to-Website Synchronization
- When an administrator records or updates a match score in the desktop manager, `broadcaster.broadcast_from_thread()` triggers an instant Server-Sent Event (`/api/events`).
- Connected browser tabs receive the score update and update standings without needing manual page refreshes.

---

## 🚀 How to Launch the Application

### Option 1: The Interactive Launcher (`run.bat`)
Double-click `run.bat` in the project root folder. It provides a simple menu:

```
 [1] Launch Full Platform (Backend API + Live Website + Desktop App)
 [2] Launch Desktop Tournament Manager App
 [3] Launch Web Server & Public Website (http://localhost:8000)
 [4] Run Asset Enhancement Pipeline (Process logos and wallpapers)
 [5] Run Full Automated Test Suite (pytest)
 [6] Exit
```

Selecting `[1]` starts the FastAPI web server on `http://localhost:8000/` and launches the desktop application simultaneously.

### Option 2: Dedicated Launch Scripts
- **Start Web Server & Website:** Double-click `start_web.bat` or run:
  ```powershell
  py -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
  ```
  Visit the website at: **`http://localhost:8000/`**
  Interactive API docs: **`http://localhost:8000/docs`**

- **Start Desktop Manager:** Double-click `run_desktop.bat` or run:
  ```powershell
  py main.py
  ```

- **Frontend Development Mode (Vite Dev Server with Hot Reloading):**
  ```powershell
  cd frontend
  npm run dev
  ```
  Dev website runs at: `http://localhost:5173/` (proxies `/api` to port 8000).

---

## 📁 Project Structure

```
Minaram Cup/
│
├── main.py                     # Desktop application entry point
├── registration_logger.py      # Preserved legacy logger script
├── run.bat                     # Master interactive Windows launcher
├── start_web.bat               # Web server launcher (FastAPI + SPA)
├── run_desktop.bat             # Desktop manager launcher
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation
│
├── app/                        # Shared Core Tournament Logic
│   ├── database.py             # SQLite database layer (WAL mode)
│   ├── events.py               # Thread-safe Server-Sent Events broadcaster
│   ├── registration_parser.py  # WhatsApp multi-format message parser
│   ├── registration_service.py # Registration CRUD & auto-team creation
│   ├── team_manager.py         # Team admin, duplicate merge, match history
│   ├── tournament_manager.py   # Group allocation, seeded & random draws
│   ├── fixture_generator.py    # Berger round-robin schedule generator
│   ├── standings.py            # Group points table & tie-breaker calculations
│   ├── results_manager.py      # Score recording, audit logs & event broadcast
│   ├── knockout_manager.py     # Playoff tree advancement (QF ➔ SF ➔ Final)
│   ├── backup_service.py       # Atomic database backups & sample generator
│   ├── export_service.py       # Master Excel workbook & CSV exporter
│   └── ui/                     # CustomTkinter Desktop User Interface
│
├── backend/                    # FastAPI Web API Layer
│   ├── main.py                 # FastAPI application & SPA static file serving
│   ├── auth.py                 # JWT authentication & security dependencies
│   └── routers/
│       ├── public.py           # Sanitized read-only public endpoints
│       └── admin.py            # Secured admin endpoints with token validation
│
├── frontend/                   # React + Vite + Tailwind CSS Public Website
│   ├── src/
│   │   ├── api.ts              # API client for public & admin endpoints
│   │   ├── types.ts            # TypeScript data models
│   │   ├── hooks/
│   │   │   └── useLiveUpdates.ts # SSE real-time hook with auto-reconnect
│   │   ├── components/         # Navbar, Footer, Ticker, MatchCard, Standings, Bracket
│   │   └── pages/              # Home, Fixtures, Results, Standings, Teams, Bracket, Rules, Admin
│   ├── public/assets/          # Web-optimized logos and wallpapers
│   └── dist/                   # Production-built web application
│
├── tools/                      # Engineering Utilities
│   ├── asset_pipeline.py       # Non-destructive image enhancement & transparency pipeline
│   └── asset_manifest.json     # Manifest catalog of processed assets
│
├── tests/                      # Automated Test Suite
│   ├── test_asset_pipeline.py  # Image processing & preservation tests
│   ├── test_backend_api.py     # Privacy enforcement, JWT auth & API tests
│   ├── test_parser.py          # WhatsApp message parser tests
│   ├── test_services.py        # Core database, teams, standings tests
│   └── test_integration.py     # End-to-end tournament lifecycle tests
│
├── Bgs/                        # Original source background wallpapers (Untouched)
├── Logo/                       # Original source logos (Untouched)
└── data/                       # Authoritative SQLite database (minaram_cup.db)
```

---

## 🧪 Testing & Verification

Run the entire test suite across all modules with a single command:

```powershell
py -m pytest -v
```

Expected output:
```
============================= test session starts =============================
collected 26 items

tests/test_asset_pipeline.py::test_manifest_generated PASSED
tests/test_asset_pipeline.py::test_source_files_preserved PASSED
tests/test_asset_pipeline.py::test_logo_transparency PASSED
tests/test_asset_pipeline.py::test_responsive_variants_exist PASSED
tests/test_backend_api.py::test_public_tournament_summary PASSED
tests/test_backend_api.py::test_public_teams_privacy_enforcement PASSED
tests/test_backend_api.py::test_public_standings PASSED
tests/test_backend_api.py::test_public_bracket PASSED
tests/test_backend_api.py::test_admin_endpoints_require_authentication PASSED
tests/test_backend_api.py::test_admin_login_and_authenticated_operations PASSED
tests/test_backend_api.py::test_spa_frontend_serving PASSED
tests/test_backend_api.py::test_static_asset_serving PASSED
tests/test_integration.py::test_full_tournament_lifecycle PASSED
tests/test_parser.py::test_parse_standard_format PASSED
tests/test_parser.py::test_parse_backslash_format PASSED
tests/test_parser.py::test_parse_multiline_whatsapp PASSED
tests/test_parser.py::test_clean_phone_number PASSED
tests/test_parser.py::test_bulk_parse PASSED
tests/test_services.py::test_database_init PASSED
tests/test_services.py::test_registration_ingestion PASSED
tests/test_services.py::test_team_creation_and_merge PASSED
tests/test_services.py::test_group_draw_and_seeding PASSED
tests/test_services.py::test_fixture_generation_round_robin PASSED
tests/test_services.py::test_results_recording_and_audit PASSED
tests/test_services.py::test_standings_calculation_tie_breakers PASSED
tests/test_services.py::test_knockout_bracket_progression PASSED

======================== 26 passed in 3.16s ========================
```

---

## 🛡️ Privacy & Security Commitments

1. **Zero Data Leaks:** No phone numbers, participant private notes, or raw message metadata are ever exposed through `/api/public/...` endpoints or the live SSE event stream.
2. **Original Assets Protected:** The original background images in `Bgs/` and original logos in `Logo/` are strictly read-only. All enhanced, trimmed, transparent, or web-optimized versions are written to `frontend/public/assets/` and `frontend/dist/assets/`.
3. **Database Integrity:** Transactions use WAL mode, enforced foreign keys, and atomic point-in-time backups to ensure zero tournament data loss.
