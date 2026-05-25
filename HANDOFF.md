# Football AI — Complete Handoff Document

> Last updated: 2026-05-24 (UI/UX overhaul pass)  
> Project root: `/Users/amrabujabal/Downloads/football-ai`

---

## 1. Project Overview

**What it is:** A computer-vision analytics pipeline that ingests broadcast football video, detects and tracks players frame-by-frame, computes advanced physical + tactical metrics, persists them to a database, and serves them via a REST API to a Next.js dashboard.

**Target customer:** UAE football academies (Al Ain FC, Al Jazira, Shabab Al Ahli feeders, private academies) that can't afford Opta/StatsBomb.

**Business model:** Sell proprietary player-profile data + a branded club dashboard to academies on a SaaS subscription.

**Language:** Bilingual — English + Arabic (`name_ar` fields throughout the DB schema).

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Detection | YOLOv10x (object detection) + SAM 2 Hiera Large (segmentation) |
| Re-ID | TransReID / OSNet (HOG stub currently wired, upgrade pending) |
| OCR | PaddleOCR (jersey number recognition) |
| Tracking | SORT (Kalman filter + Hungarian algorithm) |
| Metrics | Custom Python — pitch control (Spearman 2018), pressing, physical |
| Backend | FastAPI + SQLAlchemy 2.0 (sync) |
| Database | SQLite for local dev → PostgreSQL + pgvector for production |
| Async queue | Celery + Redis (wired in settings, not yet implemented) |
| Frontend | Next.js 14 (App Router, TypeScript, Tailwind CSS, Recharts, Lucide React) |
| Python env | Anaconda — base env at `/opt/anaconda3` (conda init commented out in .zshrc) |

---

## 3. Directory Map

```
football-ai/
├── CLAUDE.md                    # Project instructions for Claude Code
├── HANDOFF.md                   # ← this file
├── requirements.txt             # Python deps
├── config/
│   └── settings.py              # Pydantic-settings config (all tunables)
├── detection/
│   ├── detector.py              # YOLOv10 + SAM 2 — requires torch
│   └── segmentor.py
├── tracking/
│   ├── tracker.py               # SORT + re-ID (HOG stub)
│   └── reid.py
├── metrics/
│   ├── physical.py              # distance, speed, sprint/hi-run bouts
│   ├── pitch_control.py         # Spearman 2018 Voronoi model — requires torch
│   └── pressing.py              # press detection + success rate
├── utils/
│   └── homography.py            # PitchHomography class + draw_pitch()
├── database/
│   ├── models.py                # SQLAlchemy ORM models
│   ├── session.py               # engine + SessionLocal factory
│   └── repository.py            # save_pipeline_results(), PipelineResult dataclass
├── api/
│   ├── main.py                  # FastAPI app, CORS, router mounts
│   ├── deps.py                  # get_db() dependency
│   ├── schemas/
│   │   └── __init__.py          # Shared Pydantic response schemas
│   └── routers/
│       ├── academies.py
│       ├── matches.py           # Match CRUD + analytics endpoints
│       ├── players.py           # Player CRUD + stats endpoints
│       └── metrics.py
├── scripts/
│   └── run_pipeline.py          # CLI entry point for processing a video
├── dashboard/                   # Next.js 14 frontend
│   ├── package.json
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   ├── .env.local.example       # Copy → .env.local and fill in
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   ├── page.tsx             # Match list (home page)
│   │   ├── matches/[id]/page.tsx  # Match detail: summary + player table
│   │   └── players/[id]/page.tsx  # Player profile: latest stats + history chart
│   ├── components/
│   │   ├── Nav.tsx
│   │   ├── MatchCard.tsx
│   │   ├── PitchControlBar.tsx  # Two-colour home/away pitch control bar
│   │   ├── PlayerTable.tsx      # Sortable player stats table (client component)
│   │   ├── StatsHistoryChart.tsx # Recharts bar chart (distance, sprints, presses)
│   │   └── StatusBadge.tsx
│   └── lib/
│       ├── api.ts               # Typed fetch wrappers for all API endpoints
│       └── types.ts             # TypeScript interfaces mirroring Pydantic schemas
│
│   Design system files:
│   ├── tailwind.config.ts       # Custom tokens: Fira Code/Sans fonts, navy/amber palette
│   └── app/globals.css          # CSS custom properties, .card, .kpi-*, .badge-*, .data-table
└── tests/
    ├── test_api/
    │   ├── conftest.py          # In-memory SQLite fixtures (StaticPool)
    │   └── test_endpoints.py    # 29 tests — all API endpoints
    ├── test_db/
    │   └── test_repository.py   # 8 tests — save_pipeline_results()
    ├── test_metrics/
    │   └── test_physical.py     # 13 tests — distance, speed, bouts
    └── test_utils/
        └── test_homography.py   # 23 tests — PitchHomography + draw_pitch
```

