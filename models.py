import uuid
import enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
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

    __table_args__ = (
        UniqueConstraint("created_at", name="uq_emails_count_date"),
    )
    
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
    surprise = Column(Integer, nullable=False, default=0)
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

class FailedEmail(Base):
    __tablename__ = "failed_emails"

    id = Column(Integer, primary_key=True, index=True)

    task_id = Column(String(255), unique=True, nullable=False)

    from_email = Column(String(255), nullable=True)
    subject = Column(Text, nullable=True)
    body = Column(Text, nullable=True)

    received_at = Column(DateTime(timezone=True), nullable=True)

    error_type = Column(String(255), nullable=False)
    error_message = Column(Text, nullable=False)

    attempts = Column(Integer, nullable=False, default=1)

    status = Column(
        String(30),
        nullable=False,
        default="failed"
    )

    failed_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    resolved_at = Column(DateTime, nullable=True)