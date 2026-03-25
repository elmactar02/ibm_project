"""SQLAlchemy declarative base module.

Provides a single ``Base`` class used for ORM model definitions.

The ``Base`` is created via :func:`sqlalchemy.orm.declarative_base` and
exported for import by other modules.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

__all__: list[str] = ["Base"]