---

## 4. Environment Setup

### Python (no conda init in .zshrc — use full paths)

```bash
# Python interpreter
/opt/anaconda3/bin/python

# pip
/opt/anaconda3/bin/pip

# Install deps
/opt/anaconda3/bin/pip install -r requirements.txt

# Run any script
/opt/anaconda3/bin/python scripts/run_pipeline.py --video path/to/video.mp4 \
  --match-id <uuid> --academy-id <uuid>
```

> **Note:** `conda activate football-ai` won't work unless you run `conda init zsh` first (or manually source `conda.sh`). The base anaconda env at `/opt/anaconda3` has all required packages installed.

### Node (dashboard)

```bash
cd dashboard
npm install
cp .env.local.example .env.local   # fill in NEXT_PUBLIC_ACADEMY_ID
npm run dev                         # → http://localhost:3000
```

### FastAPI backend

```bash
/opt/anaconda3/bin/python -m uvicorn api.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

---

## 5. Running Tests

```bash
cd /Users/amrabujabal/Downloads/football-ai

# All torch-free tests (94 total) — these all pass
/opt/anaconda3/bin/python -m pytest tests/ \
  --ignore=tests/test_detection \
  -q

# Just API tests (29 tests)
/opt/anaconda3/bin/python -m pytest tests/test_api/ -v

# Just homography tests (23 tests)
/opt/anaconda3/bin/python -m pytest tests/test_utils/ -v

# Just metrics tests (30 tests — includes pressing + pitch_control)
/opt/anaconda3/bin/python -m pytest tests/test_metrics/ -v
```

> **Why ignore test_detection only?**  
> `tests/test_detection/` imports `detector.py` → `torch` which is not installed in the base env (~2 GB). `test_pitch_control.py` was also previously ignored, but after extracting `Track`/`TrackedFrame` to `tracking/types.py` (no torch dep), it now runs cleanly.

---

## 6. Database

### ORM Models (`database/models.py`)

| Table | Key fields |
|---|---|
| `academies` | id (UUID), name, name_ar, city, country, tier |
| `players` | id (UUID), academy_id, name, name_ar, position, jersey_number |
| `matches` | id (UUID), academy_id, home_team, away_team, processing_status, fps |
| `player_match_stats` | player_id, match_id, team, all metric columns |
| `development_scores` | player_id, week_start, overall/physical/tactical/technical scores |

**UUID handling:** All IDs use SQLAlchemy's `Uuid` type (not `postgresql.UUID`) so the same models work with both SQLite (dev) and PostgreSQL (prod). No dialect-specific imports.

### Session factory (`database/session.py`)

```python
from database.session import SessionLocal, engine

# Get a session
db = SessionLocal()
db.close()

# Use in FastAPI via dependency injection
from api.deps import get_db   # yields Session, closes on teardown
```

**SQLite-specific:** `make_engine()` automatically adds `check_same_thread: False` when the URL starts with `sqlite`.

### Default DB URL

`sqlite:///./dev.db` (set in `config/settings.py`). Override via `.env`:
```
database_url=postgresql+asyncpg://user:password@localhost:5432/football_ai
```

### Create tables

```bash
# One-liner — runs Base.metadata.create_all on the configured DB
/opt/anaconda3/bin/python -c "
from database.session import engine
from database.models import Base
Base.metadata.create_all(engine)
print('Tables created.')
"
```

---

## 7. API Endpoints

Base URL: `http://localhost:8000`  
Docs: `http://localhost:8000/docs`

### Matches

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/matches/?academy_id=<uuid>` | List all matches for an academy, newest first |
| `POST` | `/api/v1/matches/` | Register a new match (video upload is separate) |
| `GET` | `/api/v1/matches/{id}/summary` | Aggregated home/away stats for the match card |
| `GET` | `/api/v1/matches/{id}/players` | All players + stats for a match |
| `GET` | `/api/v1/matches/{id}/processing-status` | Poll pipeline status |
| `POST` | `/api/v1/matches/{id}/upload-video` | **501 Not Implemented** — stub |

### Players

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/players/` | Register a new player |
| `GET` | `/api/v1/players/{id}/stats` | Stats history (all matches), newest first. Optional `?match_id=` filter |
| `GET` | `/api/v1/players/{id}/profile` | **501 Not Implemented** — stub |
| `GET` | `/api/v1/players/{id}/heatmap` | **501 Not Implemented** — stub |

