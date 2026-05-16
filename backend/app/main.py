"""
FastAPI Main Application
=========================
Court Case Intelligence System (CCIS) — Backend API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.cases import router as cases_router
from backend.routes.judges import router as judges_router
from backend.routes.citations import router as citations_router
from backend.routes.analytics import router as analytics_router
from backend.routes.search import router as search_router

app = FastAPI(
    title="Court Case Intelligence System API",
    description="Legal analytics, citation intelligence, judge analytics, and case search — MySQL 8.0 powered",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(cases_router, prefix="/api/cases", tags=["Cases"])
app.include_router(judges_router, prefix="/api/judges", tags=["Judges"])
app.include_router(citations_router, prefix="/api/citations", tags=["Citations"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(search_router, prefix="/api/search", tags=["Search"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": "Court Case Intelligence System",
        "version": "1.0.0",
        "database": "MySQL 8.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "database": "mysql"}
