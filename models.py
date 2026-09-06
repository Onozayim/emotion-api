from sqlalchemy import Column, Integer, String, Date, func
from database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True)
    body = Column(nullable=False)
    subject = Column(String(255), nullable=False)
    emotion = Column(String(15), nullable=False)
    secondary_emotion = Column(String(15), nullable=False)
    compound_emotion = Column(String(15), nullable=False)
    from_email = Column(String(100), nullable=False)
    created_at = Column(Date, nullable=False, default=func.now())
    fixed_emotion = Column(String(15), nullable=False)

class EmailCount(Base):
    __tablename__ = "emails_count"
    
    id = Column(Integer, primary_key=True)
    joy = Column(Integer, nullable=False, default=0)
    sadness = Column(Integer, nullable=False, default=0)
    anger = Column(Integer, nullable=False, default=0)
    fear = Column(Integer, nullable=False, default=0)
    disgust = Column(Integer, nullable=False, default=0)
    sec_joy = Column(Integer, nullable=False, default=0)
    sec_sadness = Column(Integer, nullable=False, default=0)
    sec_anger = Column(Integer, nullable=False, default=0)
    sec_fear = Column(Integer, nullable=False, default=0)
    sec_disgust = Column(Integer, nullable=False, default=0)
    nostalgia = Column(Integer, nullable=False, default=0)
    intrigue = Column(Integer, nullable=False, default=0)
    justice = Column(Integer, nullable=False, default=0)
    contempt = Column(Integer, nullable=False, default=0)
    anxiety = Column(Integer, nullable=False, default=0)
    betrayal = Column(Integer, nullable=False, default=0)
    repulsion = Column(Integer, nullable=False, default=0)
    aversion = Column(Integer, nullable=False, default=0)
    hate = Column(Integer, nullable=False, default=0)
    created_at = Column(Date, nullable=False, default=func.now())