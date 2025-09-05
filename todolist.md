# Project To‑Do

Legend: [x] done (YYYY‑MM‑DD) · [ ] pending · Priority: P0 (now) / P1 (next) / P2 (later)

## Timeline & Estimates

- Phase 2A — Data Foundation & Migrations: 8–14 h (1.0–1.8 days)
- Phase 2B — Report Upload Popup (Parse & Apply): 10–18 h (1.3–2.3 days)
- Phase 2C — Weekly Reports Editor (Cards) MVP: 12–24 h (1.5–3.0 days)
- Phase 2D — Analysis Core (Sync) + Results Listing: 16–28 h (2.0–3.5 days)
- Phase 2E — WebSocket Analysis, Export & Ask AI: 16–28 h (2.0–3.5 days)

- Report Analysis Prototype (scope: 2A + 2B + 2D minimal-sync): 34–60 h (4.3–7.5 days)
  - Projected completion window (given 20h/week):
    - Earliest: Week3 = 2025-09-01 to 2025-09-05
    - Latest: Week4 or Week5
  - Weekly pacing (20h/week):
    - Week ending 2025-08-29: 2A complete; 2B complete (min) or partial (max)
    - Week ending 2025-09-05: finish 2B (max) + 2D (min) → prototype viable (min)
    - Week ending 2025-09-12: finish 2D (max) → prototype viable (max)

## A) Original Status
- [x] Backend: FastAPI scaffold with CORS and /api/health (200 OK) — 2025-08-20
- [x] Backend: Conda environment (`environment.yml`) and pinned `requirements.txt` — 2025-08-20
- [x] Backend: PostgreSQL local setup assets (`setup-database.sql`, `setup-postgres.md`, `env.example`) — 2025-08-20
- [x] Database: PostgreSQL tables created with sample data, extensions enabled — 2025-08-20
- [x] Backend: FastAPI server running on port 8002 with health endpoint — 2025-08-20
- [x] Frontend: ESLint configuration fixed; `pnpm lint:fix` runs clean (warnings only) — 2025-08-20
- [x] Documentation: Top-level README rewritten with setup details — 2025-08-20
- [x] Deployment: Cross-platform scripts for one-click installation and service management — 2025-08-20
  - [x] `install.sh` / `install.bat` - Automated setup for macOS/Linux/Windows
  - [x] `start.sh` / `start.bat` - Service management (start/stop/status/restart)
  - [x] `test.sh` - Comprehensive health checks and validation
  - [x] `demo.sh` - Platform feature showcase and demonstration
  - [x] `scripts/README.md` - Detailed usage instructions and troubleshooting

Assumptions:
- PostgreSQL 15 is available locally with `pgcrypto` and `uuid-ossp` extensions.
- The database schema in the DB section is the single source of truth and overrides any draft feature spec.
- ReportAnalysis is the first priority and should be finished early
---

## B) Minimal-Change Implementation Plan (Priority & Steps)

### P0 Phase 1 — Frontend Service Layer (keep UI/UX unchanged) — 2025-08-22 ✅ COMPLETED
Goal: Decouple UI from data source and prepare a drop-in switch from mock → real API.
- [x] Create shared types in frontend — 2025-08-22
  - `frontend/lib/types/{project.ts, history.ts, analysis.ts}` (align strictly with schema)
- [x] Create API client and feature services — 2025-08-22
  - `frontend/lib/api/client.ts` (base URL from `NEXT_PUBLIC_API_URL`, JSON helpers, error handling)
  - `frontend/lib/api/{projects.ts, projectHistory.ts, analysis.ts}` (typed functions)
- [x] Retrofit Project Management to call service layer (still hitting a mock adapter initially) — 2025-08-22
  - Loading and error states (spinner + toast)
  - Acceptance: UI behaves the same; data flows only via service layer
- [x] Env wiring — 2025-08-22
  - Add `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8002/api`
- [x] Add comprehensive tests — 2025-08-22
  - Vitest + Testing Library setup
  - API client tests
  - ProjectManagement component tests (loading, filtering, selection, status)

Acceptance for Phase 1:
- ✅ App boots with no runtime errors; all project list interactions go through service functions (mocked).
- ✅ No visual regressions.
- ✅ All tests pass (9/9 tests passing)
- ✅ Service layer decoupled from UI components

