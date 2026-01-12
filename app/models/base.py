"""
Base model with common functionality
"""
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, DateTime
from typing import Optional


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
