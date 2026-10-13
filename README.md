# MedIntel India — Medicine Price Intelligence

An interactive dashboard for understanding Indian medicine prices, comparing products with the same primary active ingredient, and exploring manufacturers and reported interaction flags. Built for **Data Visualization Using Python**, T.Y. B.Tech AIDS, MIT-WPU.

The project combines **React + Vite**, **Recharts**, **FastAPI**, and a live **Supabase PostgreSQL** database. Dashboard results come from raw parameterized SQL, not mock data. The included cleaned dataset contains **6,196 medicines, 789 manufacturers, and 36,800 normalized side-effect records** after loading.

## Explore the application

- **Dashboard:** a compact overview of prices, manufacturers, safety flags, and savings opportunities.
- **Medicine finder:** search products and compare lower-priced records sharing their primary salt.
- **Manufacturers:** product coverage, pricing relative to comparable salts, and recent NSE share prices where available.
- **Savings explorer:** price ranges and lowest-versus-highest price differences within primary salts.
- **Safety signals:** interaction flags, side-effect counts, and relationships with price.
- **Insights:** a chart-by-chart walkthrough explaining findings and limitations.
- **EDA report:** the supplied preprocessing findings and original static charts.
- **SQL transparency:** the actual documented SQL that powers the application.

## Repository layout

```text
backend/
  main.py                 FastAPI endpoints
  db.py                   Supabase PostgreSQL connection pool
  queries.py              Central SQL registry: schema, loading, and analytics
  load_data.py            CSV loader and side-effect normalization
  stock.py                yfinance integration and quote cache
  tests/                  SQL registry checks
  requirements.txt        Python dependencies
  .env.example            Safe configuration template
frontend/
  src/pages/              Dashboard and exploration pages
  src/components/         Shared charts and UI components
  public/charts/          EDA images served by the report page
  public/                 Logo and hero artwork
  package-lock.json       Reproducible npm dependencies
data/
  medicine_data_cleaned.csv
  insights_summary.txt
  charts/                 All 12 supplied EDA PNGs
docs/plans/               Design and implementation notes
```

The original separate `medicine_project/` folder's CSV, insights summary, and 12 charts are consolidated under `data/`. Browser-served chart copies remain under `frontend/public/charts/`. No original Colab notebook or raw-data preprocessing script was supplied in the local project; this repository includes the supplied EDA outputs and the Python database-loading/analysis implementation.

## Prerequisites

- Python **3.11 or later**.
- Node.js **22.12 or later**, with npm.
- Git and a running Supabase project with its PostgreSQL connection string.
- Internet connectivity for Supabase and Yahoo Finance stock quotes.

## 1. Clone and install

```bash
git clone https://github.com/SokandeSujal/medicine-price-intelligence.git
cd medicine-price-intelligence
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install backend dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

If PowerShell prevents activation, run `.\.venv\Scripts\python.exe` instead of `python` in the commands below. No activation is required when invoking that executable directly.

## 2. Configure Supabase

Create a Supabase project, or resume your existing one, then open its **Connect** panel. Copy the **Session pooler** PostgreSQL URI. This supports IPv4 networks; the direct database host may require IPv6. Use the host and region shown for your own project.

Copy the backend template:

```powershell
Copy-Item backend/.env.example backend/.env
```

On macOS/Linux, use `cp backend/.env.example backend/.env`.

Set this value in `backend/.env`:

```dotenv
DATABASE_URL=postgresql://postgres.PROJECT_REF:URL_ENCODED_PASSWORD@YOUR_SESSION_POOLER_HOST:5432/postgres?sslmode=require
```

Replace every placeholder with the values from your project. Password characters such as `@`, `#`, `/`, and `%` must be percent-encoded when included in a URI. Use the **database password**, not an anon key or service-role key.

The backend uses PostgreSQL directly, so `DATABASE_URL` is the only required database setting. The optional Supabase URL/key fields in the template are not required for this implementation. Keep credentials in `backend/.env`; it is excluded from Git. Never put database credentials or service-role keys in frontend variables.

## 3. Create tables and load the included data

From the repository root, with the Python environment active:

```bash
python -m backend.load_data
```

The loader creates `manufacturers`, `medicines`, and `side_effects`, calculates manufacturer price statistics, inserts the cleaned records, and splits side effects into separate linked rows. All SQL lives in `backend/queries.py`.

