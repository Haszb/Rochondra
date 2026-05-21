from fastapi import FastAPI
from api.routers import whitepaper_router

app = FastAPI(title="Rochondra Core API")

# Inclusion des routeurs thématiques
app.include_router(whitepaper_router.router, prefix="/api")
# app.include_router(tokenomics_router.router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "healthy"}