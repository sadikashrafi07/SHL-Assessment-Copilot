# =========================================================
# MAIN APPLICATION
# File: app/main.py
# Production Lightweight SHL Retrieval API
# =========================================================

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes.chat import router as chat_router

from app.services.retrieval import (
    BM25,
    CATALOG,
    DOCUMENTS,
    get_catalog_embeddings,
    get_embedding_model,
)

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger(__name__)

# =========================================================
# STARTUP VALIDATION
# =========================================================


def validate_startup() -> None:

    logger.info(
        "Running retrieval system validation..."
    )

    # =====================================================
    # VALIDATE CATALOG
    # =====================================================

    if not CATALOG:

        raise RuntimeError(
            "Catalog is empty."
        )

    logger.info(
        "Catalog loaded: %s assessments",
        len(CATALOG),
    )

    # =====================================================
    # VALIDATE DOCUMENTS
    # =====================================================

    if not DOCUMENTS:

        raise RuntimeError(
            "Documents not initialized."
        )

    logger.info(
        "Documents initialized: %s",
        len(DOCUMENTS),
    )

    # =====================================================
    # VALIDATE BM25
    # =====================================================

    if BM25 is None:

        raise RuntimeError(
            "BM25 engine failed initialization."
        )

    logger.info(
        "BM25 initialized successfully"
    )

    # =====================================================
    # VALIDATE EMBEDDINGS
    # =====================================================

    embeddings = get_catalog_embeddings()

    if embeddings is None:

        raise RuntimeError(
            "Embeddings failed loading."
        )

    if len(embeddings) != len(CATALOG):

        raise RuntimeError(
            "Embedding count mismatch. "
            f"embeddings={len(embeddings)} "
            f"catalog={len(CATALOG)}"
        )

    logger.info(
        "Embeddings loaded: shape=%s",
        embeddings.shape,
    )

    # =====================================================
    # VALIDATE MODEL
    # =====================================================

    model = get_embedding_model()

    if model is None:

        raise RuntimeError(
            "Embedding model failed loading."
        )

    logger.info(
        "FastEmbed model initialized successfully"
    )

    # =====================================================
    # WARMUP INFERENCE
    # =====================================================

    logger.info(
        "Running embedding warmup..."
    )

    start = time.perf_counter()

    _ = list(
        model.embed(
            [
                "software engineer",
                "data scientist",
                "leadership assessment",
            ]
        )
    )

    elapsed = round(
        time.perf_counter() - start,
        3,
    )

    logger.info(
        "Warmup completed in %ss",
        elapsed,
    )

    logger.info(
        "Retrieval system ready."
    )


# =========================================================
# APPLICATION LIFECYCLE
# =========================================================


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(
        "Starting SHL Assessment API..."
    )

    try:

        validate_startup()

        logger.info(
            "Application startup completed successfully"
        )

    except Exception as error:

        logger.exception(
            "Startup initialization failed: %s",
            error,
        )

        raise error

    yield

    logger.info(
        "Shutting down SHL Assessment API..."
    )


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="SHL Assessment Recommendation API",
    description=(
        "Production-grade hybrid retrieval "
        "engine for SHL assessment "
        "recommendation."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

# =========================================================
# CORS
# =========================================================

ALLOWED_ORIGINS = [

    # Local development
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://localhost:8081",

    # Production frontend
    "https://shl-assessment-copilot.angadimohammadsadiq.workers.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# ROUTES
# =========================================================

app.include_router(
    chat_router,
    prefix="/api",
)

# =========================================================
# ROOT
# =========================================================


@app.get("/")
async def root():

    return {
        "message": (
            "SHL Assessment Recommendation API "
            "running successfully"
        ),
        "version": "3.0.0",
        "retrieval_engine": {
            "semantic": "BAAI/bge-small-en-v1.5",
            "keyword": "BM25",
            "vector_search": "NumPy Cosine Similarity",
            "reranking": True,
            "hybrid_search": True,
        },
        "catalog_size": len(CATALOG),
        "status": "healthy",
    }


# =========================================================
# HEALTH CHECK
# =========================================================


@app.get("/api/health")
async def health():

    try:

        embeddings = get_catalog_embeddings()

        return {
            "status": "healthy",
            "service": (
                "SHL Assessment Recommendation API"
            ),
            "catalog_loaded": True,
            "catalog_size": len(CATALOG),
            "documents_loaded": len(DOCUMENTS),
            "embeddings_loaded": True,
            "embedding_shape": embeddings.shape,
            "bm25_ready": BM25 is not None,
            "model_ready": True,
        }

    except Exception as error:

        logger.exception(
            "Health check failed: %s",
            error,
        )

        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(error),
            },
        )


# =========================================================
# GLOBAL ERROR HANDLER
# =========================================================


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):

    logger.exception(
        "Unhandled exception: %s",
        exc,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": (
                "An unexpected error occurred "
                "while processing the request."
            ),
        },
    )