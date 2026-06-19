import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mode
from typing import Optional



import ollama
import pymupdf

from core_shared.config import WhitepaperConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class LineCandidate:
    """A reconstructed line with its metadata and heading qualification signals.

    Attributes:
        text: Cleaned text content of the line.
        page: Page number (1-indexed) where the line appears.
        size: Dominant font size of the line in points.
        is_bold: Whether the dominant span is bold.
        n_words: Number of words in the line.
        signals: List of qualification signals detected for this line.
        level: Inferred heading level (1, 2, or 3); ``None`` before inference.
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
    """A resolved document section with its title, hierarchy level, and page.

    Attributes:
        title: Cleaned section title.
        level: Heading level (1 = top-level, 2 = sub-section, 3 = sub-sub-section).
        page: Page number where the section starts.
        size: Font size of the heading in points.
        content: Optional body text associated with the section.
    """
    title: str
    level: int
    page: int
    size: float = 0.0

# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

class WhitepaperExtractor:
    """
    Cascade pipeline for extracting document structure from crypto whitepapers.

    Extraction strategy:
        1. Native PDF table of contents  (fast, reliable when present)
        2. Visual heuristics             (font sizes, flags, signals)
        3. LLM arbitration               (Gemma on ambiguous candidates)
        4. Heuristic fallback            (if LLM fails)

    Each result is persisted as JSON and Markdown under ``output_dir``.
    Already-processed documents are skipped automatically.
    """
    # Noisy fonts excluded unconditionally from heading detection.
    EXCLUDE_FONTS = {"CourierNewPSMT", "OpenSymbol", "Courier", "CourierNew"}

    # Matches common section numbering: "1.", "1.1", "1.1.1", "A.", "I.", "a)".
    SECTION_NUMBER_PATTERN = re.compile(
        r"^\s*(\d+(\.\d+)*\.?|[A-Z]\.?|[IVXivx]+\.?)\s*$"
    )

    EXCLUDE_PATTERNS = [
    re.compile(r"^0x[a-fA-F0-9]{40}$"),                   # Remove Ethereum addresses
    re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}$"),  # Bitcoin addresses
    re.compile(r"https?://"),               
    re.compile(r"[{}]"),                   
    re.compile(r"^\s*[\*\-\•]\s"),         
    re.compile(r"^\w[\w\s]*\s*:\s+0x"),    
    re.compile(r"^\d+[\.,]\d+\s*%"),       
    ]

    def __init__(
        self,
        llm_model: str = WhitepaperConfig.LLM_MODEL,
        output_dir: Optional[str] = None,
        llm_temperature: float = 0.0,
        body_size_cap: float = 15.0,
        size_ratio_h1: float = 1.5,
        size_ratio_h2: float = 1.15,
        max_title_words: int = 12,
        min_toc_entries: int = 5,
    ):
        self.llm_model = llm_model
        self.llm_temperature = llm_temperature
        self.body_size_cap = body_size_cap
        self.size_ratio_h1 = size_ratio_h1
        self.size_ratio_h2 = size_ratio_h2
        self.max_title_words = max_title_words
        self.min_toc_entries = min_toc_entries

        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------------------------

    def _already_processed(self, uuid: str) -> bool:
        """Return ``True`` if a JSON result file already exists for the given UUID."""
        if not self.output_dir:
            return False
        return (self.output_dir / f"{uuid}.json").exists()

    def _save(self, uuid: str, sections: list[Section]) -> None:
        """Persist extracted sections to JSON and Markdown files."""
        if not self.output_dir:
            return

        json_data = [
            {"title": s.title, "level": s.level, "page": s.page, "size": s.size}
            for s in sections
        ]
        with open(self.output_dir / f"{uuid}.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        md_lines = [f"# Table of contents: {uuid}\n"]
        for s in sections:
            indent = "  " * (s.level - 1)
            md_lines.append(f"{indent}{'#' * s.level} {s.title}  (p.{s.page})")
        with open(self.output_dir / f"{uuid}.md", "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

    def _load(self, uuid: str) -> list[Section]:
        """Load previously persisted sections from the JSON file for the given UUID."""
        if not self.output_dir:
            return []
        with open(self.output_dir / f"{uuid}.json", encoding="utf-8") as f:
            data = json.load(f)
        return [
            Section(title=d["title"], level=d["level"], page=d["page"], size=d["size"])
            for d in data
        ]

    # ---------------------------------------------------------------------------
    # Native PDF table of contents
    # ---------------------------------------------------------------------------

    def _get_native_toc(self, doc: pymupdf.Document) -> Optional[list[Section]]:
        """Attempt to extract the table of contents from native PDF metadata.

        Args:
            doc: Open PyMuPDF document object.

        Returns:
            A list of :class:`Section` objects if a valid TOC is found and
            meets the minimum entry threshold, ``None`` otherwise.
        """
        try:
            toc = doc.get_toc()
            if not toc or len(toc) < self.min_toc_entries:
                return None

            lines = self._reconstruct_lines(doc)
            sections = []

            for level, title, page_num in toc:
                clean_title = " ".join(title.split())
                if not clean_title:
                    continue

                page_lines = [ln for ln in lines if ln["page"] == page_num]
                norm_title = " ".join(clean_title.lower().split())
                size = 0.0

                for line in page_lines:
                    if " ".join(line["text"].lower().split()) == norm_title:
                        size = line["size"]
                        break

                sections.append(Section(
                    title=clean_title,
                    level=min(level, 3),
                    page=page_num,
                    size=size,
                ))

            return sections

        except Exception:  # noqa: BLE001
            return None
        
    # ------------------------------------------------------------------
    # Modal body font size
    # ------------------------------------------------------------------

    def _get_body_size(self, doc: pymupdf.Document) -> float:
        """Estimate the modal body font size across the first ten pages.

        Args:
            doc: Open PyMuPDF document object.

        Returns:
            The most frequently occurring font size at or below ``body_size_cap``,
            or ``10.0`` if no eligible spans are found.
        """
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
    
    # ------------------------------------------------------------------
    # Line reconstruction
    # ------------------------------------------------------------------

    def _reconstruct_lines(self, doc: pymupdf.Document) -> list[dict]:
        """Reconstruct text lines with dominant span metadata from all pages.

        Args:
            doc: Open PyMuPDF document object.

        Returns:
            A list of dictionaries, each representing one line with keys
            ``page``, ``text``, ``font``, ``size``, ``flags``, ``is_bold``,
            and ``n_words``.
        """
        lines_data = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            for block in page.get_text("dict").get("blocks", []): # type: ignore[index]
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

                    dominant = max(clean_spans, key=lambda s: len(s["text"]))

                    lines_data.append({
                        "page": page_num + 1,
                        "text": full_text,
                        "font": dominant["font"],
                        "size": round(dominant["size"], 1),
                        "flags": dominant["flags"],
                        "is_bold": bool(dominant["flags"] & (1 << 4)),
                        "n_words": len(full_text.split()),
                    })
        return lines_data

    # ------------------------------------------------------------------
    # Candidate qualification
    # ------------------------------------------------------------------

    def _is_excluded(self, text: str) -> bool:
        """Return ``True`` if the line matches any unconditional exclusion pattern."""
        return any(p.search(text) for p in self.EXCLUDE_PATTERNS)

    def _get_candidates(
        self,
        lines: list[dict],
        body_size: float,
    ) -> list[LineCandidate]:
        """Filter and score lines to produce heading candidates.

        Args:
            lines: Reconstructed lines as returned by :meth:`_reconstruct_lines`.
            body_size: Modal body font size used as the baseline for size ratios.

        Returns:
            A list of :class:`LineCandidate` objects that passed the qualification rules.
        """
        candidates = []

        for line in lines:
            text = line["text"].strip()
            if not text or self._is_excluded(text):
                continue

            signals = []

            if line["is_bold"] and line["size"] > body_size:
                signals.append("bold_large")
            if line["size"] >= body_size * self.size_ratio_h1:
                signals.append("size_h1")
            if line["size"] >= body_size * self.size_ratio_h2:
                signals.append("size_h2")
            if line["n_words"] <= 6:
                signals.append("short")
            if not text.endswith((".", ",", ";", ":")):
                signals.append("no_punctuation")
            if text.isupper() and len(text) > 2:
                signals.append("all_caps")
            if line["is_bold"]:
                signals.append("bold")
            if bool(self.SECTION_NUMBER_PATTERN.match(text)):
                signals.append("numbered")

            has_strong = any(s in signals for s in (
                "bold_large", "size_h1", "size_h2"
            ))
            weak_count = sum(1 for s in signals if s in (
                "short", "no_punctuation", "all_caps", "bold", "numbered"
            ))

            if not (has_strong or weak_count >= 3):
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

    # ------------------------------------------------------------------
    # Fragment merging
    # ------------------------------------------------------------------

    def _merge_fragments(
        self,
        candidates: list[LineCandidate],
    ) -> list[LineCandidate]:
        """Merge orphaned numbering fragments with the following title line.

        A fragment is a line matching ``SECTION_NUMBER_PATTERN`` (e.g. ``"1."``).
        When immediately followed by a non-fragment line on the same page with
        a similar font size, the two are joined into a single candidate.

        Args:
            candidates: Raw candidate list as returned by :meth:`_get_candidates`.

        Returns:
            A new candidate list with fragments merged where applicable.
        """
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

    # ------------------------------------------------------------------
    # Hierarchy level inference
    # ------------------------------------------------------------------

    def _infer_levels(
        self,
        candidates: list[LineCandidate],
        body_size: float,
    ) -> list[LineCandidate]:
        """Assign heading levels (1, 2, or 3) to each candidate based on size and bold flag."""
        for c in candidates:
            ratio = c.size / body_size
            if ratio >= self.size_ratio_h1 or (c.is_bold and ratio >= 1.3):
                c.level = 1
            elif ratio >= self.size_ratio_h2 or c.is_bold:
                c.level = 2
            else:
                c.level = 3
        return candidates

    # ------------------------------------------------------------------
    # LLM arbitration
    # ------------------------------------------------------------------

    def _build_llm_prompt(self, candidates: list[LineCandidate]) -> str:
        """Serialise candidates into a structured prompt string for the LLM."""
        lines = []
        for c in candidates:
            signals_str = ",".join(c.signals)
            lines.append(
                f"[p{c.page}|L{c.level}|{c.size}pt|{signals_str}] {c.text}"
            )
        return "\n".join(lines)

    def _call_llm(
        self,
        candidates: list[LineCandidate],
    ) -> Optional[list[Section]]:
        """Submit candidates to the LLM and parse the returned JSON into sections.

        Args:
            candidates: Annotated heading candidates to arbitrate.

        Returns:
            A list of :class:`Section` objects confirmed by the LLM, or ``None``
            if the call fails or the response cannot be parsed.
        """
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
                    {"role": "user", "content": self._build_llm_prompt(candidates)},
                ],
                options={
                    "temperature": self.llm_temperature,
                    "num_predict": 2048,
                },
            )
            raw = response["message"]["content"].strip()
            raw = re.sub(r"```json\s*|\s*```", "", raw).strip()

            start = raw.find("[")
            end = raw.rfind("]")
            if start == -1 or end == -1:
                return None

            data = json.loads(raw[start : end + 1])
            candidate_map = {" ".join(c.text.lower().split()): c.size for c in candidates}

            return [
                Section(
                    title=item["title"],
                    level=item.get("level", 2),
                    page=item.get("page", 0),
                    size=candidate_map.get(" ".join(item["title"].lower().split()), 0.0),
                )
                for item in data
                if "title" in item
            ]

        except Exception as e:  # noqa: BLE001
            logger.error("LLM error: %s", e)
            return None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def extract(
        self,
        uuid: str,
        use_llm: bool = True
    ) -> list[Section]:
        """Extract the structured outline of a whitepaper PDF.

        Args:
            uuid: UUID of the document to process.
            use_llm: When ``False``, returns the raw heuristic result
                without calling the LLM arbitration step.

        Returns:
            A list of :class:`Section` objects ordered by appearance.
        """
        pdf_path = WhitepaperConfig.PDF_DIR / f"{uuid}.pdf"
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found for UUID: {uuid}")

        if self._already_processed(uuid):
            logger.info("skip (already processed)")
            return self._load(uuid)

        with pymupdf.open(pdf_path) as doc:

            native = self._get_native_toc(doc)
            if native:
                logger.info("native TOC (%d entries)", len(native))
                self._save(uuid, native)
                return native

            body_size = self._get_body_size(doc)
            lines = self._reconstruct_lines(doc)
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

        logger.info("heuristic (%d candidates) → LLM...", len(candidates))
        sections = self._call_llm(candidates)

        if not sections:
            logger.warning("LLM failed, fallback to heuristic")
            sections = [
                Section(title=c.text, level=c.level or 2, page=c.page)
                for c in candidates
            ]

        self._save(uuid, sections)
        return sections