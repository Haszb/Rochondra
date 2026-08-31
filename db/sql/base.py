#!/usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql+psycopg://rochondra:devpassword@localhost:5432/rochondra"

engine = create_engine(DATABASE_URL, echo=True)  # echo=True utile en dev, à retirer en prod
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()