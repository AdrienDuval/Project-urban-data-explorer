# Data Architecture — Urban Data Explorer

Covers the full Bronze → Silver → Gold pipeline for two indicators:
- **Vivabilité Familiale** (Family Liveability Index)
- **Prix du Logement** (Housing Prices — DVF + rent)

---

## 1. Overview

The pipeline follows a three-layer data lake pattern.

```
Bronze  →  Silver  →  Gold  →  DB / API
(raw)      (clean)    (scored)
```

| Layer  | Location           | Format                     | Description                                  |
|--------|--------------------|----------------------------|----------------------------------------------|
| Bronze | `data/bronze/`     | xlsx, csv, geojson, txt    | Raw files downloaded from Google Drive       |
| Silver | `data/silver/`     | CSV, GeoJSON               | Cleaned, filtered, deduplicated              |
| Gold   | `data/gold/`       | CSV, Parquet               | Scored indicators, 0–10 scale, per IRIS zone |
| DB     | MySQL              | Tables                     | Written via SQLAlchemy for API consumption   |

**Entry point:** [run_pipeline.py](run_pipeline.py)  
**Config constants:** [src/config.py](src/config.py)

---

## 2. Spatial Reference & IRIS Zones

All indicators are aggregated at the **IRIS** level (Institut National de la Statistique — finest French statistical unit, roughly 2,000 residents each).

### IRIS Master Files

| Step   | File                                             | Script                    |
|--------|--------------------------------------------------|---------------------------|
| Bronze | `data/bronze/main_data/iris.xlsx`                | —                         |
| Bronze | `data/bronze/main_data/iris.geojson`             | —                         |
| Silver | `data/silver/iris_paris.csv`                     | [src/silver/iris.py](src/silver/iris.py) |

**Silver columns:**

| Column      | Type   | Description                                     |
|-------------|--------|-------------------------------------------------|
| `CODE_IRIS` | string | 9-digit INSEE IRIS code (zero-padded), join key |
| `NOM_COM`   | string | Municipality name                               |
| `NOM_IRIS`  | string | IRIS zone name                                  |
| `IRIS`      | string | Short IRIS reference code                       |
| `GRD_QUART` | string | Broad neighbourhood name                        |
| `Geo Point` | string | `"lat, lng"` centroid string (WGS84)            |

**Filter:** `DEP == 75` (Paris only).

### Coordinate Reference Systems

| Data source         | Native CRS           | Used as              |
|---------------------|----------------------|----------------------|
| IRIS GeoJSON        | EPSG:4326 (WGS84)    | Reprojected to 2154 for buffering |
| BDCOM establishments | EPSG:2154 (Lambert-93) | Used directly       |
| Schools / hospitals / transport | WGS84 lat/lng | Converted to GeoDataFrame → 2154 |
| Green spaces        | EPSG:4326 GeoJSON    | Reprojected to 2154  |

**Spatial join strategy:** A **500 m buffer** is drawn around each IRIS zone polygon (EPSG:2154). Points of interest within the buffer are assigned to that IRIS. Green spaces use a **300 m adjacency** buffer with a 0.5× weight bonus for spaces touching but not inside the zone.

### Population Reference

| Step   | File                                                       | Script                          |
|--------|------------------------------------------------------------|---------------------------------|
| Bronze | `data/bronze/main_data/base-ic-evol-struct-pop-2022.CSV`  | —                               |
| Silver | `data/silver/population_paris.csv`                        | [src/silver/population.py](src/silver/population.py) |

**Silver columns:** `IRIS`, `LAB_IRIS`, `population`  
**Filter:** `COM.startswith("75")`, `TYP_IRIS == "H"` (residential zones only).

---

## 3. Vivabilité Familiale

### 3.1 Composite Score Formula

```
vivabilite_score = 0.20 × school_score
                 + 0.20 × healthcare_score
                 + 0.20 × transport_score
                 + 0.20 × daily_services_score
                 + 0.20 × green_spaces_score
```

All sub-scores are on a **0–10** scale. Missing IRIS values are filled with the **median** of the column.

