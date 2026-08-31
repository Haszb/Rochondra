from typing import Optional

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Whitepaper router schemas
# ---------------------------------------------------------------------------

class ExtractionResponse(BaseModel):
    """Response schema for the PDF extraction endpoint."""

    status: str
    extract_images: bool
    save_markdown: bool = False
    doc_uuid: Optional[str] = None
    markdown_content: str

class StructuralAnalysisResponse(BaseModel):
    """Response schema for the structural analysis endpoint."""

    status: str
    uuid: str
    metrics: dict[str, Optional[float | int | str]]

class TocExtractionResponse(BaseModel):
    """Response schema for the table of contents extraction endpoint."""
    
    status: str
    uuid: str
    toc_content: str


# **************************************************************************


class SectionAnalysisItem(BaseModel):
    word_count: int
    sentiment: str
    score: str
    resume: str


class SentimentAnalysisResponse(BaseModel):
    status: str
    uuid: str
    analyses: dict[str, SectionAnalysisItem]
# ************************************************************************


class ResumeSessionResponse(BaseModel):
    """Response schema for the resume-session endpoint.

    Always returns ``available_uuids`` so callers can display or refresh a
    picker; ``uuid`` is only set when a resume actually happened.
    """

    status: str
    uuid: Optional[str] = None
    available_uuids: list[str]


class FinalizeResponse(BaseModel):
    """Response schema for the finalize endpoint.

    ``action`` reports which branch ran (``saved`` or ``deleted``); the matching
    list holds the paths that were affected.
    """

    status: str
    uuid: str
    action: str
    persisted: list[str] = []
    deleted: list[str] = []
