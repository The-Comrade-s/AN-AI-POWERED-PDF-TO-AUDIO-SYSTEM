"""
SQLAlchemy ORM models for the AI PDF to Audio System.

Tables:
    User, PDFDocument, AudioFile, Bookmark, ListeningHistory, Note, Download
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

DB_PATH = "sqlite:///pdf2audio.db"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    theme = Column(String(20), default="dark")
    default_voice = Column(String(50), default="en-US-JennyNeural")
    default_speed = Column(Float, default=1.0)
    language = Column(String(10), default="en")
    notifications_enabled = Column(Boolean, default=True)

    pdfs = relationship("PDFDocument", back_populates="owner", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    history = relationship("ListeningHistory", back_populates="user", cascade="all, delete-orphan")
    downloads = relationship("Download", back_populates="user", cascade="all, delete-orphan")


class PDFDocument(Base):
    __tablename__ = "pdfs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=True)
    page_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    summary = Column(Text, nullable=True)
    chapters_json = Column(Text, nullable=True)  # JSON list of {title, start_char, end_char}
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    file_size_kb = Column(Float, default=0.0)
    status = Column(String(30), default="uploaded")  # uploaded, processing, converted, failed

    owner = relationship("User", back_populates="pdfs")
    audio_files = relationship("AudioFile", back_populates="pdf", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="pdf", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="pdf", cascade="all, delete-orphan")
    history_entries = relationship("ListeningHistory", cascade="all, delete-orphan")


class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    voice = Column(String(50), default="en-US-JennyNeural")
    format = Column(String(10), default="mp3")
    file_path = Column(String(500), nullable=False)
    duration_seconds = Column(Float, default=0.0)
    chapter_title = Column(String(255), nullable=True)  # null = full audiobook
    chapter_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    pdf = relationship("PDFDocument", back_populates="audio_files")
    downloads = relationship("Download", cascade="all, delete-orphan")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"), nullable=False)
    position_seconds = Column(Float, default=0.0)
    label = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookmarks")
    pdf = relationship("PDFDocument", back_populates="bookmarks")


class ListeningHistory(Base):
    __tablename__ = "listening_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"), nullable=False)
    last_position_seconds = Column(Float, default=0.0)
    total_listened_seconds = Column(Float, default=0.0)
    last_played_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="history")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"), nullable=False)
    timestamp_seconds = Column(Float, default=0.0)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notes")
    pdf = relationship("PDFDocument", back_populates="notes")


class Download(Base):
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    audio_file_id = Column(Integer, ForeignKey("audio_files.id"), nullable=False)
    downloaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="downloads")


engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Return a new SQLAlchemy session."""
    return SessionLocal()