**Gold output:** [data/gold/vivabilite_familiale_iris.csv](data/gold/vivabilite_familiale_iris.csv)  
**DB table:** `vivabilite_familiale`  
**Script:** [src/gold/vivabilite_familiale.py](src/gold/vivabilite_familiale.py)

### 3.2 Gold Table Schema — `vivabilite_familiale`

| Column                  | Type    | Description                                              |
|-------------------------|---------|----------------------------------------------------------|
| `IRIS`                  | string  | 9-digit IRIS code — primary join key                     |
| `LIBCOM`                | string  | Municipality label                                       |
| `LIBIRIS`               | string  | IRIS zone label                                          |
| `GRD_QUART`             | string  | Neighbourhood name                                       |
| `population`            | int     | Resident count (from INSEE 2022)                         |
| `code_iris`             | string  | Alias for IRIS code                                      |
| `school_score`          | float   | Schools sub-score 0–10                                   |
| `healthcare_score`      | float   | Healthcare sub-score 0–10                                |
| `transport_score`       | float   | Transport sub-score 0–10                                 |
| `daily_services_score`  | float   | Daily services sub-score 0–10                            |
| `green_spaces_score`    | float   | Green spaces sub-score 0–10                              |
| `vivabilite_score`      | float   | Composite score 0–10                                     |
| `vivabilite_rank`       | int     | Rank among all Paris IRIS zones (1 = best)               |
| `vivabilite_model`      | string  | Model version tag                                        |
| `vivabilite_weights`    | json    | Dict of pillar weights used in computation               |

---

### 3.3 Pillar 1 — Schools (`school_score`)

**Script:** [src/gold/school_density.py](src/gold/school_density.py)  
**Gold output:** [data/gold/schools_score_iris.csv](data/gold/schools_score_iris.csv)  
**DB table:** `school_density`

#### Bronze → Silver

| Step   | File                                                                  | Script                        |
|--------|-----------------------------------------------------------------------|-------------------------------|
| Bronze | `data/bronze/indice_vivabilite_familiale/etablissements-scolaires-colleges.xlsx` | — |
| Bronze | `data/bronze/indice_vivabilite_familiale/etablissements-scolaires-ecoles-elementaires.xlsx` | — |
| Bronze | `data/bronze/indice_vivabilite_familiale/etablissements-scolaires-maternelles.xlsx` | — |
| Silver | `data/silver/schools_merged.csv`                                      | [src/silver/schools.py](src/silver/schools.py) |

**Silver columns:** `name`, `address`, `arrondissement`, `type` (Collège / Maternelle / Élémentaire / Polyvalent), `lat`, `lng`  
**Deduplication:** by `(name, address)`, keeping the most recent year.

#### Silver → Gold

1. Schools (points) are spatially joined to IRIS zones using a 500 m buffer.
2. `school_count` = number of schools within the buffer.
3. `schools_per_1000` = `school_count / population × 1000`.
4. `school_score` = min-max normalized to 0–10.

**Gold columns:**

| Column              | Description                          |
|---------------------|--------------------------------------|
| `IRIS`              | 9-digit IRIS join key                |
| `school_count`      | Schools within 500 m buffer          |
| `schools_per_1000`  | Schools per 1,000 residents          |
| `school_score`      | Normalized score 0–10                |

---

### 3.4 Pillar 2 — Healthcare (`healthcare_score`)

**Script:** [src/gold/family_support_scores.py](src/gold/family_support_scores.py) → `compute_healthcare_score()`  
**Gold output:** [data/gold/healthcare_score_iris.csv](data/gold/healthcare_score_iris.csv)  
**DB table:** `healthcare_score`

#### Sources

| Step   | File                                                                         | Script                          |
|--------|------------------------------------------------------------------------------|---------------------------------|
| Bronze | `data/bronze/public_service_data/les_etablissements_hospitaliers_franciliens.csv` | — |
| Bronze | `data/bronze/public_service_data/BDCOM_2023.csv`                            | — |
| Silver | `data/silver/hospitals_paris_clean.csv`                                     | [src/silver/hospitals.py](src/silver/hospitals.py) |
| Silver | `data/silver/bdcom_paris_clean.csv`                                         | [src/silver/bdcom.py](src/silver/bdcom.py) |