### Academies / Metrics

`/api/v1/academies/` and `/api/v1/metrics/` routers exist but have minimal implementation. See `api/routers/academies.py` and `api/routers/metrics.py`.

### Response Schemas (`api/schemas/__init__.py`)

- `MatchSummaryResponse` — match card data (pitch control %, top speeds, press counts)
- `MatchPlayerResponse` — one player's stats in a match
- `PlayerStatsResponse` — one match entry in a player's history
- All use Pydantic v2 `ConfigDict(from_attributes=True)`

---

## 8. Pipeline (`scripts/run_pipeline.py`)

```bash
/opt/anaconda3/bin/python scripts/run_pipeline.py \
  --video /path/to/match.mp4 \
  --match-id <match-uuid> \
  --academy-id <academy-uuid>
```

**Pipeline stages:**
1. Load video frames
2. YOLO detection → bounding boxes per frame  
3. SAM 2 segmentation → player masks  
4. Tracking → persistent track IDs across frames  
5. Physical metrics → `compute_physical_metrics()` per track (distance, speed, sprints)  
6. Pitch control → `compute_pitch_control()` per frame  
7. Pressing → `PressDetector` per frame  
8. Homography → `PitchHomography` pixel→pitch coordinate transform  
9. Persist → `save_pipeline_results()` writes all metrics to DB  

**Requires:** torch + model weights in `data/model_weights/`. Download weights:
```bash
bash scripts/download_weights.sh
```

---

## 9. Homography (`utils/homography.py`)

```python
from utils.homography import PitchHomography, draw_pitch

h = PitchHomography()

# Option A: fit from a real frame (HSV white-pixel detection + Hough lines)
success = h.fit(frame)          # frame: np.ndarray BGR

# Option B: fit from known point pairs (for testing / manual calibration)
pixel_pts = np.array([[0,0],[640,0],[640,480],[0,480]], dtype=np.float32)
pitch_pts = np.array([[0,0],[105,0],[105,68],[0,68]], dtype=np.float32)
h.fit_from_points(pixel_pts, pitch_pts)

# Transform
pitch_xy = h.pixel_to_pitch((320, 240))    # → (52.5, 34.0) metres
pixel_xy = h.pitch_to_pixel((52.5, 34.0)) # inverse

# Batch (faster for many points)
pitch_pts = h.batch_pixel_to_pitch(pixel_array)  # shape (N,2)

# Render synthetic pitch image
frame = draw_pitch(width=1920, height=1080, perspective=False)
```

**Settings used:**
- `pitch_length = 105.0 m`, `pitch_width = 68.0 m` (standard)
- `frame_width = 1920`, `frame_height = 1080`

---

## 10. Physical Metrics (`metrics/physical.py`)

```python
from metrics.physical import compute_physical_metrics, PhysicalMetrics

result: PhysicalMetrics = compute_physical_metrics(
    track_id=42,
    pitch_positions=np.array([[x0,y0],[x1,y1],...]),  # metres, shape (N,2)
    fps=25.0,
    hi_speed_threshold=5.5,   # m/s — from settings.high_intensity_speed
    sprint_threshold=7.0,     # m/s — from settings.sprint_speed
)

result.distance_covered_m   # float, metres
result.top_speed_ms         # float, m/s
result.avg_speed_ms         # float, m/s
result.sprint_count         # int, number of sprint bouts (rising edges)
result.hi_run_count         # int, high-intensity run bouts
```

---

## 11. DB Persistence (`database/repository.py`)

```python
from database.repository import save_pipeline_results, PipelineResult

result = PipelineResult(
    match_id=uuid.UUID("..."),
    fps=25.0,
    physical_metrics={track_id: PhysicalMetrics(...)},
    pitch_control_by_track={track_id: 0.58},
    press_stats={track_id: press_stats_obj},   # any object with .press_count, .press_success_rate, .trigger_accuracy
    track_teams={track_id: "home"},            # "home" | "away" | None
)

rows_created = save_pipeline_results(session, academy_id=uuid, result=result)
session.commit()
```

`save_pipeline_results` creates anonymous `Player` records (name=`"Track {id}"`) if they don't exist, then writes `PlayerMatchStats` rows and sets `match.processing_status = "done"`.

