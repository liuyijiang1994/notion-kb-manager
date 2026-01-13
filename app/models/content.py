"""
Content processing database models
"""
from sqlalchemy import Integer, String, Text, DateTime, JSON, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.link import Link
    from app.models.notion import NotionImport


class ParsedContent(Base):
    """Parsed content from links"""
    __tablename__ = 'parsed_content'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    link_id: Mapped[int] = mapped_column(Integer, ForeignKey('link.id'), nullable=False)
    raw_content: Mapped[Optional[str]] = mapped_column(Text)
    formatted_content: Mapped[Optional[str]] = mapped_column(Text)
    quality_score: Mapped[Optional[int]] = mapped_column(Integer)
    parsing_method: Mapped[Optional[str]] = mapped_column(String(50))
    images: Mapped[Optional[list]] = mapped_column(JSON)
    tables: Mapped[Optional[list]] = mapped_column(JSON)
    paper_info: Mapped[Optional[dict]] = mapped_column(JSON)
    arxiv_id: Mapped[Optional[str]] = mapped_column(String(50))
    arxiv_pdf_path: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), default='pending', nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    parsed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    link: Mapped["Link"] = relationship("Link", back_populates="parsed_content")
    ai_processed_contents: Mapped[List["AIProcessedContent"]] = relationship(
        "AIProcessedContent", back_populates="parsed_content", cascade="all, delete-orphan"
    )

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<ParsedContent(id={self.id}, link_id={self.link_id}, quality={self.quality_score})>"


class AIProcessedContent(Base):
    """AI-processed content with versioning"""
    __tablename__ = 'ai_processed_content'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parsed_content_id: Mapped[int] = mapped_column(Integer, ForeignKey('parsed_content.id'), nullable=False)
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey('model_configuration.id'), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    chapter_summaries: Mapped[Optional[list]] = mapped_column(JSON)
    structured_content: Mapped[Optional[str]] = mapped_column(Text)
    keywords: Mapped[Optional[list]] = mapped_column(JSON)
    secondary_content: Mapped[Optional[str]] = mapped_column(Text)
    insights: Mapped[Optional[str]] = mapped_column(Text)
    processing_config: Mapped[Optional[dict]] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    parsed_content: Mapped["ParsedContent"] = relationship("ParsedContent", back_populates="ai_processed_contents")
    notion_import: Mapped[Optional["NotionImport"]] = relationship("NotionImport", back_populates="ai_content", uselist=False)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<AIProcessedContent(id={self.id}, version={self.version}, is_active={self.is_active})>"


class ProcessingTask(Base):
    """Background processing task tracking"""
    __tablename__ = 'processing_task'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # parsing/ai_processing
    status: Mapped[str] = mapped_column(String(50), default='pending', nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    error_log: Mapped[Optional[list]] = mapped_column(JSON)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Background task fields (Phase 5)
    job_id: Mapped[Optional[str]] = mapped_column(String(255))  # RQ job ID
    queue_name: Mapped[Optional[str]] = mapped_column(String(50))  # Queue name
    worker_id: Mapped[Optional[str]] = mapped_column(String(100))  # Worker ID
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    result_data: Mapped[Optional[dict]] = mapped_column(JSON)  # Result storage

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<ProcessingTask(id={self.id}, type='{self.type}', status='{self.status}')>"


class TaskItem(Base, TimestampMixin):
    """Individual item within a batch task"""
    __tablename__ = 'task_item'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey('processing_task.id', ondelete='CASCADE'), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)  # link_id, parsed_content_id, or ai_content_id
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'link', 'parsed_content', 'ai_content'
    status: Mapped[str] = mapped_column(String(50), default='pending', nullable=False)  # 'pending', 'running', 'completed', 'failed'
    job_id: Mapped[Optional[str]] = mapped_column(String(255))  # RQ job ID for this item
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    result_data: Mapped[Optional[dict]] = mapped_column(JSON)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<TaskItem(id={self.id}, task_id={self.task_id}, item_id={self.item_id}, status='{self.status}')>"
