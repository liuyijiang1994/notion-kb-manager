"""
Link management database models
"""
from sqlalchemy import Integer, String, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.content import ParsedContent


class ImportTask(Base, TimestampMixin):
    """Import task tracking"""
    __tablename__ = 'import_task'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='pending', nullable=False)
    total_links: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_links: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    links: Mapped[List["Link"]] = relationship("Link", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<ImportTask(id={self.id}, name='{self.name}', status='{self.status}')>"


class Link(Base):
    """Imported link with metadata"""
    __tablename__ = 'link'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('import_task.id'))
    title: Mapped[Optional[str]] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # favorites/manual/history
    is_valid: Mapped[Optional[bool]] = mapped_column(Boolean)
    validation_status: Mapped[Optional[str]] = mapped_column(String(50))
    validation_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    priority: Mapped[str] = mapped_column(String(20), default='medium', nullable=False)
    tags: Mapped[Optional[list]] = mapped_column(JSON)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    task: Mapped[Optional["ImportTask"]] = relationship("ImportTask", back_populates="links")
    parsed_content: Mapped[Optional["ParsedContent"]] = relationship("ParsedContent", back_populates="link", uselist=False)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<Link(id={self.id}, url='{self.url[:50]}...', is_valid={self.is_valid})>"
