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
from api.routers import iris, map as map_router, population, schools, stats, bdcom, dvf
from api.routers.indicators import schools as indicator_schools
from api.routers.indicators import vivabilite as indicator_vivabilite
from api.routers.indicators import transport as indicator_transport
from api.services.data_loader import DataStore


# ---------------------------------------------------------------------------
# Lifespan: load data once at startup, clean up on shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all datasets into ``app.state.data`` at startup."""
    app.state.data = DataStore.load()
    yield
    # No teardown required for in-memory DataFrames


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
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # Routers
    # -----------------------------------------------------------------------
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
    def health(app=app):
        """Confirm the API is running and all datasets are loaded."""
        data: DataStore = app.state.data
        return {
            "status": "ok",
            "iris_zones": len(data.iris_scores),
            "schools": len(data.schools),
            "population_zones": len(data.population),
            "vivabilite_zones": len(data.vivabilite_scores),
            "transport_points": len(data.transport_points),
            "thermal_comfort_zones": len(data.thermal_comfort_scores),
            "rent_zones": len(data.rent_price_scores),
            "sale_price_rows": len(data.sale_price_scores),
        }

    return app


# Module-level instance consumed by uvicorn
app = create_app()
