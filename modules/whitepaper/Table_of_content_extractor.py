import pymupdf
import os
import re
import json
from statistics import mode
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
import ollama
from core_shared.config import WhitepaperConfig


# ==========================================
# STRUCTURES DE DONNÉES
# ==========================================

@dataclass
class LineCandidate:
    """
    Représente une ligne reconstruite avec ses métadonnées
    et les signaux qui l'ont qualifiée comme candidat titre.
    """
    text: str
    page: int
    size: float
    is_bold: bool
    n_words: int
    signals: list[str] = field(default_factory=list)
    level: Optional[int] = None


@dataclass
class Section:
    """Section finale avec titre, niveau hiérarchique et page."""
    title: str
    level: int
    page: int
    content: str = ""
    children: list["Section"] = field(default_factory=list)


# ==========================================
# EXTRACTEUR PRINCIPAL
# ==========================================

class WhitepaperExtractor:
    """
    Pipeline d'extraction de structure pour whitepapers crypto.

    Stratégie en cascade :
        1. Sommaire natif PDF       (rapide, fiable si présent)
        2. Heuristique visuelle     (polices, tailles, flags)
        3. LLM arbitre              (Gemma sur les candidats ambigus)
        4. Fallback heuristique brut (si LLM échoue)

    Chaque résultat est sauvegardé en JSON + Markdown dans output_dir.
    Les fichiers déjà traités sont ignorés (skip logic).
    """

    # Polices parasites à exclure systématiquement
    EXCLUDE_FONTS = {"CourierNewPSMT", "OpenSymbol", "Courier", "CourierNew"}

    # Numérotation : "1.", "1.1", "1.1.1", "A.", "I.", "a)"
    SECTION_NUMBER_PATTERN = re.compile(
        r'^\s*(\d+(\.\d+)*\.?|[A-Z]\.?|[IVXivx]+\.?)\s*$'
    )

    # Exclusions inconditionnelles
    EXCLUDE_PATTERNS = [
        re.compile(r'^0x[a-fA-F0-9]{10,}'),   # adresses crypto
        re.compile(r'https?://'),               # URLs
        re.compile(r'[{}]'),                    # code
        re.compile(r'^\s*[\*\-\•]\s'),         # listes à puces
        re.compile(r'^\w[\w\s]*\s*:\s+0x'),    # "CA: 0x..."
        re.compile(r'^\d+[\.,]\d+\s*%'),       # pourcentages
    ]

    def __init__(
        self,
        llm_model: str = "gemma4:31b-cloud",
        output_dir: Optional[str] = None,
        llm_temperature: float = 0.0,
        body_size_cap: float = 15.0,
        size_ratio_h1: float = 1.5,
        size_ratio_h2: float = 1.15,
        max_title_words: int = 12,
        min_toc_entries: int = 5,
    ):
        self.llm_model       = llm_model
        self.llm_temperature = llm_temperature
        self.body_size_cap   = body_size_cap
        self.size_ratio_h1   = size_ratio_h1
        self.size_ratio_h2   = size_ratio_h2
        self.max_title_words = max_title_words
        self.min_toc_entries = min_toc_entries

        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------
    # PERSISTENCE
    # ------------------------------------------

    def _already_processed(self, uuid: str) -> bool:
        if not self.output_dir:
            return False
        return (self.output_dir / f"{uuid}.json").exists()

    def _save(self, uuid: str, sections: list[Section]) -> None:
        if not self.output_dir:
            return

        # JSON — pour le pipeline downstream
        json_data = [
            {"title": s.title, "level": s.level, "page": s.page}
            for s in sections
        ]
        with open(self.output_dir / f"{uuid}.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        # Markdown — pour la lisibilité humaine
        md_lines = [f"# Table des matières : {uuid}\n"]
        for s in sections:
            indent = "  " * (s.level - 1)
            md_lines.append(f"{indent}{'#' * s.level} {s.title}  (p.{s.page})")
        with open(self.output_dir / f"{uuid}.md", "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

    def _load(self, uuid: str) -> list[Section]:
        if not self.output_dir:
            return []
        with open(self.output_dir / f"{uuid}.json", encoding="utf-8") as f:
            data = json.load(f)
        return [
            Section(title=d["title"], level=d["level"], page=d["page"])
            for d in data
        ]

    # ------------------------------------------
    # ÉTAPE 0 : Sommaire natif PDF
    # ------------------------------------------

    def _get_native_toc(self, doc: pymupdf.Document) -> Optional[list[Section]]:
        try:
            toc = doc.get_toc()
            if toc and len(toc) >= self.min_toc_entries:
                sections = []
                for level, title, page_num in toc:
                    clean_title = " ".join(title.split())
                    if clean_title:
                        sections.append(Section(
                            title=clean_title,
                            level=min(level, 3),
                            page=page_num
                        ))
                return sections
        except Exception:
            pass
        return None

    # ------------------------------------------
    # ÉTAPE 1 : Taille modale du corps de texte
    # ------------------------------------------

    def _get_body_size(self, doc: pymupdf.Document) -> float:
        all_sizes = []
        for page_num in range(min(10, len(doc))):
            page = doc[page_num]
            for block in page.get_text("dict").get("blocks", []):  # type: ignore[index]
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        size = round(span["size"], 1)
                        if size <= self.body_size_cap:
                            all_sizes.append(size)
        return mode(all_sizes) if all_sizes else 10.0
    # ------------------------------------------
    # ÉTAPE 2 : Reconstruction des lignes
    # ------------------------------------------

    def _reconstruct_lines(self, doc: pymupdf.Document) -> list[dict]:
        lines_data = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            for block in page.get_text("dict").get("blocks", []): #type:ignore
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    spans = line["spans"]
                    if not spans:
                        continue

                    full_text = "".join(s["text"] for s in spans).strip()
                    if not full_text:
                        continue

                    clean_spans = [
                        s for s in spans
                        if s["font"] not in self.EXCLUDE_FONTS
                    ]
                    if not clean_spans:
                        continue

                    # Span dominant = le plus long = le plus représentatif
                    dominant = max(clean_spans, key=lambda s: len(s["text"]))

                    lines_data.append({
                        "page":    page_num + 1,
                        "text":    full_text,
                        "font":    dominant["font"],
                        "size":    round(dominant["size"], 1),
                        "flags":   dominant["flags"],
                        "is_bold": bool(dominant["flags"] & (1 << 4)),
                        "n_words": len(full_text.split()),
                    })
        return lines_data

    # ------------------------------------------
    # ÉTAPE 3 : Qualification des candidats
    # ------------------------------------------

    def _is_excluded(self, text: str) -> bool:
        return any(p.search(text) for p in self.EXCLUDE_PATTERNS)

    def _get_candidates(
        self,
        lines: list[dict],
        body_size: float
    ) -> list[LineCandidate]:
        candidates = []

        for line in lines:
            text = line["text"].strip()
            if not text or self._is_excluded(text):
                continue

            signals = []

            # Signaux forts — suffisants seuls
            if line["is_bold"] and line["size"] > body_size:
                signals.append("bold_large")

            if line["size"] >= body_size * self.size_ratio_h1:
                signals.append("size_h1")

            if line["size"] >= body_size * self.size_ratio_h2:
                signals.append("size_h2")

            # Signaux faibles — nécessitent combinaison
            if line["n_words"] <= 6:
                signals.append("short")

            if not text.endswith(('.', ',', ';', ':')):
                signals.append("no_punctuation")

            if text.isupper() and len(text) > 2:
                signals.append("all_caps")

            if line["is_bold"]:
                signals.append("bold")

            if bool(self.SECTION_NUMBER_PATTERN.match(text)):
                signals.append("numbered")

            # Règle de qualification
            has_strong = any(s in signals for s in (
                "bold_large", "size_h1", "size_h2"
            ))
            weak_count = sum(1 for s in signals if s in (
                "short", "no_punctuation", "all_caps", "bold", "numbered"
            ))
            has_weak_combo = weak_count >= 3

            if not (has_strong or has_weak_combo):
                continue

            if line["n_words"] > self.max_title_words:
                continue

            candidates.append(LineCandidate(
                text=text,
                page=line["page"],
                size=line["size"],
                is_bold=line["is_bold"],
                n_words=line["n_words"],
                signals=signals,
            ))

        return candidates

    # ------------------------------------------
    # ÉTAPE 4 : Fusion des fragments
    # ------------------------------------------

    def _merge_fragments(
        self,
        candidates: list[LineCandidate]
    ) -> list[LineCandidate]:
        merged = []
        skip_next = False

        for i, line in enumerate(candidates):
            if skip_next:
                skip_next = False
                continue

            is_fragment = bool(
                self.SECTION_NUMBER_PATTERN.match(line.text.strip())
            )

            if is_fragment and i + 1 < len(candidates):
                next_line = candidates[i + 1]
                next_is_fragment = bool(
                    self.SECTION_NUMBER_PATTERN.match(next_line.text.strip())
                )
                if (next_line.page == line.page
                        and abs(next_line.size - line.size) <= 1.5
                        and not next_is_fragment):
                    merged.append(LineCandidate(
                        text=f"{line.text.strip()} {next_line.text.strip()}",
                        page=line.page,
                        size=line.size,
                        is_bold=line.is_bold,
                        n_words=line.n_words + next_line.n_words,
                        signals=list(set(line.signals + next_line.signals)),
                    ))
                    skip_next = True
                    continue

            merged.append(line)

        return merged

    # ------------------------------------------
    # ÉTAPE 5 : Inférence des niveaux hiérarchiques
    # ------------------------------------------

    def _infer_levels(
        self,
        candidates: list[LineCandidate],
        body_size: float
    ) -> list[LineCandidate]:
        for c in candidates:
            ratio = c.size / body_size
            if ratio >= self.size_ratio_h1 or (c.is_bold and ratio >= 1.3):
                c.level = 1
            elif ratio >= self.size_ratio_h2 or c.is_bold:
                c.level = 2
            else:
                c.level = 3
        return candidates

    # ------------------------------------------
    # ÉTAPE 6 : Arbitrage LLM
    # ------------------------------------------

    def _build_llm_prompt(self, candidates: list[LineCandidate]) -> str:
        lines = []
        for c in candidates:
            signals_str = ",".join(c.signals)
            lines.append(
                f"[p{c.page}|L{c.level}|{c.size}pt|{signals_str}] {c.text}"
            )
        return "\n".join(lines)

    def _call_llm(
        self,
        candidates: list[LineCandidate]
    ) -> Optional[list[Section]]:
        prompt_content = self._build_llm_prompt(candidates)

        system_prompt = """
        You are a document structure analyzer for crypto whitepapers.
        You receive a list of title candidates extracted from a PDF, with metadata:
        [page|level_hint|size|signals] text
        
        Your task:
        1. Confirm which lines are real section titles (remove false positives)
        2. Assign the correct hierarchy level (1, 2 or 3)
        3. Return ONLY valid JSON, no markdown, no explanation
        
        Output format:
        [
            {"title": "1. Introduction", "level": 1, "page": 2},
            {"title": "1.1 Background",  "level": 2, "page": 2}
        ]
        
        Rules:
        - Numbered sections like "1.", "1.1" are strong signals
        - Short bold lines are likely titles
        - Ignore addresses, URLs, percentages, bullet points
        - Use relative size to infer hierarchy when numbering is absent
        """

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": prompt_content}
                ],
                options={
                    "temperature": self.llm_temperature,
                    "num_predict": 2048,
                }
            )
            raw = response["message"]["content"].strip()

            raw = re.sub(r'```json\s*|\s*```', '', raw).strip()

            start = raw.find('[')
            end   = raw.rfind(']')
            if start == -1 or end == -1:
                return None
            
            data = json.loads(raw[start:end+1])
            return [
                Section(
                    title=item["title"],
                    level=item.get("level", 2),
                    page=item.get("page", 0)
                )
                for item in data
                if "title" in item
            ]


        except Exception as e:
            print(f"  LLM error: {e}")
            return None

    # ------------------------------------------
    # POINT D'ENTRÉE PUBLIC
    # ------------------------------------------

    def extract(
        self,
        uuid: str,
        use_llm: bool = True
    ) -> list[Section]:
        """
        Extrait le plan structuré d'un whitepaper PDF.

        Args:
            uuid : l'UUID du document
            use_llm  : si False, retourne le résultat heuristique brut

        Returns:
            Liste de Section(title, level, page)
        """
        pdf_path = WhitepaperConfig.PDF_DIR / f"{uuid}.pdf"
        # Skip si déjà traité
        if self._already_processed(uuid):
            print("skip (déjà traité)")
            return self._load(uuid)

        with pymupdf.open(pdf_path) as doc:

            # Voie 1 : sommaire natif
            native = self._get_native_toc(doc)
            if native:
                print(f"  natif ({len(native)} entrées)")
                self._save(uuid, native)
                return native

             # Voie 2 : heuristique
            body_size  = self._get_body_size(doc)
            lines      = self._reconstruct_lines(doc)
            candidates = self._get_candidates(lines, body_size)
            candidates = self._merge_fragments(candidates)
            candidates = self._infer_levels(candidates, body_size)


        if not use_llm or not candidates:
            sections = [
                Section(title=c.text, level=c.level or 2, page=c.page)
                for c in candidates
            ]
            self._save(uuid, sections)
            return sections

        # Voie 3 : arbitrage LLM
        print(f"  heuristique ({len(candidates)} candidats) → LLM...", end=" ", flush=True)
        sections = self._call_llm(candidates)

        # Fallback heuristique si LLM échoue
        if not sections:
            print("LLM échoué, fallback heuristique")
            sections = [
                Section(title=c.text, level=c.level or 2, page=c.page)
                for c in candidates
            ]

        self._save(uuid, sections)
        return sections


# ==========================================
# USAGE
# ==========================================

if __name__ == "__main__":

    WHITEPAPER_DIR = "/data/Whitepaper"
    OUTPUT_DIR     = "/data/Whitepaper/tocs"

    extractor = WhitepaperExtractor(
        llm_model="gemma4:31b-cloud",
        output_dir=OUTPUT_DIR,
    )

    pdf_files = sorted(
        f for f in os.listdir(WHITEPAPER_DIR)
        if f.lower().endswith(".pdf")
    )

    print(f"Traitement de {len(pdf_files)} fichiers\n")

    for filename in pdf_files:
        path = os.path.join(WHITEPAPER_DIR, filename)
        stem = Path(filename).stem
        print(f"{stem}", end="  ")

        sections = extractor.extract(path, use_llm=True)

        print(f"→ {len(sections)} sections")
        for s in sections:
            indent = "  " * (s.level - 1)
            print(f"  {indent}{'#' * s.level} {s.title}  (p.{s.page})")
        print()
