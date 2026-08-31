#!/usr/bin/env python3

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware

from api.routers import whitepaper_router
from core_shared.config import API_HOST, API_PORT, SESSION_SECRET_KEY
from db.object_store.whitepaper import list_pdf_uuids_in_temp
from db.sql.base import Base, engine
from db.sql.whitepaper import (
    models,  # noqa: F401  (registers ORM models on Base.metadata)
)

logger = logging.getLogger("rochondra.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Postgres schema is up to date.")
    except Exception as e:  # noqa: BLE001
        # Not fatal: the extract / TOC / sentiment stages don't touch Postgres,
        # so the API stays usable. Only /finalize's SAVE branch will fail.
        logger.warning("Could not create Postgres tables at startup: %s", e)

    try:
        uuids = list_pdf_uuids_in_temp()
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not list staged documents at startup: %s", e)
        uuids = []

    if uuids:
        logger.info("Staged documents available for /whitepaper/resume (%d):", len(uuids))
        for u in uuids:
            logger.info("  - %s", u)
    else:
        logger.info("No staged documents found in MinIO.")

    yield


app = FastAPI(title="Rochondra Core API", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    https_only=False,
    same_site="lax",
)

app.include_router(whitepaper_router.router, prefix="/api")


def custom_openapi() -> dict:
    """Regenerate the OpenAPI schema on every request, injecting a live UUID
    dropdown into the ``/whitepaper/resume`` endpoint's ``uuid`` parameter."""
    schema = get_openapi(title=app.title, version="1.0.0", routes=app.routes)

    try:
        uuids = list_pdf_uuids_in_temp()
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not list UUIDs for OpenAPI schema: %s", e)
        uuids = []

    if uuids:
        resume_op = schema.get("paths", {}).get("/api/whitepaper/resume", {}).get("post", {})
        for param in resume_op.get("parameters", []):
            if param.get("name") != "uuid":
                continue
            param_schema = param.get("schema", {})
            # Optional[str] serialises as ``anyOf: [{type:string}, {type:null}]``
            if "anyOf" in param_schema:
                for sub in param_schema["anyOf"]:
                    if sub.get("type") == "string":
                        sub["enum"] = uuids
            else:
                param_schema["enum"] = uuids

    return schema


app.openapi = custom_openapi  # type: ignore[method-assign]

@app.get("/")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=True)