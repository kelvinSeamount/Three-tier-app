from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .database import Base

# A Model = the blueprint for a database TABLE.
# Think of it like designing a form: what fields does a user record have?
class User(Base):
    __tablename__ = "users"  # This becomes the actual table name in PostgreSQL

    id = Column(Integer, primary_key=True, index=True)  # Auto-incremented row number
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)  # NEVER store plain text passwords
    created_at = Column(DateTime(timezone=True), server_default=func.now())