**Protocol pattern:** `press_stats` values only need to satisfy `PressStatsLike(Protocol)`:
```python
class PressStatsLike(Protocol):
    press_count: int
    press_success_rate: float
    trigger_accuracy: float
```
This breaks the `torch` import chain — `repository.py` never imports from `metrics.pressing` directly.

---

## 12. Dashboard (`dashboard/`)

### Pages

| Route | What it shows |
|---|---|
| `/` | Grid of match cards for the configured academy |
| `/matches/[id]` | Pitch control bar, home/away speed+press stat cards, sortable player table |
| `/players/[id]` | Latest-match metric pills + bar chart (distance/sprints/presses across last 8 matches) + full history table |

### Configuration

```bash
# dashboard/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ACADEMY_ID=<paste UUID from DB>
```

Get the academy UUID after creating one via the API or seeding the DB:
```bash
/opt/anaconda3/bin/python -c "
from database.session import SessionLocal
from database.models import Academy
db = SessionLocal()
print(db.query(Academy).first().id)
"
```

### Running dev

```bash
cd dashboard
npm run dev     # → http://localhost:3000
npm run build   # production build (clean, no TS errors)
```

### Key component notes

- **`PlayerTable.tsx`** — client component with `useState` for column-sort. Click any column header to sort; click again to reverse.
- **`StatsHistoryChart.tsx`** — Recharts `BarChart` with dual Y-axes: left for distance (metres), right for sprints/presses counts.
- **`PitchControlBar.tsx`** — normalises home+away percentages so the bar always fills 100% even when only a few players are tracked.
- **`api.ts`** — all fetches use `cache: "no-store"` so the dashboard always shows fresh data (no Next.js caching).

---

## 13. Test Infrastructure

### API tests (`tests/test_api/`)

**Key fix applied:** `conftest.py` uses `StaticPool` from `sqlalchemy.pool`. Without it, each SQLAlchemy session creates a new in-memory SQLite connection (= new empty database with no tables). `StaticPool` forces all checkouts to reuse the same underlying connection, so `Base.metadata.create_all` is visible to every session.

```python
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,   # ← critical
)
```

**Fixtures:**
- `db_engine` (module-scoped) — creates in-memory SQLite, runs `create_all`
- `SessionFactory` (module-scoped) — bound to the engine
- `db_session` (function-scoped) — fresh session, rolled back after each test
- `client` (function-scoped) — `TestClient` with `get_db` dependency overridden
- `seeded` (function-scoped) — inserts Academy + Match + 2 Players + 2 PlayerMatchStats, commits

### Test counts (all passing)

| Suite | Tests |
|---|---|
| `test_api/test_endpoints.py` | 29 |
| `test_db/test_repository.py` | 8 |
| `test_metrics/test_physical.py` | 13 |
| `test_metrics/test_pitch_control.py` | 8 |
| `test_metrics/test_pressing.py` | 10 |
| `test_metrics/test_pitch_control_homography.py` | 5 |
| `test_utils/test_homography.py` | 23 |
| **Total** | **94** |

Excluded (need torch):
- `tests/test_detection/` — imports `detector.py` → torch (~2 GB dep)

---

## 14. Dashboard Design System

Generated via the **UI/UX Pro Max** skill. Style: *Data-Dense Dashboard*. All tokens live in `dashboard/tailwind.config.ts` and `dashboard/app/globals.css` as CSS custom properties — never use raw hex values in components.

### Color Palette

| Token | Hex | Usage |
|---|---|---|
| `--color-primary` / `primary-800` | `#1E40AF` | Nav background, primary CTA, KPI values |
| `--color-secondary` / `primary-500` | `#3B82F6` | Secondary data bars, links |
| `--color-accent` / `accent-600` | `#D97706` | Away team, amber highlights |
| `--color-home` | `#2563EB` | Home team labels, bars, KPIs |
| `--color-away` | `#D97706` | Away team labels, bars, KPIs |
| `--color-background` | `#F8FAFC` | Page background |
| `--color-surface` | `#FFFFFF` | Card background |
| `--color-border` | `#E2E8F0` | Card borders, dividers |

### Typography

- **Headings / all numbers:** `Fira Code` (monospace, loaded from Google Fonts) — gives the dashboard a precise, technical feel; all numeric cells use `font-family: 'Fira Code'` + `tabular-nums` so columns never jitter
- **Body / labels:** `Fira Sans` — clean, readable, pairs well with Fira Code
- **Type scale used:** `text-2xs` (0.625rem) for labels/badges → `text-xs` (0.75rem) for secondary text → `text-sm` (0.875rem) for table rows → `text-base` (1rem) for body → `text-xl`/`text-2xl` for KPI values