---

### P0 Phase 2A — Data Foundation & Migrations — ✅ COMPLETED 2025-08-26
Goal: Establish minimal, correct data layer for reports and analysis.
- [x] Backend: Database Infrastructure — 2025-08-26
  - Database connection & session (`backend/app/database.py` using `DATABASE_URL`)
  - SQLAlchemy models: `projects` (minimal), `project_history`, `weekly_report_analysis`
  - Pydantic schemas for request/response
  - Alembic baseline + first migration reflecting current schema
- [x] Indexes & Constraints — 2025-08-26
  - `projects.project_code` UNIQUE
  - `weekly_report_analysis UNIQUE(project_code, cw_label, language)` + composite read index
  - Range/read indexes for `project_history` (project_code, cw_label)
  - CHECK constraint for `project_history.category` (enum: Development, EPC, Finance, Investment)
  - Optional: add `updated_at/updated_by` to `weekly_report_analysis` if updates are expected

Acceptance for Phase 2A:
- Alembic migrations apply cleanly; constraints and indexes verified
- App boots with DB connectivity; models usable in services

---

### P0 Phase 2B — Report Upload & Import (Upload → LLM Parse → Apply → DB)

- Goal: Support file upload → parsing preview → manual apply-to-cards → persistence to DB, with full traceability (`source_upload_id`).

#### 2B1 - Upload & Preview (✅ Completed 2025-08-26)
- [x] Backend: single-file upload `POST /api/reports/upload` (docx/pdf/txt/md; type whitelist, size limit, unified error schema; local temp storage+cleanup; DOCX parser for paragraphs+tables → rows)
- [x] Backend: bulk upload `POST /api/reports/upload/bulk` (docx-only; filename pattern `YYYY_CW##_{DEV|EPC|FINANCE|INVESTMENT}.docx` → year/cw/category mapping; per-file results/errors; TTL cleanup)
- [x] Frontend: upload popup (drag & drop, show parsed rows, apply-to-cards without persistence; unmatched items flagged)
- [x] Frontend: bulk folder picker (webkitdirectory filter+preview; per-file parsed rows/errors; apply-to-cards per file/category; service layer + tests)
- Acceptance:
  - [x] Files parsed into structured rows; apply-to-cards works; errors clear
  - [x] Bulk import: non-matching names/types flagged per file
  - [x] No DB writes until Save is clicked in cards editor

#### 2B2 - DB Schema & Linking (✅ Completed)
- [x] Database: add `report_uploads`; add `project_history.source_upload_id UUID REFERENCES report_uploads(id) ON DELETE SET NULL`; index `idx_project_history_source_upload_id`
- [x] Migration scripts: backward-compatible with rollback
- [x] Domain/DAO: `ReportUploads` repo (`create`/`get_by_sha256`/`mark_parsed`); insert `source_upload_id` when creating `ProjectHistory`

#### 2B3 - Importer Entrypoint (CLI/Backend)
- [x] Support single `.docx` upload (iterate until `uploads/2025_CW01_DEV.docx` passes)
- [x] Support folder recursive upload (iterate until `./uploads` passes)
- [x] Compute `sha256` for deduplication (reuse existing `report_uploads` entry)
- [ ] Final polish: CLI UX and logging details

#### 2B4 - LLM Parsing Pipeline (docx → project_history[*])
- [x] Insert `report_uploads(status='received')` before parsing; each `project_history` row must set `source_upload_id`
- [ ] On success update `status='parsed'`; on error `status='failed'` with `notes`
- [x] Azure Chat Completions (HTTP); JSON retry/fallback; low temperature; optional `DRY_RUN`
- [x] `python-docx` chunking (paragraphs+tables), token-safe; Pydantic `ParsedHistoryRow`
- [ ] Aggregation: normalize names, group by project, merge fragments within same file
- [ ] Idempotency: row-level hash, skip unchanged
- [ ] `attachment_url`: set when archived file path is available

#### 2B5 - Token Limits & Reliability (✅ Completed 2025-08-29)
- [x] Safe truncation & token estimation; env vars:
  - `AZURE_OPENAI_MAX_CONTEXT=8000` / `AZURE_OPENAI_MAX_INPUT=3500` / `AZURE_OPENAI_MAX_OUTPUT=4000` / `AZURE_OPENAI_SAFETY_BUFFER=500`
