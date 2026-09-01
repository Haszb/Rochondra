#!/usr/bin/env python3

import asyncio
import json
import logging
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from api.schemas import (
    ExtractionResponse,
    FinalizeResponse,
    ResumeSessionResponse,
    SentimentAnalysisResponse,
    StructuralAnalysisResponse,
    TocExtractionResponse,
)
from core_shared.config import WhitepaperConfig
from db.cache.client import cache_delete, cache_get, cache_set
from db.object_store.whitepaper import (
    delete_artifacts_from_temp,
    download_pdf_from_temp,
    list_pdf_uuids_in_temp,
    move_artifacts_from_temp_to_documents,
)
from db.sql.whitepaper.repository import persist_structural_analysis
from modules.whitepaper.extractor import stage_document
from modules.whitepaper.sentiment_analysis import SectionAnalyzer
from modules.whitepaper.structural_analysis import compute_structural_metrics
from modules.whitepaper.Table_of_content_extractor import WhitepaperExtractor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whitepaper", tags=["Whitepaper"])

_section_analyzer = SectionAnalyzer()

_MAX_FILE_SIZE = WhitepaperConfig.MAX_UPLOAD_BYTES


# ---------------------------------------------------------------------------
# Registry helpers
# Everything a staged document accumulates lives in Redis under ``metadata:``,
# ``structural_analysis:``, ``toc_extraction:`` and ``sentiment_analysis:``,
# all keyed by uuid and all written without a TTL. /finalize is what deletes
# them, once it has copied what it needs into Postgres — expiring them on a
# timer instead would break the save branch, which reads the structural key
# back. Abandoned documents are left to a future cleanup job.
# ---------------------------------------------------------------------------

_METADATA_KEY = "metadata:{uuid}"


