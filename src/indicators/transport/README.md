# Transport indicator (TR)

Standalone pipeline that powers the **Transport** tab in the app (`/indicators/transport`, map accessibility layer).

## Flow

1. **`silver.py`** — clean GTFS-style stops + Vélib → silver CSVs.
2. **`transport_score.py`** —  
   - `compute_transport_score` → 0–10 pillar score (**reused** as input when building vivabilité familiale).  
   - `compute_transport_indicator_score` → 0–1 score for the **Transport** API.
3. **`transport_points.py`** — merged point table for map markers (`transport_points` in DB).

**Vivabilité familiale** does not own this code; it **reads** `TRANSPORT_SCORE_GOLD` in `vivabilite_familiale/gold/composite.py` like any other pillar input.
