from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.utils.logger import setup_logger
from app.database.connection import engine, Base
from app.routes import upload_routes, dashboard_routes

logger = setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Invoice Processor API")
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise
    
    yield
    
    logger.info("Shutting down Invoice Processor API")


app = FastAPI(
    title="Invoice Processor API",
    description="API for processing and managing invoice data with AI-powered field mapping",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_routes.router, prefix=settings.API_PREFIX)
app.include_router(dashboard_routes.router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    return {
        "message": "Invoice Processor API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
