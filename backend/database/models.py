"""Database models for OdyssAI."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    """User profile model for additional user information."""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    street = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    zip = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    visa_status = Column(String(50), nullable=True)
    payment_methods = Column(JSON, default=list, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profile")


class Trip(Base):
    """Trip model for storing user trips."""
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="planned", index=True)  # planned, booked, completed
    booking_reference = Column(String(50), nullable=True)
    trip_data = Column(JSON, nullable=False)  # Stores complete trip information
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="trips")


