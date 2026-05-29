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


class AnalysisRequest(BaseModel):
    question: str
    model_name: str = "qwen3.5:9b"

class AnalysisResponse(BaseModel):
    status: str
    markdown_content: Optional[str] = None
    analysis_result: Optional[str] = None
    error: Optional[str] = None
