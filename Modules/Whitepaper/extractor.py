import pymupdf4llm
from pathlib import Path
import re
import ollama


def describe_image_with_ollama(image_path: str) -> str:
    """Envoie l'image à Ollama et retourne sa description."""
    
    system_prompt = """
    You are a precise document analyst. When describing images for text documents, follow these rules:
    1. Start with the image type (Graph, Schema, Diagram, Screenshot, Photo, Table, etc.)
    2. Provide a concise but complete description
    3. Focus on factual, structural elements
    4. Use neutral, professional language
    5. Keep descriptions to 2-3 sentences maximum

    Examples:
    - "[Graph]: A line chart comparing Bitcoin price evolution from 2020 to 2024, showing a sharp increase in 2021 followed by a correction period and gradual recovery."
    - "[Schema]: An organizational flowchart showing the company hierarchy with CEO at top, followed by CTO, CFO, and CMO divisions, each managing 3-4 department heads."
    - "[Table]: A data table with 4 columns listing transaction IDs, timestamps, amounts in BTC, and wallet addresses for the last 10 blockchain transactions."
    - "[Diagram]: A technical architecture diagram illustrating a 3-tier web application with load balancer, application servers, and database cluster."
    - "[Photo]: A screenshot of a cryptocurrency trading dashboard displaying real-time price charts, order book, and portfolio balance."
    - "[Schema]: A Venn diagram showing the overlap between machine learning, deep learning, and neural networks, with specific algorithms listed in each intersection."
"""
    # Assurez-vous d'avoir téléchargé un modèle vision, ex: 'llava' ou 'llama3.2-vision'
    response = ollama.chat(
        model='gemma4:31b-cloud',
        messages=[
            {
            'role': 'system',
            'content': system_prompt
        }, {
            'role': 'user',
            'content': "Give a brief description of the image so it can be included in a text document.",
            'images': [image_path] # Ollama gère directement les chemins de fichiers !
        }]
    )
    return response['message']['content']

def replace_with_description(match: re.Match) -> str:
    img_path = match.group(1)
    print(f"Analyse de l'image : {img_path} via Ollama...")
    
    try:
        description = describe_image_with_ollama(img_path)
        # On formate la description pour qu'elle se démarque dans le Markdown
        return f"""\n <AI img description>\n*{description.strip()}*\n</AI img description>\n"""
    except Exception as e:
        return f"\n> *[Erreur lors de l'analyse de l'image : {e}]*\n"
    
def pdf_to_semantic_markdown(pdf_path: str, output_md: str, img_dir: str = "images_tmp", extract_images: bool = True) -> str:
    if extract_images:
        Path(img_dir).mkdir(parents=True, exist_ok=True)
    
    # 1. Extraction conditionnelle
    md_text = pymupdf4llm.to_markdown(
        pdf_path,
        write_images=extract_images,
        image_path=img_dir if extract_images else None,
        image_format="png",
        force_text=False
    )
    
    # 2. Substitution conditionnelle
    if extract_images:
        img_pattern = re.compile(r'!\[.*?\]\((.*?)\)')
        final_md_text = img_pattern.sub(replace_with_description, md_text) #type:ignore
    else:
        final_md_text = md_text
    
    # 3. Sauvegarde et retour
    Path(output_md).write_text(final_md_text, encoding="utf-8") #type:ignore
    return final_md_text #type:ignore