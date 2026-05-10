"""
app/db/base.py
--------------
Shared declarative base for all ORM models.
Import Base here; never re-create it elsewhere.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
