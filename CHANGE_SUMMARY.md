# Urban Data Explorer - Interactive Map Change Summary

This document summarizes the interactive map work added to the Urban Data Explorer project, including the backend map endpoint, the new Next.js frontend, setup requirements, and how to navigate the map.

## Goal

The objective was to start the interactive cartographic dashboard requested by the Urban Data Explorer brief. The first implemented map layer focuses on the `vivabilite_familiale` indicator, displayed at Paris IRIS level as a choropleth map.

The map is built with:

- FastAPI for the backend API.
- Next.js App Router for the frontend.
- TypeScript for typed frontend code.
- Tailwind CSS for responsive styling.
- Mapbox GL through `react-map-gl` for the interactive map.

## Current Refinement: Main Indicators + Sub-Indicators

The dashboard now follows a two-level indicator model:

- **Main indicators**: `Vivabilité familiale`, `Transport`, `Confort thermique`, and `Logement`.
- **Sub-indicators**: the measurable pieces inside each main indicator.

This replaces the earlier flat UI where `Family mix`, `Schools`, `Transport`, and other pillars appeared at the same level.

### Current Main Indicator Model

| Main indicator | Geography | Main score | Sub-indicators / fields |
| --- | --- | --- | --- |
| `Vivabilité familiale` | IRIS | `vivabilite_score` | `school_score`, `childcare_score`, `safety_score`, `healthcare_score`, `environment_score`, `green_spaces_score`, `transport_score`, `daily_services_score`, plus custom `Family mix` weights |
| `Transport` | IRIS + point overlay | `transport_score` | Transport accessibility choropleth plus filters for métro, rail/RER, tram, bus, and Vélib points |
| `Confort thermique` | IRIS | `thermal_score` | `tree_density_score`, `cooling_area_score`, plus raw `densite_arbres` and `ratio_fraicheur` |
| `Logement` | Arrondissement | affordability score | `rent_score` from median rent €/m² and `sale_score` from latest median sale price €/m² |

### New Backend Map Routes

The map API now exposes multiple map-ready GeoJSON layers:

```http
GET /map/vivabilite-familiale
GET /map/thermal-comfort
GET /map/housing/rent
GET /map/housing/sale
```

`/map/vivabilite-familiale`, `/map/thermal-comfort`, and `/map/transport`-related scoring are IRIS-level. Housing layers are arrondissement-level because the current rent and sale Gold outputs are aggregated to arrondissement polygons.

### New Gold Data Loaded By The API

The API `DataStore` now loads:

- `data/gold/vivabilite_familiale_iris.csv`
- `data/gold/transport_indicator_iris.csv`
- `data/gold/transport_points.csv`
- `data/gold/urban_comfort_index.parquet`
- `data/gold/rent_data_par_arrdt.parquet`
- `data/gold/sale_price_median.parquet`

The frontend fetches the new layers lazily when a user selects the relevant main indicator.

### Dependency Notes

The pipeline now needs these dependencies in addition to the original stack:

- `xlrd` for legacy `.xls` rent-zone mapping files.
- `pdfplumber` for sale-price PDF extraction.
- `pyarrow` for Parquet Gold outputs.
- `pytest` and `httpx` for map endpoint tests.

## Backend Changes

### GeoJSON Data Loading

Updated `api/services/data_loader.py` so the API startup `DataStore` also loads IRIS geometry from:

```text
data/bronze/main_data/iris.geojson
```

The loaded geometry is stored as:

```python
DataStore.iris_geojson
```

This makes the geometry available to API services without re-reading the file for every request.

### Map Service

Added `api/services/map_service.py`.

This service builds a map-ready GeoJSON layer by joining:

- IRIS polygon geometries from `iris.geojson`.
- Family liveability scores from `store.vivabilite_scores`.

The join key is:

```text
code_iris / IRIS
```

Each returned GeoJSON feature includes these properties:

- `code_iris`
- `name`
- `arrondissement`
- `quarter_code`
- `population`
- `school_score`
- `transport_score`
- `services_score`
- `green_spaces_score`
- `vivabilite_score`
- `vivabilite_rank`

The service also returns clear errors when required data is missing:

- Missing IRIS geometry.
- Missing `vivabilite_familiale_iris.csv`.
- No matching IRIS zones between geometry and scores.

### Map Router

Added `api/routers/map.py` with this endpoint:

```http
GET /map/vivabilite-familiale
```

The endpoint returns a GeoJSON `FeatureCollection` for direct use by the frontend map.

If the map data is not ready, it returns a `503` response with a useful error message instead of silently failing.

### API Registration

Updated `api/main.py` to register the new router:

```text
/map
```

The new route is now available alongside the existing API routes for IRIS, population, schools, transport, and indicators.

## Frontend Changes

### New Next.js App

Created a new frontend project in:

```text
web/
```

The app uses:

- Next.js App Router.
- TypeScript.
- Tailwind CSS.
- ESLint.
- `react-map-gl`.
- `mapbox-gl`.

### Frontend API Client

Added `web/src/lib/api.ts`.

This file centralizes communication with the FastAPI backend. It reads:

```text
NEXT_PUBLIC_API_URL
```

and fetches:

```http
/map/vivabilite-familiale
```

It also extracts backend error messages so the UI can explain what is wrong when the API or data is unavailable.

### GeoJSON Types

Added `web/src/types/map.ts`.

This file defines TypeScript types for the vivability map data:

- `VivabiliteProperties`
- `VivabiliteFeature`
- `VivabiliteFeatureCollection`

These types make the map UI safer and clearer when accessing score, rank, population, and IRIS metadata.

