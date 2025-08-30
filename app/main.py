from fastapi import FastAPI
from app.api.v1.routes import router as api_router
from app.core.logging import setup_logging
from app.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(title="Grocery Receipt Shelf Life Service")
    
    setup_logging(settings.log_level)
    
    app.include_router(api_router, prefix="/api/v1")
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)