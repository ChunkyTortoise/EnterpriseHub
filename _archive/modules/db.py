import os
import json
from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv

load_dotenv(override=True)

# Use the local Postgres 17 instance we just set up
# Default to the one created in Step 1
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cave@localhost:5432/enterprise_hub")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class Property(Base):
    __tablename__ = "properties"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    address: Mapped[Optional[str]] = mapped_column(String)
    city: Mapped[Optional[str]] = mapped_column(String)
    price: Mapped[Optional[int]] = mapped_column(Integer)
    beds: Mapped[Optional[int]] = mapped_column(Integer)
    baths: Mapped[Optional[float]] = mapped_column(Float)
    sqft: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default='Active')
    list_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON) # Storing as JSON
    
    # Semantic Search Embedding (768 dimensions is standard for Gemini/Vertex embeddings)
    embedding = mapped_column(Vector(768), nullable=True)

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    phone: Mapped[Optional[str]] = mapped_column(String)
    max_budget: Mapped[Optional[int]] = mapped_column(Integer)
    min_beds: Mapped[Optional[int]] = mapped_column(Integer)
    preferred_neighborhood: Mapped[Optional[str]] = mapped_column(String)
    must_haves: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Preference embedding
    preference_embedding = mapped_column(Vector(768), nullable=True)

class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[str] = mapped_column(String)
    property_id: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String) # 'like', 'pass'
    feedback: Mapped[Optional[dict]] = mapped_column(JSON)
    time_on_card: Mapped[Optional[float]] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())

def init_db():
    """Creates tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
