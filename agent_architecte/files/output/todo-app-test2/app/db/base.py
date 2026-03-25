"""
SQLAlchemy declarative base for the application.

Provides a single Base class used for all ORM model definitions.
"""

from sqlalchemy.orm import DeclarativeMeta, declarative_base

Base: DeclarativeMeta = declarative_base()