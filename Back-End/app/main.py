# =========================================================
# MAIN APPLICATION
# File: app/main.py
# =========================================================

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes.chat import router as chat_router
from app.services.retrieval import initialize_chroma


# =========================================================
# LOGGING CONFIGURATION
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )
)

logger = logging.getLogger(__name__)


# =========================================================
# APPLICATION LIFECYCLE
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    # =====================================================
    # STARTUP
    # =====================================================

    try:

        logger.info(
            "Initializing SHL assessment database..."
        )

        initialize_chroma()

        logger.info(
            "Chroma database initialized successfully"
        )

    except Exception as error:

        logger.exception(
            f"Startup initialization failed: {error}"
        )

    yield

    # =====================================================
    # SHUTDOWN
    # =====================================================

    logger.info(
        "Shutting down SHL Assessment API..."
    )


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(

    title="SHL Assessment Recommendation API",

    description=(
        "Enterprise-grade SHL assessment "
        "recommendation and comparison API."
    ),

    version="2.0.0",

    lifespan=lifespan
)


# =========================================================
# CORS CONFIGURATION
# =========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# =========================================================
# ROUTERS
# =========================================================

app.include_router(
    chat_router,
    prefix="/api"
)


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
async def root():

    return {

        "message": (
            "SHL Assessment Recommendation API "
            "Running Successfully"
        ),

        "version": "2.0.0",

        "status": "healthy"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
async def health():

    return {

        "status": "healthy",

        "service": (
            "SHL Assessment Recommendation API"
        )
    }


# =========================================================
# GLOBAL EXCEPTION HANDLER
# =========================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request,
    exc
):

    logger.exception(
        f"Unhandled exception: {exc}"
    )

    return JSONResponse(

        status_code=500,

        content={
            "error": (
                "Internal server error"
            ),
            "message": (
                "Something went wrong while "
                "processing the request."
            )
        }
    )