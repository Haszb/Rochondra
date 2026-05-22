from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pathlib import Path
import tempfile
import uuid
import pandas as pd
from datetime import datetime
import shutil

from core_shared.config import WhitepaperConfig
from modules.whitepaper.extractor import pdf_to_semantic_markdown, save_pipeline_outputs

router = APIRouter(prefix="/whitepaper", tags=["Whitepaper"])

class ExtractionResponse(BaseModel):
    status: str
    extract_images: bool
    save_markdown: bool = False
    doc_uuid: str = ""  # On ajoute l'UUID dans la réponse pour le client
    markdown_content: str

@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: UploadFile = File(...),
    extract_images: bool = Form(...),
    save_markdown: bool = Form(...)
):
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Le fichier doit être un format PDF valide.")

    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Impossible de lire le fichier : {str(e)}")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            pdf_path = temp_dir_path / file.filename
            output_md = temp_dir_path / "output.md"
            img_dir = temp_dir_path / "images_tmp"

            pdf_path.write_bytes(file_content)

            markdown_content = pdf_to_semantic_markdown(
                pdf_path=str(pdf_path),
                output_md=str(output_md),
                img_dir=str(img_dir),
                extract_images=extract_images
            )
            # Initialisation de la variable pour la réponse JSON
            generated_uuid = ""

            if save_markdown:
                # 1. Génération de l'identifiant unique immuable
                generated_uuid = str(uuid.uuid4())
                
                # 2. Définition des chemins du Datalake basés sur l'UUID
                final_pdf_path = WhitepaperConfig.PDF_DIR / f"{generated_uuid}.pdf"
                final_md_path = WhitepaperConfig.MD_DIR / f"{generated_uuid}.md"
                final_img_dir = WhitepaperConfig.IMG_DIR / generated_uuid

                final_pdf_path.parent.mkdir(parents=True, exist_ok=True)
                final_md_path.parent.mkdir(parents=True, exist_ok=True)
                final_img_dir.parent.mkdir(parents=True, exist_ok=True)

                # 3. Écriture du PDF brut
                shutil.copy2(src=pdf_path, dst=final_pdf_path)

                # 4. Écriture du Markdown et déplacement du dossier d'images
                save_status = save_pipeline_outputs(
                    md_content=markdown_content,
                    final_md_path=str(final_md_path),
                    temp_img_dir=str(img_dir),
                    final_img_dir=str(final_img_dir)
                )
                
                if save_status == 0:
                    # 5. Extraction des métadonnées basiques pour le registre
                    project_name = Path(file.filename).stem.split('_')[0].capitalize()
                    file_size_mb = round(len(file_content) / (1024 * 1024), 2)
                    
                    new_entry = {
                        "uuid": generated_uuid,
                        "project_name": project_name,
                        "filename": file.filename,
                        "file_size_mb": file_size_mb,
                        "status": "success",
                        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 6. Mise à jour du fichier CSV (Index / Data Mart temporaire)
                    registry_path = WhitepaperConfig.REGISTRY_PATH
                    if registry_path.exists():
                        df = pd.read_csv(registry_path)
                        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                    else:
                        df = pd.DataFrame([new_entry])
                        
                    df.to_csv(registry_path, index=False)
                else:
                    print("[WARNING] Échec de la persistance des fichiers.")

            return ExtractionResponse(
                status="success",
                extract_images=extract_images,
                save_markdown=save_markdown,
                doc_uuid=generated_uuid,
                markdown_content=markdown_content
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement: {str(e)}")