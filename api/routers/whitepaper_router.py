import asyncio
import logging
import re
import shutil
import tempfile
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from filelock import FileLock

from api.schemas import (
    ExtractionResponse,
    SentimentAnalysisResponse,
    StructuralAnalysisResponse,
    TocExtractionResponse,
)
from core_shared.config import WhitepaperConfig
from modules.whitepaper.Table_of_content_extractor import WhitepaperExtractor
from modules.whitepaper.extractor import pdf_to_semantic_markdown, save_pipeline_outputs
from modules.whitepaper.sentiment_analysis import SectionAnalyzer
from modules.whitepaper.structural_analysis import compute_structural_metrics


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whitepaper", tags=["Whitepaper"])

_section_analyzer = SectionAnalyzer(output_dir=str(WhitepaperConfig.ANALYSIS_DIR))

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


# ---------------------------------------------------------------------------
# Registry helpers
# Temporary CSV-based persistence; will be replaced by database interactions.
# ---------------------------------------------------------------------------

def _append_to_registry(entry: dict) -> None:
    """Append a new entry to the CSV registry."""
    registry_path = WhitepaperConfig.REGISTRY_PATH
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    with FileLock(str(registry_path) + ".lock", timeout=10):
        df_new = pd.DataFrame([entry])
        if registry_path.exists() and registry_path.stat().st_size > 0:
            df = pd.concat([pd.read_csv(registry_path), df_new], ignore_index=True)
        else:
            df = df_new
        df.to_csv(registry_path, index=False)


def _update_analysis_to_registry(metrics: dict) -> None:
    """Update an existing registry row with computed metrics.

    Args:
        metrics: Dictionary of metrics including a ``uuid`` key identifying
            the row to update. A new row is appended if the UUID is absent.

    Raises:
        KeyError: If *metrics* does not contain a ``uuid`` key.
    """
    registry_path = WhitepaperConfig.REGISTRY_PATH
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    with FileLock(str(registry_path) + ".lock", timeout=10):
        if registry_path.exists() and registry_path.stat().st_size > 0:
            df = pd.read_csv(registry_path)
        else:
            df = pd.DataFrame()

        target_uuid = metrics.get("uuid")
        if not target_uuid:
            raise KeyError("The metrics dictionary does not contain a valid 'uuid' key.")

        if "uuid" in df.columns and target_uuid in df["uuid"].values:
            mask = df["uuid"] == target_uuid
            update_dict = {k: v for k, v in metrics.items() if k != "uuid"}
            df.loc[mask, update_dict.keys()] = pd.Series(update_dict)
        else:
            df = pd.concat([df, pd.DataFrame([metrics])], ignore_index=True)

        df.to_csv(registry_path, index=False)


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
    """Extract and persist a PDF whitepaper, returning its Markdown content."""
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
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            safe_filename = re.sub(r"[^\w\-.]", "_", file.filename)
            pdf_path = temp_dir_path / safe_filename
            output_md = temp_dir_path / "output.md"
            img_dir = temp_dir_path / "images_tmp"

            pdf_path.write_bytes(file_content)

            markdown_content = await asyncio.to_thread(
                pdf_to_semantic_markdown,
                pdf_path=str(pdf_path),
                output_md=str(output_md),
                img_dir=str(img_dir),
                extract_images=extract_images,
            )

            generated_uuid = str(uuid.uuid4())

            final_pdf_path = WhitepaperConfig.PDF_DIR / f"{generated_uuid}.pdf"
            final_md_path = WhitepaperConfig.MD_DIR / f"{generated_uuid}.md"
            final_img_dir = WhitepaperConfig.IMG_DIR / generated_uuid

            for p in [final_pdf_path, final_md_path, final_img_dir]:
                p.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(src=pdf_path, dst=final_pdf_path)

            save_status = save_pipeline_outputs(
                md_content=markdown_content,
                final_md_path=str(final_md_path),
                temp_img_dir=str(img_dir),
                final_img_dir=str(final_img_dir),
            )

            if not save_status:
                raise HTTPException(status_code=500, detail="Failed to persist output files.")

            _append_to_registry({
                "uuid": generated_uuid,
                "project_name": (project_name or Path(file.filename).stem).strip() or "Unknown",
                "filename": file.filename,
                "file_size_mb": round(len(file_content) / (1024 * 1024), 2),
                "status": "success",
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "marked_for_deletion": not save_markdown,
            })

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
        await asyncio.to_thread(_update_analysis_to_registry, metrics=metrics)

        return StructuralAnalysisResponse(
            status="success",
            uuid=doc_uuid,
            metrics=metrics,
            saved_to_registry=True,
        )

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
        output_dir=WhitepaperConfig.TOCS_DIR,
    )

    try:
        sections = await asyncio.to_thread(
            extractor.extract,
            uuid=doc_uuid,
            use_llm=True,
        )

        toc_data = "".join(
            f"{'  ' * (s.level - 1)}{'#' * s.level} {s.title}  (p.{s.page})\n"
            for s in sections
        )

        return TocExtractionResponse(
            status="success",
            uuid=doc_uuid,
            toc_content=toc_data,
        )

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

        return SentimentAnalysisResponse(
            status="success",
            uuid=doc_uuid,
            analyses=payload,  # type: ignore[arg-type]
            saved_to_registry=True,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Sentiment analysis failed for %s: %s", doc_uuid, e)
        raise HTTPException(
            status_code=500,
            detail="Internal error during sentiment analysis.",
        )