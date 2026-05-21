from fastapi import  APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pathlib import Path
import tempfile
import shutil

from modules.whitepaper.extractor import pdf_to_semantic_markdown

router = APIRouter(prefix="/whitepaper", tags=["Whitepaper"])

class ExtractionResponse(BaseModel):
    status: str
    extract_images: bool
    markdown_content: str

@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: UploadFile = File(...),
    extract_images: bool = Form(True) # True par défaut, contrôlable via la requête
):
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Le fichier doit être un format PDF valide.")

    # Isolation de l'exécution dans un dossier temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        pdf_path = temp_dir_path / file.filename
        output_md = temp_dir_path / "output.md"
        img_dir = temp_dir_path / "images_tmp"

        # Sauvegarde du flux binaire
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            # Exécution du pipeline
            markdown_content = pdf_to_semantic_markdown(
                pdf_path=str(pdf_path),
                output_md=str(output_md),
                img_dir=str(img_dir),
                extract_images=extract_images
            )

            return ExtractionResponse(
                status="success",
                extract_images=extract_images,
                markdown_content=markdown_content
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du traitement: {str(e)}")