# backend/db.py
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, History

DB_PATH = Path(__file__).parent / "db.sqlite3"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)

def add_history_entry(data: Dict[str, Any]):
    """Add or update a history entry"""
    db = SessionLocal()
    try:
        entry_id = data.get("id")
        url = data.get("url")
        filename = data.get("filename")
        mode = data.get("mode", "video")
        status = data.get("status", "finished")
        meta = data.get("meta", {})
        
        # Check if exists
        existing = db.query(History).filter(History.id == entry_id).first()
        if existing:
            # Update
            existing.filename = filename
            existing.status = status
            existing.finished_at = datetime.datetime.utcnow()
            if meta:
                existing.meta = json.dumps(meta)
        else:
            # Create new
            hist = History(
                id=entry_id,
                url=url,
                filename=filename,
                mode=mode,
                status=status,
                meta=json.dumps(meta) if meta else None
            )
            db.add(hist)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def list_history(limit: int = 200) -> List[Dict]:
    """List history entries"""
    db = SessionLocal()
    try:
        entries = db.query(History).order_by(History.created_at.desc()).limit(limit).all()
        return [e.to_dict() for e in entries]
    finally:
        db.close()

def delete_history(entry_id: str) -> bool:
    """Delete a history entry by id"""
    db = SessionLocal()
    try:
        entry = db.query(History).filter(History.id == entry_id).first()
        if entry:
            db.delete(entry)
            db.commit()
            return True
        return False
    finally:
        db.close()

def clear_history():
    """Clear all history entries"""
    db = SessionLocal()
    try:
        db.query(History).delete()
        db.commit()
    finally:
        db.close()
