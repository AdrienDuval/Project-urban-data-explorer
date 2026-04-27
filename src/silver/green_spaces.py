"""
Bronze → Silver: Green spaces (Paris)

Loads the Paris open-data espaces_verts GeoJSON, filters to open and
family-relevant spaces (parks, gardens, squares — not decorative street
planters), and saves a clean GeoJSON for the Gold scoring step.

Output: data/silver/espaces_verts_paris.geojson
"""
import geopandas as gpd

from src.config import ESPACES_VERTS_RAW, ESPACES_VERTS_SILVER, SILVER

# These type_ev categories are decorative street furniture, not usable green
# spaces for families — they are tiny (flower boxes, road dividers, etc.)
DECORATIVE_TYPES = {
    "Décorations sur la voie publique",
    "Decoration sur la voie publique",
}


def process_green_spaces() -> gpd.GeoDataFrame:
    """
    Clean and filter Paris green spaces.

    Steps:
        1. Load GeoJSON (already EPSG:4326)
        2. Keep only open spaces (ouvert_ferme == 'Ouvert')
        3. Drop decorative street planters (not usable parks)
        4. Drop rows with null geometry or zero area
        5. Keep only the columns needed downstream
        6. Save to silver as GeoJSON

    Returns:
        Cleaned GeoDataFrame saved to ESPACES_VERTS_SILVER.
    """
    print(f"[green_spaces] Loading {ESPACES_VERTS_RAW.name}...")
    gdf = gpd.read_file(ESPACES_VERTS_RAW)
    print(f"[green_spaces]   → {len(gdf):,} features loaded")

    # ── Filter to open spaces ─────────────────────────────────────────────────
    if "ouvert_ferme" in gdf.columns:
        before = len(gdf)
        gdf = gdf[gdf["ouvert_ferme"].astype(str).str.strip() == "Ouvert"].copy()
        print(f"[green_spaces]   Open filter: {len(gdf):,}/{before:,} kept")

    # ── Drop decorative types ─────────────────────────────────────────────────
    if "type_ev" in gdf.columns:
        before = len(gdf)
        gdf = gdf[~gdf["type_ev"].isin(DECORATIVE_TYPES)].copy()
        print(f"[green_spaces]   Decorative filter: {len(gdf):,}/{before:,} kept")

    # ── Drop null geometry and ensure valid polygons ──────────────────────────
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()

    # ── Fill missing surface area from geometry ───────────────────────────────
    # surface_totale_reelle is in m² — use it when available, else derive it.
    # Geometry is in EPSG:4326 so we project to Lambert-93 for area in m².
    if "surface_totale_reelle" in gdf.columns:
        missing_area = gdf["surface_totale_reelle"].isna() | (gdf["surface_totale_reelle"] <= 0)
        if missing_area.any():
            projected = gdf[missing_area].to_crs(epsg=2154)
            gdf.loc[missing_area, "surface_totale_reelle"] = projected.geometry.area.values
    else:
        projected = gdf.to_crs(epsg=2154)
        gdf["surface_totale_reelle"] = projected.geometry.area.values

    gdf["surface_totale_reelle"] = gdf["surface_totale_reelle"].fillna(0)

    # ── Select final columns ──────────────────────────────────────────────────
    keep_cols = [
        "nsq_espace_vert", "nom_ev", "type_ev", "categorie",
        "surface_totale_reelle", "geometry",
    ]
    keep_cols = [c for c in keep_cols if c in gdf.columns]
    gdf = gdf[keep_cols].copy()

    # ── Save ──────────────────────────────────────────────────────────────────
    SILVER.mkdir(parents=True, exist_ok=True)
    gdf.to_file(ESPACES_VERTS_SILVER, driver="GeoJSON")
    print(f"[green_spaces] {len(gdf):,} spaces saved → {ESPACES_VERTS_SILVER.name}")
    print(f"  Types: {gdf['type_ev'].value_counts().head(5).to_dict()}")
    return gdf