**Hospital silver columns:** `lat`, `lng`, `raison_sociale`, `finess_et` (unique ID), `dept`, `is_public_service`, `has_coordinates`  
**Deduplication:** by `finess_et`. **Validation:** lat ∈ [48.1, 49.3], lng ∈ [1.4, 3.6].

**BDCOM healthcare filter:** `niv47` label contains `pharmacie|médic|opticien` OR `niv18` label contains `santé`.

#### Silver → Gold

1. Hospitals and BDCOM healthcare points joined to IRIS (500 m buffer).
2. `hospital_count` + `healthcare_service_count` (from BDCOM).
3. `weighted_healthcare_access` = hospitals weighted higher than pharmacy points.
4. Min-max normalized to `healthcare_score` 0–10.

**Gold columns:**

| Column                      | Description                              |
|-----------------------------|------------------------------------------|
| `IRIS`                      | 9-digit join key                         |
| `hospital_count`            | Hospitals/clinics within buffer          |
| `healthcare_service_count`  | BDCOM healthcare establishments          |
| `weighted_healthcare_access`| Weighted combined count                  |
| `healthcare_score`          | Score 0–10                               |

---

### 3.5 Pillar 3 — Transport (`transport_score`)

**Script:** [src/gold/transport_score.py](src/gold/transport_score.py)  
**Gold outputs:** [data/gold/transport_score_iris.csv](data/gold/transport_score_iris.csv), [data/gold/transport_indicator_iris.csv](data/gold/transport_indicator_iris.csv)  
**DB tables:** `transport_score`, `transport_score_iris`

#### Sources

| Step   | File                                     | Script                            |
|--------|------------------------------------------|-----------------------------------|
| Bronze | `data/bronze/transport_data/arrets.csv`  | —                                 |
| Bronze | `data/bronze/transport_data/velib.csv`   | —                                 |
| Silver | `data/silver/transport_arrets_paris.csv` | [src/silver/transport.py](src/silver/transport.py) |
| Silver | `data/silver/velib_paris.csv`            | [src/silver/transport.py](src/silver/transport.py) |

**Silver columns (stops):** `id`, `name`, `type` (metro / rail / tram / bus / cableway), `lat`, `lng`, `postal_region`  
**Silver columns (vélib):** `id`, `name`, `type` = `"velib"`, `lat`, `lng`

#### Transport Weights (from `src/config.py`)

| Mode       | Weight |
|------------|--------|
| `metro`    | 1.0    |
| `rail`     | 1.2    |
| `tram`     | 0.7    |
| `bus`      | 0.4    |
| `cableway` | 0.5    |
| `velib`    | 0.3    |

#### Silver → Gold

1. All stops joined to IRIS (500 m buffer).
2. `stop_count` = raw count; `weighted_stops` = sum of mode weights.
3. Normalized to `transport_score` 0–10.
4. A second indicator (`transport_indicator_iris.csv`) computes density + proximity sub-scores on 0–1 scale.

**Gold columns (transport_score_iris.csv):**

| Column            | Description                                    |
|-------------------|------------------------------------------------|
| `IRIS`            | 9-digit join key                               |
| `stop_count`      | Total stops within buffer                      |
| `weighted_stops`  | Mode-weighted sum                              |
| `transport_score` | Score 0–10                                     |

**Gold columns (transport_indicator_iris.csv):**

| Column            | Description                   |
|-------------------|-------------------------------|
| `CODE_IRIS`       | 9-digit join key               |
| `density_score`   | Stop density 0–1              |
| `proximity_score` | Nearest-stop proximity 0–1    |
| `transport_score` | Combined 0–1                  |

---

### 3.6 Pillar 4 — Daily Services (`daily_services_score`)

**Script:** [src/gold/family_support_scores.py](src/gold/family_support_scores.py) → `compute_daily_services_score()`  
**Gold output:** [data/gold/daily_services_score_iris.csv](data/gold/daily_services_score_iris.csv)  
**DB table:** `daily_services_score`

#### Source

| Step   | File                                           | Script                    |
|--------|------------------------------------------------|---------------------------|
| Bronze | `data/bronze/public_service_data/BDCOM_2023.csv` | —                       |
| Silver | `data/silver/bdcom_paris_clean.csv`            | [src/silver/bdcom.py](src/silver/bdcom.py) |

