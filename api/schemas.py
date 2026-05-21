from pydantic import BaseModel
from typing import Optional

class AnalysisRequest(BaseModel):
    question: str
    model_name: str = "qwen3.5:9b"

class AnalysisResponse(BaseModel):
    status: str
    markdown_content: Optional[str] = None
    analysis_result: Optional[str] = None
    error: Optional[str] = None