### Spacing & Grid

- **Card padding:** 16px (`--card-padding`)
- **Grid gap:** 8px (`--grid-gap`)
- **Card radius:** 10px (`--card-radius`)
- **Header height:** 56px (`--header-height`)
- **Spacing rhythm:** 4/8px increments throughout — never arbitrary values

### Reusable CSS Classes (defined in `globals.css`)

| Class | What it is |
|---|---|
| `.card` | White surface, border, 10px radius, subtle shadow, `border-color` + `box-shadow` transitions |
| `.card-hover` | Add to `<Link>` cards — blue shadow + border on hover |
| `.kpi-label` | 0.625rem, semibold, uppercase, wide tracking, slate-400 |
| `.kpi-value` | 1.5rem, bold, Fira Code, leading-none — for big stat numbers |
| `.badge-done/processing/pending/failed` | Rounded pill with colored dot + text + ring |
| `.dot-done/processing/pending/failed` | 8px coloured status dot (standalone) |
| `.team-pill-home` | Blue micro-badge for home team |
| `.team-pill-away` | Amber micro-badge for away team |
| `.section-title` | 0.75rem, semibold, uppercase, wide tracking — section headings |
| `.data-table` | Full table system: `thead`, `th` (sortable style), `td`, hover rows |
| `.skip-link` | Visually hidden, appears on focus — keyboard accessibility |

### Component Notes

**`Nav.tsx`**
- Brand icon is a hand-coded SVG pitch diagram (no emoji, no external icon dep)
- Brand name uses Fira Code: `football_ai`
- `sticky top-0 z-40` — stays visible while scrolling
- Skip-to-main-content link for keyboard users

**`StatusBadge.tsx`**
- Renders a colored `<span>` dot + text + ring-1 border — three visual channels for status (shape, color, text), not color-only

**`MatchCard.tsx`**
- Uses `card card-hover` — hover lifts with a blue shadow
- `<time datetime="...">` for semantic date
- `aria-label` on the `<Link>` describes the full match for screen readers
- Lucide `<ChevronRight>` icon with `aria-hidden="true"`

**`PitchControlBar.tsx`**
- `role="img"` + `aria-label` with exact percentages for screen readers
- Colored legend dots instead of team-name-only labels
- Percentages shown inside the bar segments with Fira Code font

**`PlayerTable.tsx`**
- `aria-sort="ascending|descending|none"` on every `<th>` — screen reader announces sort state
- `ArrowUp`/`ArrowDown`/`ArrowUpDown` Lucide icons replace text arrows
- `tabular-nums` + Fira Code on every numeric `<td>` — no column width jitter on sort
- Rows link to player profile via `<Link>` with focus ring

**`StatsHistoryChart.tsx`**
- Custom `<CustomTooltip>` component — clean white card, Fira Code values, colored dot per series
- `vertical={false}` on CartesianGrid — horizontal rules only, data reads cleanly
- `cursor={{ fill: "rgba(30,64,175,0.04)" }}` — subtle hover highlight
- Colors: navy `#1E40AF` (Distance), blue `#3B82F6` (Sprints), amber `#D97706` (Presses)
- `maxBarSize={40}` — bars don't go comically wide on large screens

### Accessibility Checklist (all passing)

- [x] No emoji used as icons — SVG only (Lucide + hand-coded)
- [x] `cursor-pointer` inherited from Tailwind's `<button>`/`<a>` defaults; all clickable elements are semantic `<Link>` or `<button>`
- [x] Hover transitions 150–200ms with `ease-out` — within the 150–300ms UX window
- [x] Text contrast: slate-900 on white = 16.1:1 (well above 4.5:1 AA minimum)
- [x] Focus rings: `focus-visible:ring-2 focus-visible:ring-primary-600` on all interactive elements
- [x] `prefers-reduced-motion` — no JS animations; CSS transitions only, no `@keyframes`
- [x] `aria-sort` on sortable table headers
- [x] `aria-label` on icon-only elements
- [x] `role="img"` + `aria-label` on the pitch control bar
- [x] Skip link: `<a href="#main-content">Skip to main content</a>` in Nav
- [x] `<main id="main-content">` on every page
- [x] `<nav aria-label="Breadcrumb">` on detail pages
- [x] `<time datetime="...">` on match dates
- [x] `tabular-nums` on every numeric data cell


