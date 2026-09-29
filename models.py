import uuid
import enum

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    Enum
)
from sqlalchemy.orm import relationship

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
    created_at = Column(Date, nullable=False)
    fixed_emotion = Column(String(15), nullable=True)
    fixed_secondary_emotion = Column(String(15), nullable=True)
    fixed_compound_emotion = Column(String(15), nullable=True)

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
    created_at = Column(Date, nullable=False)

class SurveyStatus(enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    ANSWERED = "ANSWERED"
    EXPIRED = "EXPIRED"


class SurveyTemplate(Base):
    __tablename__ = "surveys_templates"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    subject = Column(
        String(100),
        nullable=False
    )

    message = Column(
        String(255),
        nullable=False
    )

    template = Column(
        Text,
        nullable=False
    )

    emotion = Column(
        String(15),
        nullable=False
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    answers = relationship(
        "SurveyAnswer",
        back_populates="survey"
    )


class SurveyAnswer(Base):
    __tablename__ = "surveys_answers"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    email = Column(
        String(100),
        nullable=False
    )

    survey_id = Column(
        Integer,
        ForeignKey("surveys_templates.id"),
        nullable=False
    )

    token = Column(
        String(40),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    answers = Column(
        Text,
        nullable=True
    )

    responded_at = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    status = Column(
        Enum(
            SurveyStatus,
            name="survey_status",
            native_enum=True
        ),
        nullable=False,
        default=SurveyStatus.PENDING,
        server_default="PENDING"
    )

    template_snapshot = Column(
        Text,
        nullable=True
    )

    sent_at = Column(
        DateTime,
        nullable=True
    )

    last_activity_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    survey = relationship(
        "SurveyTemplate",
        back_populates="answers"
    )