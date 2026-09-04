"""Shared SQLAlchemy declarative base for all CabShare models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
