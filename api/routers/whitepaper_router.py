from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pathlib import Path
import tempfile
import uuid
import pandas as pd
from datetime import datetime, timezone
from filelock import FileLock
import re
import shutil
from typing import Optional
import asyncio
import logging

from core_shared.config import WhitepaperConfig
from modules.whitepaper.extractor import pdf_to_semantic_markdown, save_pipeline_outputs

router = APIRouter(prefix="/whitepaper", tags=["Whitepaper"])

logger = logging.getLogger(__name__)
_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 Mo

class ExtractionResponse(BaseModel):
    status: str
    extract_images: bool
    save_markdown: bool = False
    doc_uuid: Optional[str] = None  # On ajoute l'UUID dans la réponse pour le client
    markdown_content: str

# ---------------------------------------------------------------------------
# Registre CSV — point d'entrée unique, facile à remplacer par une DB plus tard
# ---------------------------------------------------------------------------
 
def _append_to_registry(entry: dict) -> None:
    """
    Écrit une entrée dans le registre CSV.
    Quand on passera à SQLite/PostgreSQL, seule cette fonction change.
    """
    registry_path = WhitepaperConfig.REGISTRY_PATH
    registry_path.parent.mkdir(parents=True, exist_ok=True)
 
    lock_path = str(registry_path) + ".lock"
    with FileLock(lock_path, timeout=10):
        df_new = pd.DataFrame([entry])
        if registry_path.exists():
            df = pd.concat([pd.read_csv(registry_path), df_new], ignore_index=True)
        else:
            df = df_new
        df.to_csv(registry_path, index=False)


@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: UploadFile = File(...),
    extract_images: bool = Form(...),
    save_markdown: bool = Form(...),
    project_name: str = Form(default=""),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant.")
    
    try:
        file_content = await file.read()
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier : {e}")
        raise HTTPException(status_code=400, detail= "Impossible de lire le fichier")
    
    if not file_content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Le contenu du fichier n'est pas un PDF valide.")


    if len(file_content) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"Fichier trop volumineux (max {_MAX_FILE_SIZE // (1024**2)} Mo).")

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
                extract_images=extract_images
            )
            # Initialisation de la variable pour la réponse JSON
            generated_uuid : Optional[str] = None

            if save_markdown:
                # 1. Génération de l'identifiant unique immuable
                generated_uuid = str(uuid.uuid4())
                
                # 2. Définition des chemins du Datalake basés sur l'UUID
                final_pdf_path = WhitepaperConfig.PDF_DIR / f"{generated_uuid}.pdf"
                final_md_path = WhitepaperConfig.MD_DIR / f"{generated_uuid}.md"
                final_img_dir = WhitepaperConfig.IMG_DIR / generated_uuid

                for p in [final_pdf_path, final_md_path, final_img_dir]:
                    p.parent.mkdir(parents=True, exist_ok=True)


                # 3. Écriture du PDF brut
                shutil.copy2(src=pdf_path, dst=final_pdf_path)

                # 4. Écriture du Markdown et déplacement du dossier d'images
                save_status = save_pipeline_outputs(
                    md_content=markdown_content,
                    final_md_path=str(final_md_path),
                    temp_img_dir=str(img_dir),
                    final_img_dir=str(final_img_dir)
                )
                
                if not save_status:
                    raise HTTPException(status_code=500, detail="Échec de la persistance des fichiers.")

                # 5. Enregistrement dans le registre CSV
                _append_to_registry({
                    "uuid": generated_uuid,
                    "project_name": (project_name or Path(file.filename).stem).strip() or "Unknown",
                    "filename": file.filename,
                    "file_size_mb": round(len(file_content)/ (1024*1024), 2),
                    "status": "success",
                    "analyzed_at" :datetime.now(timezone.utc).isoformat(),
                })



            return ExtractionResponse(
                status="success",
                extract_images=extract_images,
                save_markdown=save_markdown,
                doc_uuid=generated_uuid,
                markdown_content=markdown_content
            )

    except HTTPException:
        raise  # On laisse remonter les erreurs déjà formatées
    except Exception as e:
        logger.exception("Erreur inattendue lors du traitement du fichier %s", file.filename)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")
    