## 16. What's Left To Build

Priority order (agreed in this sprint):

### A. ✅ Wire homography into metrics (DONE — 2026-05-24)

`compute_pitch_control()` now accepts `homography: Optional[PitchHomography] = None`.
`PressAnalyser.__init__` now accepts `homography: Optional[PitchHomography] = None`.
Both fall back to naive linear conversion when `homography=None`.
The `self._closing_speed` side-effect assignment bug in `pressing.py` was removed.
`Track`/`TrackedFrame` extracted to `tracking/types.py` (breaks torch chain — press + pitch_control tests now run without torch).

**To wire in the pipeline** (`scripts/run_pipeline.py`):
```python
from utils.homography import PitchHomography
h = PitchHomography()
h.fit(first_frame)   # fits from first video frame
# then pass h= to compute_pitch_control() and PressAnalyser()
```

### B. ✅ Upload video endpoint (DONE — 2026-05-24)

`POST /api/v1/matches/{id}/upload-video` is fully implemented:
1. Validates match exists (404) and file extension (400)
2. Saves file to `settings.raw_dir/{match_id}.{ext}`
3. Sets `match.processing_status = "processing"` and commits
4. Enqueues `process_match.delay(match_id, academy_id)` via Celery

`tasks/pipeline.py` — Celery task that marks status "done" on completion, "failed" on error.
The `run_pipeline.run()` call inside the task is commented out pending torch installation.

**To start Redis + Celery worker:**
```bash
redis-server &
/opt/anaconda3/bin/celery -A tasks.pipeline.celery_app worker --loglevel=info
```

`ALLOWED_VIDEO_EXTENSIONS` defined in `config/settings.py` — shared by endpoint + task.

### C. Jersey OCR wiring (medium effort)

`detection/ocr.py` has `PaddleOCR` calls but they're not wired into `run_pipeline.py`. After detection (Stage 2), for each bounding box:
```python
from detection.ocr import read_jersey_number
jersey_num = read_jersey_number(frame, bbox)
# Then update the Player record's jersey_number field
```
Confidence threshold: `settings.jersey_ocr_conf = 0.7`

### D. Re-ID upgrade (large effort)

`tracking/tracker.py` uses a HOG-based appearance feature stub. Replace with TransReID or OSNet:
1. Download OSNet weights: `osnet_x1_0_market.pth`
2. Implement `extract_reid_features(crop: np.ndarray) -> np.ndarray` using torchreid
3. Replace the HOG call in `tracker.py` line ~85
4. Tune `settings.reid_threshold = 0.6` (cosine similarity cutoff)

### E. Player profile + heatmap endpoints (small effort)

Two 501 stubs in `api/routers/players.py`:
- `GET /api/v1/players/{id}/profile` — aggregate stats + development trend
- `GET /api/v1/players/{id}/heatmap` — return `heatmap_data` JSON from `player_match_stats`

### F. Alembic migrations (small effort)

Currently using `Base.metadata.create_all()` manually. For production, add:
```bash
pip install alembic
alembic init alembic
# Edit alembic/env.py to import Base from database.models
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### G. Auth (medium effort)

`config/settings.py` has JWT settings (`secret_key`, `algorithm`, `access_token_expire_minutes`). The API has no auth currently — add FastAPI-users or a custom JWT middleware.

---

## 17. Known Issues / Gotchas

| Issue | Location | Notes |
|---|---|---|
| `self._closing_speed` AttributeError | `metrics/pressing.py` | Edge case: track with only 1 frame. Fix: initialise to 0.0 in `__init__` or guard with `len > 1` check |
| HOG re-ID is a stub | `tracking/tracker.py` | Returns random-ish features; re-ID won't be stable across long occlusions until TransReID/OSNet is wired |
| No authentication | `api/` | All endpoints are open. Fine for local dev; add JWT before any public deployment |
| `class Config` deprecation warning | Several Pydantic models in routers | Use `model_config = ConfigDict(from_attributes=True)` instead of inner `class Config`. Not breaking, just noisy |
| Torch not installed in base env | All of `tests/test_detection/` | torch is ~2 GB; install separately in a dedicated conda env if you need to run detection tests |
| `database_url` default is SQLite | `config/settings.py` | Production needs `postgresql+asyncpg://...` in `.env`. SQLite does not support `pgvector` |
| `upload-video` is a 501 | `api/routers/matches.py` | Celery + Redis not yet wired |

