"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# Authentication Schemas
class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model."""
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# Profile Schemas
class UserProfileUpdate(BaseModel):
    """User profile update request."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    visa_status: Optional[str] = None


class PaymentMethod(BaseModel):
    """Payment method model."""
    type: str  # "card", "paypal", etc.
    last4: Optional[str] = None
    brand: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    masked_number: Optional[str] = None


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: int
    user_id: int
    full_name: Optional[str]
    phone: Optional[str]
    street: Optional[str]
    city: Optional[str]
    zip: Optional[str]
    country: Optional[str]
    visa_status: Optional[str]
    payment_methods: List[Dict[str, Any]]
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentMethodAdd(BaseModel):
    """Add payment method request."""
    type: str
    last4: Optional[str] = None
    brand: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    masked_number: Optional[str] = None


# Trip Schemas
class TripCreate(BaseModel):
    """Create trip request."""
    status: str = "planned"  # planned, booked, completed
    booking_reference: Optional[str] = None
    trip_data: Dict[str, Any]  # Complete trip information


class TripUpdate(BaseModel):
    """Update trip request."""
    status: Optional[str] = None
    booking_reference: Optional[str] = None
    trip_data: Optional[Dict[str, Any]] = None


class TripResponse(BaseModel):
    """Trip response model."""
    id: int
    user_id: int
    status: str
    booking_reference: Optional[str]
    trip_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