**BDCOM daily services filter:** `niv8` ∈ `{2 (Alimentaire), 4 (Service commercial)}` + family amenities (post office, library, sports, leisure).

#### BDCOM Hierarchy

BDCOM encodes each establishment at four activity levels:

| Column  | Levels | Example                     |
|---------|--------|-----------------------------|
| `niv2`  | 2      | Commerce / Service          |
| `niv8`  | 8      | Alimentaire, Santé, …       |
| `niv18` | 18     | Pharmacies, Supermarkets, … |
| `niv47` | 47     | Pharmacies (detail), …      |

Key spatial columns: `X`, `Y` (EPSG:2154 Lambert-93).

#### Silver → Gold

1. BDCOM daily-service points joined to IRIS (500 m buffer).
2. `daily_service_count` + `weighted_daily_service_count` (weights vary by niv8 category).
3. Normalized to `daily_services_score` 0–10.

**Gold columns:**

| Column                       | Description                            |
|------------------------------|----------------------------------------|
| `IRIS`                       | 9-digit join key                       |
| `daily_service_count`        | Raw count within buffer                |
| `weighted_daily_service_count` | Category-weighted count             |
| `daily_services_score`       | Score 0–10                             |

---

### 3.7 Pillar 5 — Green Spaces (`green_spaces_score`)

**Script:** [src/gold/green_spaces_score.py](src/gold/green_spaces_score.py)  
**Gold output:** [data/gold/green_spaces_score_iris.csv](data/gold/green_spaces_score_iris.csv)  
**DB table (merged into vivabilite):** inline join

#### Sources

| Step   | File                                                                | Script                            |
|--------|---------------------------------------------------------------------|-----------------------------------|
| Bronze | `data/bronze/indice_vivabilite_familiale/espaces_verts.geojson`     | —                                 |
| Silver | `data/silver/espaces_verts_paris.geojson`                           | [src/silver/green_spaces.py](src/silver/green_spaces.py) |

**Silver geometry:** Polygon (EPSG:4326 → 2154). **Filter:** `ouvert_ferme == "Ouvert"` (open to public), excludes decorative planters. Missing `surface_totale_reelle` filled from reprojected polygon area.

**Key silver columns:** `geometry`, `surface_totale_reelle` (m²), `type_ev`, `ouvert_ferme`

#### Silver → Gold

1. Green space polygons intersected with IRIS polygons (reprojected to EPSG:2154).
2. `interior_m2` = area of green spaces whose centroid is **inside** the IRIS zone.
3. `adjacent_m2` = area of green spaces within 300 m buffer but outside zone (weighted at 0.5×).
4. `total_green_m2 = interior_m2 + 0.5 × adjacent_m2`.
5. `green_m2_per_resident = total_green_m2 / population`.
6. Normalized to `green_spaces_score` 0–10.

**Gold columns:**

| Column                 | Description                                     |
|------------------------|-------------------------------------------------|
| `IRIS`                 | 9-digit join key                                |
| `interior_m2`          | Green space m² inside IRIS                      |
| `adjacent_m2`          | Green space m² within 300 m adjacency buffer    |
| `total_green_m2`       | Weighted total (interior + 0.5 × adjacent)      |
| `green_m2_per_resident`| Per-capita green space                          |
| `green_spaces_score`   | Score 0–10                                      |

---

### 3.8 Join Flow — Vivabilité Familiale

```
iris_paris.csv         ──┐
population_paris.csv   ──┤  (left join on IRIS)
schools_score_iris.csv ──┤
healthcare_score_iris.csv ┤  LEFT JOIN on IRIS (9-digit, zero-padded)
transport_score_iris.csv  ┤
daily_services_score_iris ┤
green_spaces_score_iris   ┘
          │
          ▼
vivabilite_familiale_iris.csv
          │
          ▼
   DB table: vivabilite_familiale
```

All missing values after joins are **filled with the column median** before scoring.

---

## 4. Prix du Logement (Housing Prices)

Two distinct price datasets are maintained separately:

| Dataset         | Granularity     | Type       | Source          |
|-----------------|-----------------|------------|-----------------|
| **DVF**         | Transaction     | Sale price | Notarial records |
| **Sale Median** | Arrondissement  | Median €/m² | Historical PDF  |
| **Rent**        | Zone            | Rent €/m²  | Observatoire des Loyers |

---

### 4.1 DVF — Demande de Valeurs Foncières

**Bronze → Silver script:** [src/silver/dvf.py](src/silver/dvf.py)  
**Silver → Gold script:** [src/gold/dvf.py](src/gold/dvf.py)

#### Bronze Source

| File                                                      | Format       |
|-----------------------------------------------------------|--------------|
| `data/bronze/public_service_data/ValeursFoncieres-2025.txt` | Pipe-delimited `|` text |

#### Silver Cleaning ([src/silver/dvf.py](src/silver/dvf.py))

**Filters applied:**

| Filter                     | Value / Range           | Reason                                  |
|----------------------------|-------------------------|-----------------------------------------|
| `code_departement`         | `"75"`                  | Paris only                              |
| `nature_mutation`          | `"Vente"`               | Sales only (no donations/inheritance)   |
| `type_local`               | `{"Appartement","Maison"}` | Residential only                     |
| `surface_m2`               | [5, 1000] m²            | Remove data-entry errors                |
| `prix_m2`                  | [1000, 50000] €/m²      | Remove outliers                         |

**Derived columns:**

| Column           | Formula                                        |
|------------------|------------------------------------------------|
| `prix_m2`        | `valeur_fonciere / surface_m2`                 |
| `arrondissement` | `code_commune[-2:]` → integer (1–20)           |
| `annee`          | year extracted from `date_mutation`            |
| `mois`           | month extracted from `date_mutation`           |

**Full silver column list:**

| Column             | Type    | Description                              |
|--------------------|---------|------------------------------------------|
| `date_mutation`    | date    | Transaction date                         |
| `nature_mutation`  | string  | Always `"Vente"` after filter            |
| `valeur_fonciere`  | float   | Total sale price (€)                     |
| `numero_voie`      | string  | Street number                            |
| `type_voie`        | string  | Street type (RUE, BD, AV, …)            |
| `nom_voie`         | string  | Street name                              |
| `code_postal`      | string  | Postal code                              |
| `commune`          | string  | Municipality name                        |
| `code_departement` | string  | `"75"` after filter                      |
| `code_commune`     | string  | INSEE commune code                       |
| `section`          | string  | Land registry section                    |
| `code_type_local`  | string  | Type code                                |
| `type_local`       | string  | `"Appartement"` or `"Maison"`            |
| `surface_m2`       | float   | Living area in m²                        |
| `nb_pieces`        | int     | Number of rooms                          |
| `nature_culture`   | string  | Land use category                        |
| `arrondissement`   | int     | Paris arrondissement (1–20), derived     |
| `prix_m2`          | float   | Price per m², derived                    |
| `annee`            | int     | Transaction year                         |
| `mois`             | int     | Transaction month                        |

**Silver output:** `data/silver/dvf_paris_clean.csv` (~3.9 MB)

#### Gold Processing ([src/gold/dvf.py](src/gold/dvf.py))

The gold DVF file is the same transaction-level data with summary statistics computed for the API:

**Gold output:** `data/gold/dvf.csv`  
**No IRIS join** — DVF stays at arrondissement / address level; spatial aggregation is not applied.

**API endpoints ([api/routers/dvf.py](api/routers/dvf.py)):**

| Route             | Output                                                 |
|-------------------|--------------------------------------------------------|
| `GET /dvf/stats`  | Transaction counts, price ranges, breakdown by arrondissement and type |
| `GET /dvf/by-year`| Price trends grouped by year                           |

---

### 4.2 Sale Price Median (Arrondissement)

**Bronze → Silver script:** [src/silver/sale_price_median_to_silver.py](src/silver/sale_price_median_to_silver.py)  
**Silver → Gold script:** [src/gold/sale_price_median_to_gold.py](src/gold/sale_price_median_to_gold.py)

#### Bronze Source

| File                                                                             | Format |
|----------------------------------------------------------------------------------|--------|
| `data/bronze/sale_price_data/HistoriquedesprixaumappartementsanciensParispararrdt_2.pdf` | PDF |