If this database has already been loaded, the loader refuses to insert duplicates. Skip loading and run the app against those existing tables. For an intentional replacement of **all data in these three project tables**, use:

```bash
python -m backend.load_data --replace
```

Other options:

```bash
python -m backend.load_data --schema-only
python -m backend.load_data --csv /path/to/medicine_data_cleaned.csv
```

## 4. Start the backend

From the repository root:

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- API documentation: <http://127.0.0.1:8000/docs>
- Database health: <http://127.0.0.1:8000/api/health>
- Overview data: <http://127.0.0.1:8000/api/overview>
- SQL registry/source: <http://127.0.0.1:8000/api/debug/queries>

The health response should contain `"status": "ok"` and `"rows": 6196` for the included dataset. Check the response body: an HTTP response alone does not confirm database connectivity.

## 5. Start the frontend

Open a second terminal at the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open **<http://localhost:5173>**. Vite proxies `/api` calls to port 8000, so no frontend environment file is required for local development. Keep both terminals running; press Ctrl+C in each to stop.

For an API hosted separately, copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_URL` to the API origin, without `/api` or a trailing slash. Restart Vite after editing it. Update the backend CORS origins for the deployed frontend. The production build does not include Vite's development proxy.

## Build and verification

From the repository root:

```bash
python -m pytest backend/tests -q
```

The included tests check the SQL registry; they do not replace a live Supabase connectivity check.

From `frontend/`:

```bash
npm run build
```

This generates `frontend/dist/`. To preview it locally with a running backend, set `VITE_API_URL=http://127.0.0.1:8000` before building and run `npm run preview -- --port 5173`; port 5173 is allowed by the current backend CORS configuration.

## Database work and live quotes

`backend/queries.py` is the single source of SQL for schema creation, loading, and API analytics. Its documented registry demonstrates JOINs, GROUP BY/HAVING, CTEs, subqueries, percentiles, and window functions. The SQL Transparency page and `/api/debug/queries` expose this work for evaluation. Side effects form a one-to-many relationship with medicine records.

Stock quotes use `yfinance` for supported listed manufacturers, including Sun Pharma, Cipla, Dr Reddy's, and Glenmark. No API key is required. Quotes may be delayed, unavailable, or rate-limited; the backend uses an in-memory cache and exposes unavailable/stale states. These are recent market quotes, not guaranteed real-time trading prices.

## Data and EDA provenance

Source: [Indian Medicine Data by mohneesh7 on Kaggle](https://www.kaggle.com/datasets/mohneesh7/indian-medicine-data). The supplied Colab outputs are preserved in `data/insights_summary.txt` and `data/charts/`, covering missing values, price distribution, manufacturer counts/prices, categories, salt price ranges, savings differences, ingredient/side-effect relationships, interaction flags, and a correlation heatmap.

The original summary reports 195,605 raw rows reduced to 6,196 cleaned, deduplicated records. It also reports some preprocessing-stage counts, such as 7,914 outliers, that exceed the final dataset size; read those as historical preprocessing notes, not final-table counts. Live dashboard metrics are calculated from the loaded CSV.

Prices are a dataset snapshot, with no date field for a time trend. Records sharing a primary salt may differ in full composition, dose, formulation, pack size, and clinical suitability. Displayed price differences are comparisons, not validated interchangeable prescriptions. Interaction flags reflect dataset descriptions rather than individualized clinical risk. Stock valuation and medicine pricing are independent signals, with no causal claim.

## Troubleshooting

- **Data connection unavailable:** confirm Supabase is resumed, the connection URI is correct, and loading has completed. The backend retries failed pool initialization; restart it after changing `.env`.
- **`getaddrinfo failed` or direct-host connection errors:** copy your project's IPv4-compatible Session pooler URI from Supabase. Do not guess its region or host.
- **Authentication failed:** verify the database password and URI encoding. An anon/service-role JWT cannot authenticate a PostgreSQL connection.
- **Frontend opens but requests fail:** verify the backend is running on port 8000, and inspect `/api/health` and `/docs`.
- **Port already in use:** stop the previous server or configure another port; adjust Vite's proxy and backend CORS accordingly.
- **Stocks unavailable:** Yahoo Finance may throttle requests. The rest of the dashboard uses Supabase independently.

This repository includes source, cleaned data, and EDA artifacts. Local secrets, virtual environments, npm dependencies, browser profiles, logs, and build output are intentionally excluded.
