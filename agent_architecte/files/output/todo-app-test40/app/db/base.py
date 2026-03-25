from sqlalchemy.orm import declarative_base

# Base class for all ORM models.
Base = declarative_base()

__all__: list[str] = ["Base"]