**Silver output:** `data/silver/sale_price_m2.csv`

**Silver columns:**

| Column        | Description                              |
|---------------|------------------------------------------|
| `arrondissement` | Paris arrondissement (1–20)           |
| `prix_m2`     | Median price per m²                      |
| `trimestre`   | Quarter (Q1–Q4)                          |
| `date_periode`| Period label                             |

**Gold output:** `data/gold/sale_price_median.parquet`

The gold file joins the median prices with the arrondissement GeoJSON (`data/bronze/main_data/arrondissements.geojson`) to produce a geo-enriched Parquet for choropleth maps:

**Gold columns:** `geometry` (Polygon, EPSG:4326) + all silver columns.

---

### 4.3 Rent Data (Observatoire des Loyers)

**Bronze → Silver script:** [src/silver/rent_data_to_silver.py](src/silver/rent_data_to_silver.py)  
**Silver → Gold script:** [src/gold/rent_data_to_gold.py](src/gold/rent_data_to_gold.py)

#### Bronze Sources

| File                                              | Format |
|---------------------------------------------------|--------|
| `data/bronze/rent_data/Base_OP_2024_L7501.csv`   | CSV    |
| `data/bronze/rent_data/table_zones_2024_L7501_1.xls` | Excel |
| `data/bronze/rent_data/L7501_zone_elem_2024.kml` | KML    |

**Silver output:** `data/silver/rent_data_complet.csv`

**Silver columns:**

| Column              | Description                             |
|---------------------|-----------------------------------------|
| `Zone_calcul`       | Rent zone identifier                    |
| `loyer_median`      | Median rent (€/m²/month)               |
| `loyer_1_quartile`  | 25th percentile rent                    |
| `loyer_3_quartile`  | 75th percentile rent                    |
| `c_ar`              | Arrondissement code                     |

**Gold output:** `data/gold/rent_data_par_arrdt.parquet`

Gold joins rent zones with their KML polygon geometries to produce a spatial Parquet file:

**Gold columns:**

| Column              | Description                             |
|---------------------|-----------------------------------------|
| `geometry`          | Polygon from KML (EPSG:4326)            |
| `loyer_median_m2`   | Median rent per m²                      |
| `loyer_q1_m2`       | Q1 rent per m²                          |
| `loyer_q3_m2`       | Q3 rent per m²                          |
| _(+ zone metadata)_ |                                         |

---

## 5. BDCOM — Établissements Commerciaux

BDCOM (Base de Données du Commerce) is the shared foundation for both the healthcare and daily services scores.

**Bronze → Silver script:** [src/silver/bdcom.py](src/silver/bdcom.py)  
**Silver output:** `data/silver/bdcom_paris_clean.csv` (~17 MB)

#### Bronze Sources

| File                                                  | Format |
|-------------------------------------------------------|--------|
| `data/bronze/public_service_data/BDCOM_2023.csv`     | CSV    |
| `data/bronze/public_service_data/BDCOM_2023_OD.xlsx` | Excel  |

The two files are merged on `codact` (activity code).

#### Silver Columns

| Column                  | Description                                   |
|-------------------------|-----------------------------------------------|
| `X`                     | Easting (EPSG:2154, Lambert-93)               |
| `Y`                     | Northing (EPSG:2154, Lambert-93)              |
| `niv2`                  | Activity level 2 (2 categories)              |
| `niv8`                  | Activity level 8 (8 categories)              |
| `niv18`                 | Activity level 18                             |
| `niv47`                 | Activity level 47 (finest)                   |
| `codact`                | Activity code (join key between files)        |
| `Libellé activité`      | Human-readable activity label (224 postes)    |
| `TYPE`                  | Establishment type                            |
| `surf`                  | Floor area (m²)                               |

**Gold output (full BDCOM with IRIS join):** `data/gold/bdcom.csv` — adds `code_iris` via spatial join of (X, Y) coordinates into IRIS polygons.  
**DB table:** `bdcom`

#### Filtering Logic Used by Each Pillar

| Pillar             | Filter on BDCOM                                                                          |
|--------------------|------------------------------------------------------------------------------------------|
| Healthcare         | `niv47` contains `pharmacie\|médic\|opticien` OR `niv18` contains `santé`               |
| Daily services     | `niv8` ∈ `{2 (Alimentaire), 4 (Service commercial)}` + post office, library, sports     |
| General services   | `niv8` ∈ `{2, 4}` only                                                                   |

