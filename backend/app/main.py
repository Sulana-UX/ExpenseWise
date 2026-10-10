from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.database import engine, Base
from app.routers import auth, transactions, budgets, dashboard, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to create database tables on startup."""
    # Ensure SQLite tables and schema exist
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Secure Smart Expense Tracker API",
    description=(
        "Educational & Cybersecurity Portfolio REST API for managing personal finances. "
        "Demonstrates Argon2 password hashing, JWT stateless authentication, IDOR mitigation, "
        "and strict user data isolation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS Middleware (Permits development clients from localhost and mobile emulators)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "*",  # Local development wildcard for mobile emulator testing
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Middleware to disable caching on dynamic API endpoints for real-time frontend accuracy
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Global Exception Handler for Clean Input Validation Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic validation errors cleanly without exposing internal system details."""
    errors = []
    for err in exc.errors():
        field_loc = " -> ".join([str(loc) for loc in err["loc"] if loc != "body"])
        errors.append(f"{field_loc}: {err['msg']}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Input validation failed. Please check the provided data.",
            "errors": errors,
        },
    )


# Health Check Endpoints
@app.get("/", tags=["General"])
def root_endpoint():
    return {
        "app": "Secure Smart Expense Tracker",
        "version": "1.0.0",
        "status": "healthy",
        "docs_url": "/docs",
    }


@app.get("/health", tags=["General"])
def health_check():
    return {"status": "ok", "environment": settings.APP_ENV}


# Include Feature Routers
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
