# backend/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class History(Base):
    __tablename__ = "history"
    
    id = Column(String, primary_key=True, index=True)
    url = Column(Text, nullable=False)
    filename = Column(String, nullable=True)
    mode = Column(String, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    meta = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "filename": self.filename,
            "mode": self.mode,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "meta": self.meta,
        }