---

## 18. Settings Reference (`config/settings.py`)

```python
# All overridable via .env file

# Paths
data_dir        = PROJECT_ROOT / "data"
raw_dir         = PROJECT_ROOT / "data" / "raw"
processed_dir   = PROJECT_ROOT / "data" / "processed"
weights_dir     = PROJECT_ROOT / "data" / "model_weights"

# GPU
cuda_device     = 0
device          = "cuda"     # "cuda" | "cpu" | "mps"

# Detection
yolo_model          = "yolov10x.pt"
yolo_conf_threshold = 0.5
yolo_iou_threshold  = 0.45
sam2_model          = "sam2_hiera_large.pt"
sam2_config         = "sam2_hiera_l.yaml"

# Tracking
max_lost_frames  = 30    # frames before dropping a track
reid_threshold   = 0.6   # cosine similarity cutoff for re-ID
min_track_length = 5     # min frames before a track is confirmed

# Video
default_fps   = 25.0
tactical_fps  = 50.0
frame_width   = 1920
frame_height  = 1080

# Pitch (metres — standard FIFA)
pitch_length  = 105.0
pitch_width   = 68.0

# OCR
jersey_ocr_conf = 0.7

# Database
database_url = "sqlite:///./dev.db"     # override with postgresql+asyncpg://...
redis_url    = "redis://localhost:6379/0"

# API JWT
secret_key                 = "change-me-in-production"
algorithm                  = "HS256"
access_token_expire_minutes = 1440    # 24 hours

# Metrics
press_window_seconds      = 5.0   # window to evaluate press success
press_distance_threshold  = 5.0   # metres — counts as "pressing"
high_intensity_speed      = 5.5   # m/s threshold
sprint_speed              = 7.0   # m/s threshold
```

---

## 19. Quick-start Checklist for CLI

```bash
# 1. Navigate to project
cd /Users/amrabujabal/Downloads/football-ai

# 2. Verify tests are green (94 tests)
/opt/anaconda3/bin/python -m pytest tests/ --ignore=tests/test_detection -q

# 3. Create DB tables
/opt/anaconda3/bin/python -c "
from database.session import engine
from database.models import Base
Base.metadata.create_all(engine)
print('Done')
"

# 4. Start the API
/opt/anaconda3/bin/python -m uvicorn api.main:app --reload
# → http://localhost:8000/docs

# 5. Seed a test academy + match via the API
curl -X POST http://localhost:8000/api/v1/academies/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Al Ain FC","city":"Al Ain","country":"UAE","tier":"pro"}'
# Copy the returned id → ACADEMY_ID

# 6. Start the dashboard
cd dashboard
cp .env.local.example .env.local
# Edit .env.local: set NEXT_PUBLIC_ACADEMY_ID=<ACADEMY_ID from step 5>
npm install && npm run dev
# → http://localhost:3000
```

---

## 20. File Change Log (This Sprint + Priority A sprint)

| File | Status | What changed |
|---|---|---|
| `utils/homography.py` | Created | Full `PitchHomography` class + `draw_pitch()` |
| `tests/test_utils/test_homography.py` | Created | 23 tests (all pass) |
| `database/models.py` | Modified | `UUID(as_uuid=True)` → `Uuid` (cross-DB compatibility) |
| `database/session.py` | Created | `make_engine()`, `SessionLocal`, `get_session()` |
| `database/repository.py` | Created | `PipelineResult`, `PressStatsLike`, `save_pipeline_results()` |
| `tests/test_db/test_repository.py` | Created | 8 tests (all pass) |
| `metrics/physical.py` | Created | `PhysicalMetrics`, `compute_physical_metrics()`, `_count_bouts()` |
| `tests/test_metrics/test_physical.py` | Created | 13 tests (all pass) |
| `config/settings.py` | Modified | `database_url` default → SQLite |
| `scripts/run_pipeline.py` | Modified | Stages 5–6 wired (physical metrics + DB persistence) |
| `api/deps.py` | Created | `get_db()` FastAPI dependency |
| `api/schemas/__init__.py` | Created | 3 Pydantic v2 response schemas |
| `api/routers/matches.py` | Rewritten | `list_matches`, `get_match_summary`, `get_match_players`, `get_processing_status` |
| `api/routers/players.py` | Rewritten | `create_player`, `get_player_stats` |
| `tests/test_api/conftest.py` | Created | `StaticPool` SQLite fixtures |
| `tests/test_api/test_endpoints.py` | Created | 29 tests (all pass) |
| `dashboard/` | Created | Full Next.js 14 app — 3 pages, 6 components, typed API client |

