# Pipeline layout by indicator

Code that used to sit flat under `src/silver/` and `src/gold/` now lives under **`src/indicators/<name>/`**, in reading order for demos.

| Package | Role | Typical flow (run order) |
|---------|------|--------------------------|
| **`foundation/`** | IRIS geometry, population, DB reference loads for gold | `iris` → `population` → (gold stage) `reference` |
| **`transport/`** | Public transport & Vélib — **standalone** TR indicator; API + map points; pillar score reused by vivabilité | `silver.py` → `transport_score.py` → `transport_points.py` |
| **`thermal_comfort/`** | Micro-climate comfort | `silver.py` → `gold.py` |
| **`housing_market/`** | Median rent & sale by arrondissement | `rent_silver` / `sale_silver` → `rent_gold` / `sale_gold` |
| **`demographics/`** | Socio-demographic index | `silver.py` → `gold.py` |
| **`dvf/`** | Property transactions (DVF) | `silver.py` → `gold.py` |
| **`bdcom/`** | Commercial premises (BDCom) | `silver.py` → `gold.py` |
| **`vivabilite_familiale/`** | Non-transport pillars + composite (reads transport gold CSV as input) | `silver/*` (schools, hospitals, green spaces) → `gold/*` → `composite.py` |

The orchestrator **`run_pipeline.py`** imports from these packages (not from `silver`/`gold`).

**Backward compatibility:** the old module paths (e.g. `src.silver.iris`) remain as thin files that re-export from `src.indicators`.

Misc scripts that are not tied to a single indicator stay where they are (e.g. `src/silver/pop_csp_to_silver.py`, `src/transport_score.py`).
