# Indian Medicine Price Intelligence — Design

## Architecture

The application is a React/Vite single-page dashboard backed by FastAPI and a Supabase-hosted PostgreSQL database. All application SQL—including schema creation, loading, and analytical queries—lives in `backend/queries.py`. Route handlers select named queries and never embed SQL.

## Data flow

The idempotent loader reads the cleaned CSV, derives manufacturer aggregates, inserts normalized medicines, and comma-splits side effects into a child table. FastAPI executes the named SQL directly against Supabase Postgres. The React client uses the API for every metric and chart. Stock quotes are the sole external dataset and are cached server-side using yfinance.

## Experience

The interface uses a refined clinical-editorial direction: warm white surfaces, deep ink typography, emerald/teal accents, compact contextual annotations, generous whitespace, and subtle staged motion. A persistent desktop rail becomes a compact mobile header. SQL transparency is available both per analytical page and on a dedicated page.

## Reliability

Database failures produce explicit 503 responses and visible frontend recovery states. Stock failures never break manufacturer analytics. Loader transactions roll back on failure. Backend tests validate route/query contracts, and the frontend must pass its production build.
