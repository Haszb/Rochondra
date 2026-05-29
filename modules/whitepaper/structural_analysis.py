# modules/whitepaper/structural_analysis.py
import re
import textstat
from core_shared.config import WhitepaperConfig

_AI_DESC_PATTERN = re.compile(r'<AI img description>.*?</AI img description>', re.DOTALL)
_NO_IMG_SAVED_IN_OLLAMA = re.compile(r'\*\*==>\s*picture\s*\[\d+\s*x\s*\d+\]\s*intentionally\s*omitted\s*<==\*\*')

def _clean_text_for_nlp(md_content: str) -> str:
    """Prépare le texte pour les analyses NLP en supprimant la pollution structurelle."""
    text = _AI_DESC_PATTERN.sub('', md_content)
    text = _NO_IMG_SAVED_IN_OLLAMA.sub('', text)
    text = re.compile(r'!\[[^\]]*\]\([^\)]*\)').sub('', text)
    text = re.compile(r'\[([^\]]*)\]\([^\)]*\)').sub(r'\1', text)
    text = re.compile(r'[|#*`\-_]').sub(' ', text)
    return re.compile(r'\s+').sub(' ', text).strip()

def compute_structural_metrics(uuid: str, include_images_stats: bool = True) -> dict:
    """
    Calcule les métriques structurelles sur le texte épuré du document.
    Renvoie un dictionnaire incluant l'UUID du document traité.
    """
    md_path = WhitepaperConfig.MD_DIR / f"{uuid}.md"
    img_dir = WhitepaperConfig.IMG_DIR / uuid

    if not md_path.exists():
        raise FileNotFoundError(f"Markdown introuvable pour UUID: {uuid}")

    md_content = md_path.read_text(encoding="utf-8")
    clean_text = _clean_text_for_nlp(md_content)
    
    words = clean_text.split()
    word_count = len(words)
    text_size_bytes = len(md_content.encode("utf-8"))

    gunning_fog, flesch_reading_ease, sentence_count, syllable_count = 0.0, 0.0, 0, 0

    if word_count > 0:
        try:
            sentence_count = textstat.sentence_count(clean_text) #type:ignore (just pylance shenigans)
            syllable_count = textstat.syllable_count(clean_text) #type:ignore
            gunning_fog = textstat.gunning_fog(clean_text) #type:ignore
            flesch_reading_ease = textstat.flesch_reading_ease(clean_text) #type:ignore
        except Exception as nlp_err:
            # Remplacement du print par un log si nécessaire, ou maintien du warning
            print(f"[WARNING] Échec textstat sur l'UUID {uuid} : {nlp_err}")

    total_chars_in_words = sum(len(word) for word in words)
    avg_word_len = round(total_chars_in_words / word_count, 2) if word_count > 0 else 0.0

    img_stats = {}
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
        "uuid": uuid,  # <-- L'UUID est nativement ancré ici
        "text_size_bytes": text_size_bytes,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "syllable_count": syllable_count,
        "avg_word_length": avg_word_len,
        "gunning_fog_index": round(gunning_fog, 2),
        "flesch_reading_ease": round(flesch_reading_ease, 2),
        **img_stats,
    }