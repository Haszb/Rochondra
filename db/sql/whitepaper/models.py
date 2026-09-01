from datetime import UTC, datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from db.sql.base import Base


class Whitepaper(Base):
    __tablename__ = "whitepaper"

    uuid = Column(String, primary_key=True)
    project_name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=True)
    analyzed_at = Column(DateTime, default=lambda: datetime.now(UTC))
    analysis_version = Column(Integer, nullable=True, default=1)

    structural = relationship("FactStructural", back_populates="whitepaper", uselist=False)
    sentiments = relationship("FactSentiment", back_populates="whitepaper")
    ner = relationship("FactNer", back_populates="whitepaper", uselist=False)
    reference = relationship("FactReference", back_populates="whitepaper", uselist=False)


class FactStructural(Base):
    __tablename__ = "fact_structural"

    whitepaper_uuid = Column(String, ForeignKey("whitepaper.uuid"), primary_key=True)  # ← renommé
    text_size_bytes = Column(Integer)
    word_count = Column(Integer)
    sentence_count = Column(Integer)
    syllable_count = Column(Integer)
    avg_word_length = Column(Float)
    gunning_fog_index = Column(Float, nullable=True)
    flesch_reading_ease = Column(Float, nullable=True)
    image_count = Column(Integer, nullable=True)
    images_total_size_bytes = Column(Integer, nullable=True)

    whitepaper = relationship("Whitepaper", back_populates="structural")


class FactSentiment(Base):
    """Placeholder — columns TBD once the section-segmentation methodology is implemented."""
    __tablename__ = "fact_sentiment"

    whitepaper_uuid = Column(String, ForeignKey("whitepaper.uuid"), primary_key=True)
    section_name = Column(String, primary_key=True)

    whitepaper = relationship("Whitepaper", back_populates="sentiments")


class FactNer(Base):
    """Placeholder — columns TBD."""
    __tablename__ = "fact_ner"

    whitepaper_uuid = Column(String, ForeignKey("whitepaper.uuid"), primary_key=True)

    whitepaper = relationship("Whitepaper", back_populates="ner")


class FactReference(Base):
    """Placeholder — columns TBD."""
    __tablename__ = "fact_reference"

    whitepaper_uuid = Column(String, ForeignKey("whitepaper.uuid"), primary_key=True)

    whitepaper = relationship("Whitepaper", back_populates="reference")