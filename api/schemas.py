from pydantic import BaseModel
from typing import Optional


# Whitepaper_router schemas 

class ExtractionResponse(BaseModel):
    status: str
    extract_images: bool
    save_markdown: bool = False
    doc_uuid: Optional[str] = None
    markdown_content: str

class StructuralAnalysisResponse(BaseModel):
    status: str
    uuid: str
    metrics: dict
    saved_to_registry: bool = True

class TocExtractionResponse(BaseModel):
    status: str
    uuid: str
    toc_content: str