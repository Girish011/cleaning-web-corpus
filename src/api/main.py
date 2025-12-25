"""
FastAPI main application entry point.

Sets up the FastAPI app with routers, middleware, and error handlers.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import workflow, procedures, stats
from src.api.middleware.error_handler import error_handler_middleware

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cleaning Workflow Planner API",
    description="API for generating structured cleaning workflows for robots and AI agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS (enabled for all origins in MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP: allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handling middleware (must be added after CORS)
app.middleware("http")(error_handler_middleware)

# Include routers
app.include_router(workflow.router, prefix="/api/v1", tags=["workflow"])
app.include_router(procedures.router, prefix="/api/v1", tags=["procedures"])
app.include_router(stats.router, prefix="/api/v1", tags=["stats"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "cleaning-workflow-planner"}


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Starting Cleaning Workflow Planner API")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Cleaning Workflow Planner API")