- [x] Smart `max_tokens` allocation; truncated JSON recovery (strip ```json fences, parse incomplete arrays, regex fallback)
- [x] Tests & docs: `backend/tests/test_token_limits.py`, `backend/Token_Limits_Configuration.md`
- [x] Verified: 12,711 char doc → 27 rows extracted; log includes smart allocation

#### 2B7 - Folder → DB Orchestrator
- [ ] Process only `.docx` matching filename pattern; archive to `REPORT_UPLOAD_ARCHIVE_DIR/{year}/{cw}/{category}/...`; set `attachment_url`
- [x] Project mapping: establish truth source (`project_name → project_code` via CSV/DB); load+cache; unresolved flagged — 2025-08-29
  - Implemented CSV-backed loader `backend/app/utils.py:get_project_code_by_name`
  - Replaced keyword mapper in `backend/app/main.py` with CSV mapper
  - Importer now skips rows when mapping is missing (warns)
- [ ] Content parser (non-LLM path): detect project sections (headings/colon patterns, MW capacity), aggregate bullets into normalized summary; set `entry_type="Report"`
- [ ] CW/date logic: derive `cw_label` from filename; compute ISO-week Monday `log_date`
- [ ] UPSERT key: `(project_code, log_date, entry_type='Report')`; idempotent via content hash
- [ ] Run logging: record counts (processed/created/updated/skipped), errors, source path

#### Tests & Acceptance
- [x] Frontend: Commuting + Task Status + queue (TODO)
- [x] Unit: `report_uploads` lifecycle + dedup; status transitions (received→parsed/failed)
- [x] Unit: single docx import yields N `project_history` rows, each linked to `source_upload_id`
- [x] Integration: bulk folder import marks failed files but doesn’t block others
- [ ] Query: given `report_uploads.id`, fetch linked `project_history`; given `project_history.id`, fetch upload metadata
- [ ] Edge cases: ISO-week year boundaries, mapping normalization, orchestrator unit tests
- [x] Single-File Import — Verification (E2E/Mock ✅ 2025-08-29)
  - [x] Rows persisted with correct `cw_label`/`category`/`source_upload_id`/`entry_type='Report'`
  - [ ] Idempotency check: re-run → no new rows or only updates when changed
  - Precondition: `AZURE_OPENAI_E2E=1` + env set; input: `/Users/yuxin.xue/Projects/qenergy-platform/uploads/2025_CW01_DEV.docx`
  - Assert: `report_uploads.status='parsed'`, `parsed_at` NOT NULL; ≥1 `project_history` row with correct ISO-week Monday `log_date` (e.g., 2025-01-06)

#### Prompt / Output Control
- [x] Enforce strict JSON formatting in the prompt, or use Azure’s response_format={"type": "json_object"} if supported.
- [x] Move the schema definition out of the system prompt and enforce it separately with a Pydantic model for strict validation, eliminating the need for fragile regex-based post-processing.

#### Documentation
- [ ] README: add “Upload & Import” flow diagram, CLI examples, error-handling notes

---

### P0 Phase 2C — Weekly Reports Editor (Cards) MVP
Goal: Create/save weekly reports via cards with correct CW logic.
- [ ] Backend: Weekly Reports APIs
  - `UPSERT /api/project-history` (key: project_code + log_date); server computes `cw_label` (Monday-based)
  - `GET /api/project-history?project_code&cw_range&category`
  - `GET /api/project-history/content?project_code&cw_label&category` (return single summary text)
- [ ] Frontend: Cards Editor
  - Year/CW selectors; compute Monday `log_date`; `cw_label="CW##"`
  - Fields & validations: entry_type (enum), summary required; email/URL checks
  - Category enum validation: Development, EPC, Finance, Investment
  - Save only dirty entries; per-card error display
  - Service layer (`frontend/lib/api/reports.ts`) + unit tests

Acceptance for Phase 2C:
- Saving creates/updates by (project_code, log_date) with correct cw_label
- Validation errors surfaced per card; unit tests pass

---

### P0 Phase 2D — Analysis Core (Sync) + Results Listing
Goal: Run basic analysis (sync/small batches) and list results.
- [ ] Backend: Analysis Core
  - `POST /api/reports/analyze` (trigger sync analysis)
  - `GET /api/weekly-analysis?past_cw&latest_cw&language` (list)
  - `GET /api/projects/by-cw-pair?past_cw&latest_cw` (list candidate projects present in either CW)
  - Compute: risk level, similarity, negative words; persist to `weekly_report_analysis`
  - Simple cache reuse (skip unchanged via timestamps/hash)
  - LLM client wiring (Azure OpenAI): env `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`; retries and 429 backoff
  - Data source for by-cw-pair endpoint: derive from `project_history` existence in either CW
- [ ] Frontend: Results Display (MVP)
  - Charts for risk/similarity; basic table/cards; historical records view
  - Service layer (`frontend/lib/api/analysis.ts`) + tests

Acceptance for Phase 2D:
- Analysis runs and persists for small datasets; results list renders
- Cache reuse verified on repeat runs; unit/integration tests pass

---

### P0 Phase 2E — WebSocket Analysis, Export & Ask AI
Goal: Real-time analysis UX with caching, export, and AI Q&A.
- [ ] Backend: WebSocket Workflow
  - WS `/ws/analysis`: events `analysis:start|progress|item|stop|done`
  - Concurrency control; backoff/retry on 429; cancel on stop
  - Caching keyed by (project_code, past_cw, latest_cw, language)
  - Export: `GET /api/weekly-analysis/export?...` (Excel)
  - `GET /api/cw/available?year=YYYY` (list CW labels that have data)
  - `POST /api/weekly-analysis/chat` (LLM Q&A over selected results)
- [ ] Frontend: Advanced Analysis UI
  - Start/Stop controls; progress bar; per-row status
  - Export to Excel; Ask AI modal with FAQ presets (context = selected CW pair + results)
  - Language toggle (KO/EN) that drives prompts and UI labels
  - Rate limiting guardrails in UI; error toasts

Acceptance for Phase 2E:
- WS analysis flows run end-to-end; progress visible; stop cancels work
- Export produces expected dataset; Ask AI works with current context
- Basic rate limiting in place; tests for WS event handling

---

### P0 Phase 3 — Project Management Integration & Backend Integration
Goal: Integrate report analysis with project management and connect frontend to real backend.
- [ ] Backend: Complete Project CRUD
  - `GET /api/projects` (pagination, search by `project_code|project_name|portfolio_cluster`, filter `status`)
  - `POST /api/projects` (create)
  - `PUT /api/projects/{project_code}` (update by business key)
  - `DELETE /api/projects/{project_code}` (delete by business key)
  - Complete SQLAlchemy models for `projects` and `project_history`
- [ ] Backend: Project History API
  - `GET /api/project-history` (filters: `project_code`, CW range, `category`)
  - `POST /api/project-history` (create; upsert on `(project_code, log_date)`)
- [ ] Frontend ↔ Backend Integration (Replace Mock with Real)
  - Switch API base to backend; ensure CORS works (allow `http://localhost:3000`)
  - Document env keys: `API_V1_STR=/api`, `BACKEND_CORS_ORIGINS`, `DATABASE_URL`, `NEXT_PUBLIC_API_URL`
  - Project Management uses real `GET/POST/PUT/DELETE`
  - Basic error display (toast) and optimistic UI kept simple
  - Update service layer to call real endpoints instead of mock data; update tests accordingly
- [ ] Frontend: Project-Analysis Integration
  - Display analysis results in ProjectDetail
  - Filter analysis by CW (Calendar Week)
  - Link analysis results to project status
  - Project history with analysis insights
- [ ] Backend: Seed Data
  - Optional script to insert sample projects and analysis data for testing
- [ ] Backend: External PPM Project List integration (optional)
  - `GET /api/integrations/ppm/projects?date=YYYY-MM-DD` (use Monday of CW)
  - Env: `QENERGY_PPM_API_KEY`, base URL; enforce TLS verification
- [ ] Frontend: Project Management UX (per spec)
  - Search box (debounced) over `project_code|project_name|portfolio_cluster`; toggle \"Show Active Only\"
  - Table: columns (Code|Name|Portfolio|Status pill), row selection via checkbox
  - Server-side sorting by any visible column; server-side pagination (default 20; remember last page size)
  - Actions: Add Project modal (validations; server conflict shows field error); Remove Selected with confirm; Upload Excel → Bulk Replace flow
- [ ] Backend: Projects Bulk Replace (Excel/CSV)
  - Validate entire file (schema, required fields, status 0/1, duplicates)
  - On any row invalid → no change; return per-row error list (downloadable)
  - On all valid → delete all and insert all (replace-all); server sets timestamps; ignore client timestamps

Acceptance for Phase 3:
- Project list renders with real database data
- Frontend successfully communicates with backend; CORS and API prefix configured
- E2E smoke: upload → analyze → view flow works end-to-end
- CW-based filtering works
- Create/update/delete operations persist
- Error logging enabled and visible; basic unit/integration tests pass
 - Project Management supports search/sort/pagination, add modal, bulk delete, and bulk replace with per-row error reporting

---

### P1 Phase 4A — Project Detail (History Viewer)
Goal: Read-only screen to review a project’s Weekly Report history over a selected CW period.
- [ ] Frontend: Project Detail screen
  - Filters: Project (required), Category (opt), Start/End CW pickers (Year + CW; Monday-based rule)
  - Results: Table with columns (Project Code/Name/Category + one column per CW in range)
  - Each CW cell shows summary snippet (tooltip with full text); sticky first columns; virtual horizontal scroll for long ranges
  - Actions: Search, Ask AI (on result set), Download Excel (full summaries)
- [ ] Backend: Range query API for weekly reports by project and CW range; join with projects for names

Acceptance for Phase 4:
- Query returns expected rows across CW range; empty states handled
- Excel export matches visible table with full summaries
- Ask AI modal wired with current result set as context

---

### P1 Phase 4B — Advanced Features & Polish
Goal: Add advanced features and improve user experience.
- [ ] Backend: Bulk Operations
  - `POST /api/projects/bulk-upload` (validate file schema)
  - Batch analysis processing
  - Progress tracking for long operations
- [ ] Frontend: Enhanced UI/UX
  - Advanced filtering and search
  - Export functionality
  - Real-time updates
  - Better error handling and user feedback
- [ ] Backend: Performance & Caching
  - Analysis result caching
  - Database query optimization
  - Rate limiting

Acceptance for Phase 4:
- Bulk operations work efficiently
- UI is responsive and user-friendly
- Performance is acceptable for production use

---

### P1 Phase 6 — Developer Experience & Ops
Goal: Improve development workflow and deployment.
- [x] Cross-platform deployment scripts for one-click installation — 2025-08-20
- [x] Alembic baseline + first migration reflecting current schema — 2025-08-26
- [ ] Docker Compose (postgres + backend; optional frontend)
- [ ] Makefile / task runner for common commands
- [ ] CI/CD pipeline setup

Acceptance for Phase 6:
- Easy local development setup
- Automated testing and deployment
- Production-ready deployment process

---

### P2 Later — Advanced Features
- AuthN/AuthZ (JWT), capture `created_by/updated_by` from user
- React Query/Zustand for server/client state
- WebSockets for real-time analysis progress
- Advanced AI/ML features
- Rate limiting and request logging
- Multi-language support

---

## C) Database (Canonical Schema)

Tables (SQL excerpts; authoritative):

- Projects
```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_code VARCHAR(32) UNIQUE NOT NULL,
  project_name VARCHAR(255) NOT NULL,
  portfolio_cluster VARCHAR(128),
  status INTEGER NOT NULL CHECK (status IN (0, 1)),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by VARCHAR(255) NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by VARCHAR(255) NOT NULL
);
```

- Project History
```sql
CREATE TABLE project_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_code VARCHAR(32) NOT NULL REFERENCES projects(project_code),
  category VARCHAR(128),
  entry_type VARCHAR(50) NOT NULL CHECK (entry_type IN ('Report','Issue','Decision','Maintenance','Meeting minutes','Mid-update')),
  log_date DATE NOT NULL,
  cw_label VARCHAR(8),
  title VARCHAR(255),
  summary TEXT NOT NULL,
  next_actions TEXT,
  owner VARCHAR(255),
  attachment_url VARCHAR(1024),
  source_text TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by VARCHAR(255) NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by VARCHAR(255) NOT NULL,
  source_upload_id UUID REFERENCES report_uploads(id) ON DELETE SET NULL,
  UNIQUE(project_code, log_date)
);
```

- Report Uploads
```sql
CREATE TABLE report_uploads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  original_filename VARCHAR(512) NOT NULL,
  storage_path VARCHAR(1024) NOT NULL, -- currently local path
  mime_type VARCHAR(128) NOT NULL,
  file_size_bytes BIGINT NOT NULL,
  sha256 CHAR(64) NOT NULL UNIQUE, 
  status VARCHAR(16) NOT NULL CHECK (status IN ('received','parsed','failed','partial')),
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  parsed_at TIMESTAMPTZ,

  cw_label VARCHAR(8),
  doc_date DATE,
  notes TEXT,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by VARCHAR(255) NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by VARCHAR(255) NOT NULL
);
```

- Weekly Report Analysis
```sql
CREATE TABLE weekly_report_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_code VARCHAR(32) NOT NULL REFERENCES projects(project_code),
  category VARCHAR(128),
  cw_label VARCHAR(8) NOT NULL,
  language VARCHAR(2) NOT NULL DEFAULT 'EN',
  risk_lvl DECIMAL(5,2) CHECK (risk_lvl BETWEEN 0 AND 100),
  risk_desc VARCHAR(500),
  similarity_lvl DECIMAL(5,2) CHECK (similarity_lvl BETWEEN 0 AND 100),
  similarity_desc VARCHAR(500),
  negative_words JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by VARCHAR(255) NOT NULL,
  UNIQUE(project_code, cw_label, language)
);
```

Indexes (selection):
```sql
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_project_history_project_code ON project_history(project_code);
CREATE INDEX idx_project_history_log_date ON project_history(log_date);
CREATE INDEX idx_analysis_project_cw ON weekly_report_analysis(project_code, cw_label);
```

---

## D) Deployment Scripts (Completed)

### Cross-Platform Installation & Management
- **`scripts/install.sh`** - macOS/Linux one-click installation
  - Auto-detects OS and installs dependencies
  - Sets up PostgreSQL, Node.js, pnpm, Conda
  - Creates database with schema and sample data
  - Installs frontend and backend dependencies
  - Verifies installation

- **`scripts/install.bat`** - Windows one-click installation
  - Requires Administrator privileges
  - Installs Chocolatey, Node.js, pnpm, PostgreSQL, Miniconda
  - Sets up database and backend environment
  - Installs frontend dependencies

- **`scripts/start.sh`** - macOS/Linux service management
  - `start` - Start all services (PostgreSQL, Backend, Frontend)
  - `stop` - Stop all services
  - `status` - Check service status
  - `restart` - Restart all services

- **`scripts/start.bat`** - Windows service management
  - Same functionality as start.sh for Windows

- **`scripts/test.sh`** - Comprehensive health checks
  - Database connection and schema validation
  - Backend API testing
  - Frontend accessibility testing
  - Performance benchmarking
  - Integration testing

- **`scripts/demo.sh`** - Platform demonstration
  - Service status overview
  - Database schema and sample data display
  - API endpoint documentation
  - Frontend feature highlights
  - Architecture overview
  - Development workflow guidance

### Usage Examples
```bash
# macOS/Linux
chmod +x scripts/*.sh
./scripts/install.sh    # One-click installation
./scripts/start.sh      # Start all services
./scripts/test.sh       # Health check
./scripts/demo.sh       # Platform demo

# Windows
scripts\install.bat     # One-click installation (Admin)
scripts\start.bat       # Start all services
```

### Service Ports
- PostgreSQL: 5432
- FastAPI Backend: 8002
- Next.js Frontend: 3000

---

## E) Risks & Mitigations
- Schema is authoritative; any spec conflicts defer to schema.
- Timezone: all timestamps in UTC; clients must not send server timestamps.
- `project_code` is the business key; CRUD operations should prefer it over UUIDs.
- Early integration avoids large refactors later; keep UI changes minimal while swapping data sources.