### Interactive Map Dashboard

Added `web/src/components/MapDashboard.tsx`.

This is the main map experience. It includes:

- Full-screen map centered on Paris.
- IRIS choropleth layer colored by `vivabilite_score`.
- Red-to-green color scale from low score to high score.
- Hover cursor and active IRIS outline.
- Click selection.
- Popup on selected IRIS zone.
- Responsive detail panel.
- Score legend.
- Loading state.
- Error state when the API or Gold data is missing.

### Home Page

Updated `web/src/app/page.tsx` to render the new `MapDashboard` instead of the default Next.js starter page.

### Global Styling

Updated `web/src/app/globals.css` to:

- Import Tailwind.
- Import Mapbox GL CSS.
- Style Mapbox popups.
- Use the project font variables.

### Metadata

Updated `web/src/app/layout.tsx` with Urban Data Explorer metadata.

### Frontend Environment Example

Added `web/.env.example`:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_MAPBOX_TOKEN=
```

`NEXT_PUBLIC_MAPBOX_TOKEN` can be filled with a Mapbox token. If it is empty, the map falls back to a public Mapbox-compatible basemap style.

### Next.js Build Config

Updated `web/next.config.ts` to set the Turbopack root to the `web/` app directory. This removes the workspace-root warning caused by multiple lockfiles elsewhere on the machine.

## Documentation Changes

Updated `README.md` with:

- The new map endpoint.
- How to run the interactive map frontend.
- Required frontend environment variables.
- The backend command to start the API.
- The pipeline command needed to generate the Gold vivability CSV.

## How To Run The Map

### 1. Generate The Gold Indicator Data

From the project root:

```bash
python run_pipeline.py --gold
```

The map needs this file:

```text
data/gold/vivabilite_familiale_iris.csv
```

If this file is missing, the frontend will show a clear "Map data unavailable" message.

### 2. Start The FastAPI Backend

Use the project virtual environment:

```bash
.venv/Scripts/uvicorn api.main:app --reload
```

The backend should run at:

```text
http://127.0.0.1:8000
```

You can test the new map endpoint directly here:

```text
http://127.0.0.1:8000/map/vivabilite-familiale
```

### 3. Configure The Frontend

From the `web/` folder:

```bash
cp .env.example .env.local
```

Then edit `web/.env.local`:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here
```

The Mapbox token is recommended. Without it, the app uses a public fallback basemap style.

### 4. Start The Next.js Frontend

From the `web/` folder:

```bash
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## How To Navigate The Map

### Basic Navigation

- Drag the map to pan around Paris.
- Scroll with the mouse wheel or pinch on a trackpad to zoom.
- On mobile, drag with one finger to move and pinch with two fingers to zoom.

### Reading The Colors

The map uses a choropleth color scale based on `vivabilite_score`:

- Red means lower family liveability.
- Orange/yellow means medium score.
- Green means higher family liveability.

The legend shows the score scale from `0` to `10`.

### Hovering An IRIS Zone

Move the mouse over a colored IRIS polygon.

The hovered area gets an outline so you can see which zone is active.

### Selecting An IRIS Zone

Click an IRIS polygon to select it.

After selection:

- A popup appears on the map.
- The detail panel updates with that IRIS zone.
- The selected polygon keeps a stronger outline.

### Detail Panel

The detail panel shows:

- IRIS name.
- Arrondissement.
- Composite family liveability score.
- Paris-wide rank.
- Population.
- IRIS code.
- School score.
- Transport score.
- Services score.
- Green spaces score.

On desktop, the panel appears as a card near the bottom/right of the map.

On smaller screens, it behaves like a mobile-friendly bottom panel.

### Clearing A Selection

Click the `Close` button in the detail panel to return to the overview state.

When no IRIS is selected, the panel shows a Paris overview based on loaded map data.

### Error Overlay

If the frontend cannot load data, an error overlay appears.

Common reasons:

- The FastAPI backend is not running.
- `NEXT_PUBLIC_API_URL` is incorrect.
- `data/gold/vivabilite_familiale_iris.csv` has not been generated.
- The pipeline has not been run.

The overlay includes the commands needed to regenerate data and start the API.

## Validation Performed

The following checks passed after implementation:

```bash
python -m compileall api
npm run lint
npm run build
```

The backend data smoke test confirmed:

- IRIS geometry loads correctly.
- Missing Gold vivability data is reported clearly.

At the time of testing, `data/gold/vivabilite_familiale_iris.csv` was missing locally, so the map endpoint correctly returned a data-unavailable message until the Gold pipeline is run.

## Files Added Or Updated

### Backend

- `api/services/data_loader.py`
- `api/services/map_service.py`
- `api/routers/map.py`
- `api/main.py`

### Frontend

- `web/package.json`
- `web/package-lock.json`
- `web/.env.example`
- `web/next.config.ts`
- `web/src/app/page.tsx`
- `web/src/app/layout.tsx`
- `web/src/app/globals.css`
- `web/src/components/MapDashboard.tsx`
- `web/src/lib/api.ts`
- `web/src/types/map.ts`

### Documentation

- `README.md`
- `CHANGE_SUMMARY.md`

## Current Status

The first interactive map foundation is implemented. It is ready to display the `vivabilite_familiale` IRIS choropleth once the Gold indicator CSV exists locally and the API is running.

Next useful improvements would be:

- Add score and arrondissement filters.
- Add search by IRIS name or arrondissement.
- Add additional indicators as selectable map layers.
- Add a side ranking list.
- Add tests for the map GeoJSON endpoint.
