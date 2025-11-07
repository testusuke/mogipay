"""FastAPI application entry point.

This module creates and configures the FastAPI application instance:
- Application initialization
- Router registration
- CORS configuration
- Exception handlers
- Health check endpoint
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth_controller,
    financial_controller,
    inventory_controller,
    kitchen_controller,
    product_controller,
    sales_controller,
)

# Create FastAPI app
app = FastAPI(
    title="MogiPay API",
    description="学園祭模擬店向けレジ/売上管理システム",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
# Development: Allow all origins
# Production: Restrict to frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_controller.router)
app.include_router(product_controller.router)
app.include_router(sales_controller.router)
app.include_router(inventory_controller.router)
app.include_router(financial_controller.router)
app.include_router(kitchen_controller.router)


@app.get("/api/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint.

    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "service": "MogiPay API",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors.

    Args:
        request: The request that caused the exception
        exc: The exception that was raised

    Returns:
        JSON error response
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "システムエラーが発生しました。しばらく待ってから再度お試しください。",
        },
    )
