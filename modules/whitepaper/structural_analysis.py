import re
import logging

import textstat # type: ignore[import]

from core_shared.config import WhitepaperConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level patterns
# ---------------------------------------------------------------------------

_AI_DESC_PATTERN = re.compile(
    r"<AI img description>.*?</AI img description>",
    re.DOTALL
)
_OMITTED_PICTURE_PATTERN = re.compile(
    r"\*\*==>\s*picture\s*\[\d+\s*x\s*\d+\]\s*intentionally\s*omitted\s*<==\*\*"
)
_UUID_V4_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)

# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def _clean_text_for_nlp(md_content: str) -> str:
    """Strip structural noise from Markdown content before NLP analysis.

    Args:
        md_content: Raw Markdown string to clean.

    Returns:
        A plain-text string with images, links, and Markdown syntax removed.
    """
    text = _AI_DESC_PATTERN.sub("", md_content)
    text = _OMITTED_PICTURE_PATTERN.sub("", text)
    text = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^\)]*\)", r"\1", text)
    text = re.sub(r"[|#*`\-_]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

# ---------------------------------------------------------------------------
# Structural metrics
# ---------------------------------------------------------------------------

def compute_structural_metrics(uuid: str, include_images_stats: bool = True) -> dict:
    """Compute structural metrics on the cleaned text of a whitepaper document.

    Args:
        uuid: UUID v4 identifier of the document to analyse.
        include_images_stats: When ``True``, image count and total size are
            included in the returned dictionary; ``None`` values are used when
            the image directory does not exist.

    Returns:
        A dictionary of structural metrics keyed by metric name, including
        the document UUID.

    Raises:
        ValueError: If *uuid* does not match the UUID v4 format.
        FileNotFoundError: If no Markdown file exists for the given UUID.
    """
    if not _UUID_V4_PATTERN.fullmatch(uuid):
        raise ValueError(f"Invalid UUID format : {uuid!r}")
    
    md_path = WhitepaperConfig.MD_DIR / f"{uuid}.md"
    img_dir = WhitepaperConfig.IMG_DIR / uuid

    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found for UUID: {uuid}")

    md_content = md_path.read_text(encoding="utf-8")
    clean_text = _clean_text_for_nlp(md_content)
    words = clean_text.split()
    word_count = len(words)
    text_size_bytes = len(md_content.encode("utf-8"))

    sentence_count: int = 0
    syllable_count: int = 0
    gunning_fog: float = 0.0
    flesch_reading_ease: float = 0.0

    if word_count > 0:
        try:
            sentence_count = textstat.sentence_count(clean_text)                     # type: ignore[assignment]
            syllable_count = textstat.syllable_count(clean_text)                     # type: ignore[assignment]
            gunning_fog = textstat.gunning_fog(clean_text)                           # type: ignore[assignment]
            flesch_reading_ease = textstat.flesch_reading_ease(clean_text)           # type: ignore[assignment]
        except Exception as e: # noqa: BLE001
            logger.warning("textstat failed for UUID %s: %s", uuid, e)

    avg_word_len = (
        round(sum(len(w) for w in words) / word_count, 2) if word_count > 0 else 0.0
    )   

    img_stats: dict = {} 
    if include_images_stats:
        if img_dir.exists():
            img_files = [f for f in img_dir.iterdir() if f.is_file()]
            img_stats = {
                "image_count": len(img_files),
                "images_total_size_bytes": sum(f.stat().st_size for f in img_files),
            }
        else:
            img_stats = {
                "image_count": None,
                "images_total_size_bytes": None,
            }
    return {
        "uuid": uuid,
        "text_size_bytes": text_size_bytes,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "syllable_count": syllable_count,
        "avg_word_length": avg_word_len,
        "gunning_fog_index": round(gunning_fog, 2) if gunning_fog > 0 else None,
        "flesch_reading_ease": round(flesch_reading_ease, 2) if flesch_reading_ease > 0 else None,
        **img_stats,
    }
