#!/usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from core_shared.config import PostgresConfig

engine = create_engine(PostgresConfig.URL, echo=PostgresConfig.ECHO_SQL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()
