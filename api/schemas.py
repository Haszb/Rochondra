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
    metrics: dict
    saved_to_registry: bool = True

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
    saved_to_registry: bool = False
# ************************************************************************    