"""FastAPI application.

    uvicorn backend.app:app --reload --port 8000

Read-only over the three committed artefacts (AGENTS.md section 1.2). The
artefacts are loaded once at startup and held in memory; nothing under
backend/ writes to them.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import artefacts as art
from .config import API_PREFIX, CORS_ORIGINS, PLOT_DIRS
from .routers import match, meta, style, value


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load once. A missing key fails here rather than per request."""
    app.state.artefacts = art.load()
    yield
    # Nothing to tear down: no connections, no write handles, no temp files.


app = FastAPI(
    title="PL-Analytics API",
    version="1.0.0",
    description=(
        "Read-only API over three committed model artefacts.\n\n"
        "Route names reflect what actually happens. `/estimate` computes; "
        "`/held-out-forecast` and `/assignment` retrieve. Project 02's "
        "forecasts are never computed per request -- every match is in that "
        "model's training set, where it scores 0.980 against a real accuracy "
        "of 0.470, so a live endpoint would misrepresent it by a factor of "
        "two.\n\n"
        "Refusal (`not_calibrated`) and out-of-scope return HTTP 200 with a "
        "`status` discriminant. The entity exists and the API knows about it; "
        "it is the model that has nothing honest to say."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],      # the API is read-only
    allow_headers=["*"],
)

app.include_router(meta.router, prefix=API_PREFIX)
app.include_router(value.router, prefix=API_PREFIX)
app.include_router(match.router, prefix=API_PREFIX)
app.include_router(style.router, prefix=API_PREFIX)

# Committed PNGs served as-is rather than regenerated, so the methodology
# pages cannot drift from the evidence the README's claims rest on.
for tool, directory in PLOT_DIRS.items():
    if directory.exists():
        app.mount(f"/plots/{tool}", StaticFiles(directory=directory),
                  name=f"plots-{tool}")
