import os
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from api.routers import whitepaper_router
from core_shared.config import init_storage_directories, API_HOST, API_PORT

init_storage_directories()

app = FastAPI(title="Rochondra Core API")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "change-me-in-production-use-env-var"),
    https_only=False,
    same_site="lax",
)

app.include_router(whitepaper_router.router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=True)