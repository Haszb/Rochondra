#!/usr/bin/env python3

from datetime import datetime, timezone

from db.sql.base import SessionLocal
from db.sql.whitepaper.models import FactStructural, Whitepaper


def persist_structural_analysis(uuid: str, metrics: dict, metadata: dict) -> None:
    """Upsert the ``Whitepaper`` + ``FactStructural`` rows for *uuid*.

    Merges are idempotent, so calling this twice with the same UUID updates
    the existing rows instead of raising.

    Args:
        uuid: Document UUID (primary key on both tables).
        metrics: Structural metrics dict (word_count, gunning_fog_index, …).
        metadata: Document metadata dict (project_name, filename,
            file_size_mb, analyzed_at) sourced from the extract stage.
    """
    session = SessionLocal()
    try:
        analyzed_at_raw = metadata.get("analyzed_at")
        analyzed_at = (
            datetime.fromisoformat(analyzed_at_raw)
            if isinstance(analyzed_at_raw, str) and analyzed_at_raw
            else datetime.now(timezone.utc)
        )
        file_size_mb = metadata.get("file_size_mb")
        file_size_bytes = (
            int(float(file_size_mb) * 1024 * 1024) if file_size_mb is not None else None
        )

        session.merge(Whitepaper(
            uuid=uuid,
            project_name=metadata.get("project_name") or "Unknown",
            filename=metadata.get("filename") or f"{uuid}.pdf",
            file_size=file_size_bytes,
            analyzed_at=analyzed_at,
        ))
        session.merge(FactStructural(
            whitepaper_uuid=uuid,
            text_size_bytes=metrics.get("text_size_bytes"),
            word_count=metrics.get("word_count"),
            sentence_count=metrics.get("sentence_count"),
            syllable_count=metrics.get("syllable_count"),
            avg_word_length=metrics.get("avg_word_length"),
            gunning_fog_index=metrics.get("gunning_fog_index"),
            flesch_reading_ease=metrics.get("flesch_reading_ease"),
            image_count=metrics.get("image_count"),
            images_total_size_bytes=metrics.get("images_total_size_bytes"),
        ))
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
