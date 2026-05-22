import ollama
from pathlib import Path
from typing import List

def analyze_document_with_vision(question: str, image_paths: List[Path], model_name: str) -> str:
    """Envoie une question globale et les images au modèle de langage."""
    
    # Conversion des chemins Path en strings pour Ollama
    str_images = [str(img) for img in image_paths]
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{
                "role": "user",
                "content": question, # Strictement une chaîne de caractères
                "images": str_images # Liste des chemins des images
            }]
        )
        return response['message']['content']
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'analyse Ollama : {e}")