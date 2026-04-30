"""FastAPI application factory.

Entry point for the Urban Data Explorer API.  Run with:

    uvicorn api.main:app --reload

Or use the convenience script at the project root:

    python run_api.py
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import API_DESCRIPTION, API_TITLE, API_VERSION, CORS_ORIGINS
from api.routers import (
    auth as auth_router,
    bdcom,
    dvf,
    iris,
    map as map_router,
    population,
    schools,
    stats,
    zone_analytics,
)
from api.routers.indicators import schools as indicator_schools
from api.routers.indicators import vivabilite as indicator_vivabilite
from api.routers.indicators import transport as indicator_transport
from api.routers.indicators import thermal_comfort
from api.services.spatial_cache import get_spatial_store


# ---------------------------------------------------------------------------
# Lifespan: pre-warm spatial cache at startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm the spatial GeoDataFrame cache so the first map request is fast."""
    get_spatial_store()
    yield


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
        lifespan=lifespan,
        # Expose interactive docs at /docs (Swagger) and /redoc
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — allow the local dev frontends listed in config
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # Routers
    # -----------------------------------------------------------------------
    app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
    app.include_router(iris.router, prefix="/iris", tags=["IRIS Zones"])
    app.include_router(population.router, prefix="/population", tags=["Population"])
    app.include_router(schools.router, prefix="/schools", tags=["Schools"])
    app.include_router(
        indicator_schools.router,
        prefix="/indicators/schools",
        tags=["Indicators — Schools"],
    )
    app.include_router(
        indicator_vivabilite.router,
        prefix="/indicators/vivabilite-familiale",
        tags=["Indicators — Vivabilité Familiale"],
    )
    app.include_router(
        indicator_transport.router,
        prefix="/indicators/transport",
        tags=["Indicators — Transport"],
    )
    app.include_router(map_router.router, prefix="/map", tags=["Map Layers"])
    app.include_router(stats.router, prefix="/stats", tags=["Statistics"])
    app.include_router(bdcom.router, prefix="/bdcom", tags=["BDCom"])
    app.include_router(dvf.router, prefix="/dvf", tags=["DVF"])
    app.include_router(
        zone_analytics.router,
        prefix="/analytics/zone-clicks",
        tags=["Analytics — Zone interest"],
    )

    app.include_router(
        thermal_comfort.router, 
        prefix="/indicators/thermal-comfort", 
        tags=["Thermal Comfort"])


    # -----------------------------------------------------------------------
    # Root / health endpoints
    # -----------------------------------------------------------------------

    @app.get("/", include_in_schema=False)
    def root():
        """Minimal landing page — redirects users to the interactive docs."""
        return JSONResponse(
            {
                "message": "Urban Data Explorer API",
                "version": API_VERSION,
                "docs": "/docs",
                "redoc": "/redoc",
            }
        )

    @app.get(
        "/health",
        tags=["Health"],
        summary="Health check",
        description="Returns 200 OK with dataset record counts when the API is ready.",
    )
    def health():
        """Confirm the API is running and the database is reachable."""
        from sqlalchemy import text
        from src.db import engine
        with engine.connect() as conn:
            return {
                "status": "ok",
                "iris_zones": conn.execute(text("SELECT COUNT(*) FROM school_density")).scalar(),
                "schools": conn.execute(text("SELECT COUNT(*) FROM schools_ref")).scalar(),
                "population_zones": conn.execute(text("SELECT COUNT(*) FROM population_ref")).scalar(),
                "vivabilite_zones": conn.execute(text("SELECT COUNT(*) FROM vivabilite_familiale")).scalar(),
                "transport_points": conn.execute(text("SELECT COUNT(*) FROM transport_points")).scalar(),
                "thermal_comfort_zones": conn.execute(text("SELECT COUNT(*) FROM thermal_comfort")).scalar(),
                "rent_zones": conn.execute(text("SELECT COUNT(*) FROM rent_data")).scalar(),
                "sale_price_rows": conn.execute(text("SELECT COUNT(*) FROM sale_price_median")).scalar(),
            }

    return app


# Module-level instance consumed by uvicorn
app = create_app()