**Priority A — Homography wiring + pressing bug fix (2026-05-24):**

| File | Status | What changed |
|---|---|---|
| `tracking/types.py` | Created | `Track` + `TrackedFrame` dataclasses extracted here (no torch dep) |
| `tracking/tracker.py` | Modified | Imports `Track`/`TrackedFrame` from `tracking.types` instead of defining them |
| `metrics/pitch_control.py` | Modified | Added `homography: Optional[PitchHomography]` param; `get_pitch_pos` uses it |
| `metrics/pressing.py` | Modified | Added `homography` param; `_get_pitch_pos` uses it; removed `self._closing_speed` side-effect |
| `tests/test_metrics/conftest.py` | Created | Shared `identity_homography` + `skewed_homography` fixtures |
| `tests/test_metrics/test_pressing.py` | Created | 10 TDD tests for pressing (bug fixes + homography wiring) |
| `tests/test_metrics/test_pitch_control_homography.py` | Created | 5 TDD tests for pitch_control homography wiring |
| `tests/test_metrics/test_pitch_control.py` | Modified | Import changed to `tracking.types` — now runs without torch |
| `HANDOFF.md` | Modified | Test counts, run commands, backlog updated |

**Priority B — Upload video endpoint (2026-05-24):**

| File | Status | What changed |
|---|---|---|
| `tasks/__init__.py` | Created | Package marker |
| `tasks/pipeline.py` | Created | Celery app + `process_match` task |
| `api/routers/matches.py` | Modified | `upload_video` fully implemented; `_ALLOWED_EXTENSIONS` replaced by shared constant |
| `api/main.py` | Modified | `lifespan` handler creates `raw_dir` at startup |
| `config/settings.py` | Modified | `ALLOWED_VIDEO_EXTENSIONS` frozenset added |
| `tests/test_api/test_upload.py` | Created | 8 TDD tests for the upload endpoint |

**UI/UX Overhaul pass** (applied via UI/UX Pro Max skill — Data-Dense Dashboard design system):

| File | Status | What changed |
|---|---|---|
| `dashboard/package.json` | Modified | Added `lucide-react` for SVG icons |
| `dashboard/tailwind.config.ts` | Rewritten | Fira Code + Fira Sans fonts; navy/amber palette; `home`/`away` color tokens; `card` + `card-hover` shadow scale |
| `dashboard/app/globals.css` | Rewritten | Google Fonts import; full CSS custom-property design token set; `.card`, `.kpi-label`, `.kpi-value`, `.badge-*`, `.team-pill-*`, `.section-title`, `.data-table`, `.skip-link` component classes |
| `dashboard/app/layout.tsx` | Modified | Added `<title>` template; tightened vertical padding |
| `dashboard/components/Nav.tsx` | Rewritten | `⚽` emoji → hand-coded SVG pitch icon; Fira Code brand name; skip-to-main-content link; `sticky top-0 z-40` |
| `dashboard/components/StatusBadge.tsx` | Rewritten | Colored dot + text + ring-1 — three signal channels, not color-only |
| `dashboard/components/MatchCard.tsx` | Rewritten | `card-hover` lift; `<time datetime>` semantic date; `aria-label` on link; Lucide `ChevronRight`; data-dense layout |
| `dashboard/components/PitchControlBar.tsx` | Rewritten | `role="img"` + `aria-label`; colored legend dots; Fira Code percentages inside bar |
| `dashboard/components/PlayerTable.tsx` | Rewritten | `aria-sort` on all `<th>`; Lucide sort icons; Fira Code + `tabular-nums` on all numeric cells; focus rings on player links |
| `dashboard/components/StatsHistoryChart.tsx` | Rewritten | Custom `CustomTooltip`; navy/blue/amber palette; `vertical={false}` grid; `maxBarSize={40}`; Fira Code in axis ticks |
| `dashboard/app/page.tsx` | Rewritten | Stats summary (analysed/processing counts); proper empty state; warning SVG icon |
| `dashboard/app/matches/[id]/page.tsx` | Rewritten | `<nav aria-label="Breadcrumb">`; `KpiCard` sub-component; section labeled with `aria-labelledby` |
| `dashboard/app/players/[id]/page.tsx` | Rewritten | `<nav aria-label="Breadcrumb">`; gradient avatar; `MetricPill` sub-component; all sections `aria-labelledby` |
