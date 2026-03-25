# app/db/base.py
"""SQLAlchemy declarative base module.

Provides the shared :data:`Base` class used for ORM model definitions.

Attributes:
    Base: The declarative base class for all SQLAlchemy models.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

__all__: list[str] = ["Base"]