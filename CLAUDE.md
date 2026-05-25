# Football Player Identification System

## Project Overview
Computer vision pipeline to detect, track, and analytically profile football players on a pitch.
Target market: UAE football academies (Al Ain, Al Jazira, Shabab Al Ahli feeders + private academies).

## Business Goal
Sell proprietary player profile data and a club dashboard to academies that can't afford Opta/StatsBomb.
Bilingual product: Arabic + English UI.

## Stack
- Python 3.11
- SAM 2 (Meta) — segmentation
- YOLOv10 — player detection
- TransReID / OSNet — player re-identification across frames
- PaddleOCR — jersey number recognition
- FastAPI — REST API backend
- PostgreSQL + pgvector — player database with vector embeddings
- Celery + Redis — async video processing queue
- Next.js — club dashboard frontend

## Module Map
- /detection        → YOLO + SAM 2 pipeline (frame-level player detection + segmentation)
- /tracking         → Re-ID, multi-object tracking, trajectory storage
- /metrics          → All advanced metric computation (pitch control, xT, press metrics, etc.)
- /api              → FastAPI routers, schemas, auth
- /database         → SQLAlchemy models, Alembic migrations
- /dashboard        → Next.js frontend (separate repo, referenced here)
- /models           → Pydantic data models
- /utils            → Video I/O, coordinate transforms, visualization helpers
- /scripts          → One-off scripts: model downloads, dataset prep, batch processing
- /data             → Raw footage, processed clips, model weights (gitignored)
- /tests            → Pytest test suite

## Key Conventions
- All coordinates are normalized [0,1] relative to pitch dimensions unless stated otherwise
- Pitch reference frame: origin bottom-left, x = width, y = length
- Player IDs are persistent across a match session; re-assigned each new match
- All metric outputs include a `confidence` float [0,1]
- Frame rate assumption: 25fps (broadcast); 50fps (tactical cam) — configure per source

## Environment
- Use conda env: `conda activate football-ai`
- GPU: configure in config/settings.py (CUDA device index)
- Model weights stored in /data/model_weights/ (not committed to git)

## Completed
- Detection pipeline (YOLO + SAM 2)
- Jersey OCR + team color classification
- Physical metrics (distance, speed, sprints, hi-intensity runs)
- Pitch control (Voronoi-based)
- Pressing analysis (press count, success rate, trigger accuracy)
- DevelopmentScore auto-computed per player per week after each match
- Database schema + Alembic migrations
- FastAPI REST API with JWT auth
- Video upload endpoint → Celery async pipeline
- Next.js dashboard (match list, match detail, player profile)

## Current Priority
Player performance prediction model:
1. Add position + date_of_birth to Player model (Alembic migration)
2. Feature assembly script (rolling match history → training rows)
3. Train scikit-learn model per position group
4. GET /api/v1/players/{id}/prediction endpoint
5. Dashboard prediction widget

## Backlog
- Heatmap grid written by pipeline (endpoint exists, data not yet computed)
- Re-ID across occlusions (TransReID/OSNet — needs torch)
- PostgreSQL + pgvector for production
- Arabic UI (name_ar fields in schema already)

## Do Not
- Commit model weights or raw footage to git
- Use absolute paths — always use pathlib relative to PROJECT_ROOT
- Skip type hints — all functions must be typed
