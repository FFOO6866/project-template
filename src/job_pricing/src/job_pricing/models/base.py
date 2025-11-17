"""
Base SQLAlchemy Models and Mixins

This module provides:
- Base: Declarative base for all models
- TimestampMixin: Automatic created_at/updated_at timestamps
- Additional utility mixins for common model patterns
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base

# Declarative base for all models
Base = declarative_base()


class TimestampMixin:
    """
    Mixin to add automatic timestamp tracking to models.

    Provides:
    - created_at: Timestamp when record was created (UTC)
    - updated_at: Timestamp when record was last updated (UTC)

    Usage:
        class MyModel(Base, TimestampMixin):
            __tablename__ = 'my_table'
            id = Column(Integer, primary_key=True)
    """

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when record was created (UTC)"
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when record was last updated (UTC)"
    )
