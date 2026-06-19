import re
import shutil
from pathlib import Path
import logging

import ollama
import pymupdf4llm

from core_shared.config import WhitepaperConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Image description
# ---------------------------------------------------------------------------

def describe_image_with_ollama(image_path: str) -> str:
    """Send an image to Ollama and return its generated description.

    Args:
        image_path: Absolute or relative path to the image file.

    Returns:
        A short, structured description produced by the vision model.
    """
    system_prompt = """
    You are a precise document analyst. When describing images for text documents, follow these rules:
    1. Start with the image type (Graph, Schema, Diagram, Screenshot, Photo, Table, etc.)
    2. Provide a concise but complete description.
    3. Focus on factual, structural elements.
    4. Use neutral, professional language.
    5. Keep descriptions to 2-3 sentences maximum.

    Examples:
    - "[Graph]: A line chart comparing Bitcoin price evolution from 2020 to 2024, showing a sharp
      increase in 2021 followed by a correction period and gradual recovery."
    - "[Schema]: An organizational flowchart showing the company hierarchy with CEO at top,
      followed by CTO, CFO, and CMO divisions, each managing 3-4 department heads."
    - "[Table]: A data table with 4 columns listing transaction IDs, timestamps, amounts in BTC,
      and wallet addresses for the last 10 blockchain transactions."
    - "[Diagram]: A technical architecture diagram illustrating a 3-tier web application with
      load balancer, application servers, and database cluster."
    - "[Photo]: A screenshot of a cryptocurrency trading dashboard displaying real-time price
      charts, order book, and portfolio balance."
    - "[Schema]: A Venn diagram showing the overlap between machine learning, deep learning, and
      neural networks, with specific algorithms listed in each intersection.
      """
    # Requires a vision-capable model, e.g. 'llava' or 'llama3.2-vision'.
    response = ollama.chat(
        model=WhitepaperConfig.LLM_MODEL_VISION,
        messages=[
        {
            'role': 'system',
            'content': system_prompt
        },
        {
            'role': 'user',
            'content': "Give a brief description of the image so it can be included in a text document.",
            'images': [image_path]
        }]
    )
    content = response["message"]["content"]
    if not isinstance(content, str):
        raise TypeError(f"Unexpected content type from Ollama: {type(content)}")
    return content

def _replace_image_with_description(match: re.Match[str]) -> str:
    """Replace a Markdown image tag with an AI-generated description via Ollama."""
    img_path = match.group(1)
    logger.info("Analyzing image: %s via Ollama...", img_path)

    try:
        description = describe_image_with_ollama(img_path)
        return (
            f"\n<AI img description>\n"
            f"*{description.strip()}*\n"
            f"</AI img description>\n"
        )
    except Exception as e:
        return f"\n> *[Error while analysing image: {e}]*\n"

# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------


def pdf_to_semantic_markdown(
        pdf_path: str,
        output_md: str,
        img_dir: str = "images_tmp",
        extract_images: bool = True,
) -> str:
    """Convert a PDF file to semantic Markdown, optionally replacing images with AI descriptions.

    Args:
        pdf_path: Path to the source PDF file.
        output_md: Destination path for the generated Markdown file.
        img_dir: Directory used to store extracted images temporarily.
            Only created when *extract_images* is ``True``.
        extract_images: When ``True``, images are extracted and described by
            the Ollama vision model; when ``False``, image tags are left as-is.

    Returns:
        The final Markdown content as a string.
    """
    if extract_images:
        Path(img_dir).mkdir(parents=True, exist_ok=True)
    
    md_text= pymupdf4llm.to_markdown( # type: ignore[assignment]
        pdf_path,
        write_images=extract_images,
        image_path=img_dir if extract_images else None,
        image_format="png",
        force_text=False
    )
    
    if extract_images:
        img_pattern = re.compile(r'!\[.*?\]\((.*?)\)')
        final_md_text: str = img_pattern.sub(_replace_image_with_description, md_text) # type: ignore[arg-type]
    else:
        final_md_text = md_text # type: ignore[assignment]
    Path(output_md).write_text(final_md_text, encoding="utf-8")
    return final_md_text #type:ignore[return-value]

def save_pipeline_outputs(
        md_content: str,
        final_md_path: str,
        temp_img_dir: str,
        final_img_dir: str,
) -> bool:
    """Persist Markdown content and move the temporary image directory to permanent storage.

    Args:
        md_content: Markdown string to write to disk.
        final_md_path: Destination path for the Markdown file.
        temp_img_dir: Path to the temporary image directory produced during extraction.
        final_img_dir: Target path in the datalake where images should be stored permanently.

    Returns:
        ``True`` on success, ``False`` if any I/O error occurs.
    """
    try:
        md_path = Path(final_md_path)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md_content, encoding="utf-8")

        source_imgs = Path(temp_img_dir)
        target_imgs = Path(final_img_dir)

        if (
            source_imgs.exists()
            and source_imgs.is_dir()
            and any(source_imgs.iterdir())
            ):

            if target_imgs.exists():
                shutil.rmtree(target_imgs)
            target_imgs.parent.mkdir(parents=True, exist_ok=True)

            shutil.copytree(source_imgs, target_imgs)

        return True
    except Exception as e:
        logger.error("Error while saving pipeline outputs: %s", e)
        return False