---

## 6. Database Tables

All tables are written via `src/db.py` (SQLAlchemy + PyMySQL, credentials from `.env`) using `to_sql(..., if_exists="replace")`.

| Table                   | Granularity | Source file                          |
|-------------------------|-------------|--------------------------------------|
| `school_density`        | IRIS        | `data/gold/schools_score_iris.csv`   |
| `transport_score`       | IRIS        | `data/gold/transport_score_iris.csv` |
| `transport_score_iris`  | IRIS        | `data/gold/transport_indicator_iris.csv` |
| `services_score`        | IRIS        | `data/gold/services_score_iris.csv`  |
| `healthcare_score`      | IRIS        | `data/gold/healthcare_score_iris.csv`|
| `daily_services_score`  | IRIS        | `data/gold/daily_services_score_iris.csv` |
| `green_spaces_score`    | IRIS        | `data/gold/green_spaces_score_iris.csv` |
| `vivabilite_familiale`  | IRIS        | `data/gold/vivabilite_familiale_iris.csv` |
| `family_missing_factors`| IRIS        | Inline (neutral 5.0 for childcare/safety/environment) |
| `schools_ref`           | Point       | School coordinates for map layer     |
| `population_ref`        | IRIS        | `data/silver/population_paris.csv`   |
| `sale_price_median`     | Arrondissement | `data/gold/sale_price_median.parquet` |
| `bdcom`                 | Point       | `data/gold/bdcom.csv`                |

---

## 7. API Exposure

**Framework:** FastAPI (`api/main.py`)

| Endpoint                          | Data source          | Description                          |
|-----------------------------------|----------------------|--------------------------------------|
| `GET /indicators/vivabilite/list` | `vivabilite_familiale` CSV | Paginated IRIS scores            |
| `GET /dvf/stats`                  | `dvf.csv`            | Price stats by arrondissement/type   |
| `GET /dvf/by-year`                | `dvf.csv`            | Yearly price trends                  |

**Pydantic model:** `api/models/indicators/vivabilite.py` → `VivabiliteIndicator`  
**Service layer:** `api/services/indicators/vivabilite_service.py` — `_row_to_indicator(row)` converts CSV rows to Pydantic objects.

---

## 8. Key Configuration (`src/config.py`)

| Constant                  | Value                  | Used in                            |
|---------------------------|------------------------|------------------------------------|
| `BUFFER_METERS`           | 500                    | Schools, transport, services, hospitals |
| `GREEN_SPACES_BUFFER_METERS` | 300               | Green space adjacency              |
| `MIN_POPULATION`          | 500                    | Exclude low-population IRIS zones  |
| `DVF_SURFACE_MIN`         | 5 m²                   | DVF outlier removal                |
| `DVF_SURFACE_MAX`         | 1000 m²                | DVF outlier removal                |
| `DVF_PRIX_M2_MIN`         | 1,000 €/m²             | DVF outlier removal                |
| `DVF_PRIX_M2_MAX`         | 50,000 €/m²            | DVF outlier removal                |
| `SCHOOL_TYPES`            | Collège, Maternelle, Élémentaire, Polyvalent | School filter |

---

## 9. Data Quality Notes

| Issue                      | Handling                                                          |
|----------------------------|-------------------------------------------------------------------|
| Missing IRIS scores        | Filled with column **median** before composite computation        |
| Duplicate schools          | Deduplicated on `(name, address)`, keeping most recent year       |
| Duplicate hospitals        | Deduplicated on `finess_et`                                       |
| Duplicate BDCOM rows       | Deduplicated on full row                                          |
| Invalid hospital coords    | Validated to IDF bounding box; invalid rows dropped               |
| Missing green space areas  | Computed from reprojected polygon geometry                        |
| DVF price/surface outliers | Removed by configured min/max ranges                              |
| IRIS code padding          | All codes zero-padded to 9 digits: `IRIS.str.zfill(9)`           |
| Low-population zones       | Excluded (population < 500) to avoid distorting per-capita scores |