def _get_current_uuid(request: Request) -> str:
    """Retrieve the current document UUID from the session.

    Args:
        request: The incoming FastAPI request carrying the session.

    Returns:
        The UUID string of the document currently in session.

    Raises:
        HTTPException: 400 if no document UUID is found in the session.
    """
    doc_uuid = request.session.get("current_uuid")
    if not doc_uuid:
        raise HTTPException(
            status_code=400,
            detail="No document in session. Extract a document via /extract first.",
        )
    return doc_uuid


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    request: Request,
    file: UploadFile = File(...),
    extract_images: bool = Form(...),
    save_markdown: bool = Form(...),
    project_name: str = Form(default=""),
) -> ExtractionResponse:
    """Extract a PDF whitepaper and stage its outputs in MinIO, returning its Markdown content."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename.")

    try:
        file_content = await file.read()
    except Exception as e:
        logger.error("Failed to read uploaded file: %s", e)
        raise HTTPException(status_code=400, detail="Failed to read uploaded file.")

    if not file_content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File content is not a valid PDF.")

    if len(file_content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {_MAX_FILE_SIZE // (1024 * 1024)} MB).",
        )

    try:
        generated_uuid, markdown_content = await asyncio.to_thread(
            stage_document,
            file_content=file_content,
            filename=file.filename,
            extract_images=extract_images,
        )

        metadata = {
            "uuid": generated_uuid,
            "project_name": (project_name or Path(file.filename).stem).strip() or "Unknown",
            "filename": file.filename,
            "file_size_mb": round(len(file_content) / (1024 * 1024), 2),
            "status": "success",
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "marked_for_deletion": not save_markdown,
        }
        await asyncio.to_thread(
            cache_set,
            _METADATA_KEY.format(uuid=generated_uuid),
            json.dumps(metadata),
            None,
        )

        request.session["current_uuid"] = generated_uuid
        request.session["current_project"] = project_name or Path(file.filename).stem

        return ExtractionResponse(
            status="success",
            extract_images=extract_images,
            save_markdown=save_markdown,
            doc_uuid=generated_uuid,
            markdown_content=markdown_content,
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while processing file %s", file.filename)
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.post("/structural_analysis", response_model=StructuralAnalysisResponse)
async def analyze_document_structure(
    request: Request,
    include_images_stats: bool = Form(default=False),
) -> StructuralAnalysisResponse:
    """Run structural metrics analysis on the document currently in session."""
    doc_uuid = _get_current_uuid(request)

    try:
        metrics = await asyncio.to_thread(
            compute_structural_metrics,
            uuid=doc_uuid,
            include_images_stats=include_images_stats,
        )
        metrics_dict = asdict(metrics)

        response = StructuralAnalysisResponse(
            status="success",
            uuid=doc_uuid,
            metrics=metrics_dict,
        )

        await asyncio.to_thread(
            cache_set, f"structural_analysis:{doc_uuid}", response.model_dump_json(), None
        )

        return response

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Structural analysis failed for %s: %s", doc_uuid, e)
        raise HTTPException(status_code=500, detail="Internal error during structural analysis.")


@router.post("/toc_extraction", response_model=TocExtractionResponse)
async def extract_toc(request: Request) -> TocExtractionResponse:
    """Extract the table of contents from the document currently in session."""
    doc_uuid = _get_current_uuid(request)

    extractor = WhitepaperExtractor(
        llm_model=WhitepaperConfig.LLM_MODEL,
    )

    def _download_and_extract() -> list:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_pdf_path = Path(temp_dir) / f"{doc_uuid}.pdf"
            download_pdf_from_temp(doc_uuid, temp_pdf_path)
            return extractor.extract(uuid=doc_uuid, pdf_path=temp_pdf_path, use_llm=True)

    try:
        sections = await asyncio.to_thread(_download_and_extract)

        toc_data = "".join(
            f"{'  ' * (s.level - 1)}{'#' * s.level} {s.title}  (p.{s.page})\n"
            for s in sections
        )

        response = TocExtractionResponse(
            status="success",
            uuid=doc_uuid,
            toc_content=toc_data,
        )

        await asyncio.to_thread(
            cache_set, f"toc_extraction:{doc_uuid}", response.model_dump_json(), None
        )

        return response

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"PDF document not found for UUID: {doc_uuid}",
        )
    except Exception as e:
        logger.error("TOC extraction failed for %s: %s", doc_uuid, e)
        raise HTTPException(
            status_code=500,
            detail="Internal error during table of contents extraction.",
        )


@router.post("/sentiment_analysis", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(request: Request) -> SentimentAnalysisResponse:
    """Run semantic analysis (sentiment + summary) on each section of the document."""
    doc_uuid = _get_current_uuid(request)

    try:
        results = await asyncio.to_thread(_section_analyzer.analyze, uuid=doc_uuid)

        payload = {title: asdict(analysis) for title, analysis in results.items()}

        response = SentimentAnalysisResponse(
            status="success",
            uuid=doc_uuid,
            analyses=payload,  # type: ignore[arg-type]
        )

        await asyncio.to_thread(
            cache_set, f"sentiment_analysis:{doc_uuid}", response.model_dump_json(), None
        )

        return response

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Sentiment analysis failed for %s: %s", doc_uuid, e)
        raise HTTPException(
            status_code=500,
            detail="Internal error during sentiment analysis.",
        )


@router.post("/resume", response_model=ResumeSessionResponse)
async def resume_session(
    request: Request,
    uuid: str | None = None,
) -> ResumeSessionResponse:
    """List staged documents and optionally bind one to the current session.

    Without a ``uuid`` query parameter, returns the list of staged UUIDs so a
    caller can pick one. With a ``uuid``, verifies it is staged in MinIO and
    binds it to the session — skipping a fresh ``/extract`` upload.

    The full ``available_uuids`` list is always returned, so the caller can
    refresh its picker in the same round-trip.
    """
    available = await asyncio.to_thread(list_pdf_uuids_in_temp)

    if uuid is None:
        return ResumeSessionResponse(status="success", available_uuids=available)

    if uuid not in available:
        raise HTTPException(status_code=404, detail=f"No staged PDF found for UUID: {uuid}")

    request.session["current_uuid"] = uuid
    return ResumeSessionResponse(status="success", uuid=uuid, available_uuids=available)


@router.post("/finalize", response_model=FinalizeResponse)
async def finalize_document(
    request: Request,
    uuid: str | None = None,
) -> FinalizeResponse:
    """Close a document's session: either save it durably or delete it.

    The ``marked_for_deletion`` flag captured at ``/extract`` time (from the
    ``save_markdown`` toggle) decides the branch:

    * **SAVE**  — upsert Postgres rows and move MinIO artifacts to
      documents-bucket.
    * **DELETE** — drop MinIO artifacts from temp-bucket, no Postgres write.

    Both branches drop the four uuid-scoped Redis keys and clear the session
    if the UUID matches. Prefers the session's ``current_uuid`` when set;
    otherwise a ``uuid`` query parameter is required.
    """
    session_uuid = request.session.get("current_uuid")
    uuid = session_uuid or uuid
    if not uuid:
        raise HTTPException(
            status_code=400,
            detail="No UUID provided and no document in session.",
        )

    metadata_raw = await asyncio.to_thread(cache_get, _METADATA_KEY.format(uuid=uuid))
    if metadata_raw is None:
        raise HTTPException(
            status_code=404,
            detail=f"No cached metadata found for UUID: {uuid}",
        )

    try:
        metadata = json.loads(metadata_raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Corrupted metadata payload.")

    redis_keys = (
        _METADATA_KEY.format(uuid=uuid),
        f"structural_analysis:{uuid}",
        f"toc_extraction:{uuid}",
        f"sentiment_analysis:{uuid}",
    )

    if metadata.get("marked_for_deletion"):
        try:
            deleted = await asyncio.to_thread(delete_artifacts_from_temp, uuid)
        except Exception as e:
            logger.exception("Failed to delete MinIO artifacts for %s", uuid)
            raise HTTPException(status_code=500, detail=f"MinIO delete failed: {e}")

        await asyncio.to_thread(cache_delete, *redis_keys)

        if request.session.get("current_uuid") == uuid:
            request.session.pop("current_uuid", None)
            request.session.pop("current_project", None)

        return FinalizeResponse(
            status="success",
            uuid=uuid,
            action="deleted",
            deleted=[*deleted, *(f"redis:{k}" for k in redis_keys)],
        )

    structural_raw = await asyncio.to_thread(cache_get, f"structural_analysis:{uuid}")
    if structural_raw is None:
        raise HTTPException(
            status_code=404,
            detail=f"No cached structural analysis found for UUID: {uuid}",
        )

    try:
        metrics = json.loads(structural_raw).get("metrics", {})
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Corrupted cache payload.")

    try:
        await asyncio.to_thread(persist_structural_analysis, uuid, metrics, metadata)
    except Exception as e:
        logger.exception("Failed to persist structural analysis to Postgres for %s", uuid)
        raise HTTPException(status_code=500, detail=f"Postgres write failed: {e}")

    try:
        moved = await asyncio.to_thread(move_artifacts_from_temp_to_documents, uuid)
    except Exception as e:
        logger.exception("Failed to move MinIO artifacts for %s", uuid)
        raise HTTPException(status_code=500, detail=f"MinIO move failed: {e}")

    await asyncio.to_thread(cache_delete, *redis_keys)

    if request.session.get("current_uuid") == uuid:
        request.session.pop("current_uuid", None)
        request.session.pop("current_project", None)

    return FinalizeResponse(
        status="success",
        uuid=uuid,
        action="saved",
        persisted=["postgres:whitepaper", "postgres:fact_structural", *moved],
    )