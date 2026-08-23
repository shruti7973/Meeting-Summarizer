# File: backend/models.py

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    filename: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    transcript: Mapped["Transcript"] = relationship(
        "Transcript",
        back_populates="meeting",
        cascade="all, delete-orphan",
        uselist=False,
    )

    summary: Mapped["Summary"] = relationship(
        "Summary",
        back_populates="meeting",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    meeting_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "meetings.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    meeting: Mapped["Meeting"] = relationship(
        "Meeting",
        back_populates="transcript",
    )


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    meeting_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "meetings.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
    )

    summary_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    decisions_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    action_items_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    meeting: Mapped["Meeting"] = relationship(
        "Meeting",
        back_populates="summary",
    )