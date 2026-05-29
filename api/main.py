from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from api.routers import whitepaper_router
from core_shared.config import init_storage_directories


init_storage_directories()


app = FastAPI(title="Rochondra Core API")

app.add_middleware(
    SessionMiddleware, 
    secret_key="change-me-in-production-use-env-var"
)

# Inclusion des routeurs thématiques
app.include_router(whitepaper_router.router, prefix="/api")
# app.include_router(tokenomics_router.router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "healthy"}