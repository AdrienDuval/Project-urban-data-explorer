# Vivabilité familiale — pipeline map

Present **after** running the **Transport** indicator (`src/indicators/transport/`): the composite reads `TRANSPORT_SCORE_GOLD` produced there.

## 1. Silver (`silver/`)

| File | Role |
|------|------|
| `schools.py` | School registry → IRIS-ready table |
| `hospitals.py` | Hospital / SSU points |
| `green_spaces.py` | Green space polygons |

*(Stops and Vélib are in `../transport/silver.py`.)*

## 2. Gold pillars (`gold/`)

| File | Output / function |
|------|-------------------|
| `school_density.py` | `compute_school_density()` |
| `services_score.py` | `compute_services_score()` |
| `green_spaces_score.py` | `compute_green_spaces_score()` |
| `family_support_scores.py` | `compute_family_support_scores()` |
| `composite.py` | `compute_vivabilite_familiale()` — merges pillars **including transport** from `TRANSPORT_SCORE_GOLD` |

Depends on **foundation** IRIS/population, **foundation.reference**, and **transport** gold outputs.
