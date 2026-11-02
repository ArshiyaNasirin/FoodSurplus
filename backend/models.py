"""
models.py - SQLAlchemy ORM Models for FoodResQ AI platform.
Includes tables for Users, Surplus Food, NGOs, Donation Requests, Matches, and Pickup Status.
Configured with rich relational mappings, cascade behaviors, and validation rules.
"""

from datetime import datetime
import enum
import re
from typing import Optional, List

from sqlalchemy import (
    String, Integer, Float, DateTime, Text, Boolean,
    ForeignKey, CheckConstraint, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from backend.database import Base



class UserRole(str, enum.Enum):
    DONOR = "donor"
    RECIPIENT = "recipient"
    COURIER = "courier"
    ADMIN = "admin"

UserType = UserRole


class FoodCategory(str, enum.Enum):
    COOKED = "cooked"
    BAKERY = "bakery"
    PRODUCE = "produce"
    DAIRY = "dairy"
    RAW = "raw"
    PACKAGED = "packaged"


class FoodStatus(str, enum.Enum):
    AVAILABLE = "available"
    MATCHED = "matched"
    CLAIMED = "claimed"
    COMPLETED = "completed"
    EXPIRED = "expired"


class RequestUrgency(str, enum.Enum):
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RequestStatus(str, enum.Enum):
    OPEN = "open"
    MATCHED = "matched"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class PickupStage(str, enum.Enum):
    CLAIMED = "claimed"
    DRIVER_ASSIGNED = "driver_assigned"
    AT_RESTAURANT = "at_restaurant"
    PIN_VERIFIED = "pin_verified"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"



class User(Base):
    """Represents system participants: donors, restaurants, couriers, or admins."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    role: Mapped[str] = mapped_column(String(30), default=UserRole.DONOR.value, nullable=False)
    user_type: Mapped[str] = mapped_column(String(30), default=UserRole.DONOR.value, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), default="Bengaluru", nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    surplus_foods: Mapped[List["SurplusFood"]] = relationship(
        "SurplusFood", back_populates="donor", cascade="all, delete-orphan"
    )
    assigned_pickups: Mapped[List["PickupStatus"]] = relationship(
        "PickupStatus", back_populates="courier"
    )

    def __init__(self, **kwargs):
        if "user_type" in kwargs and "role" not in kwargs:
            kwargs["role"] = kwargs["user_type"]
        if "role" in kwargs and "user_type" not in kwargs:
            kwargs["user_type"] = kwargs["role"]
        if "location" in kwargs and "address" not in kwargs:
            kwargs["address"] = kwargs["location"]
        if "address" in kwargs and "location" not in kwargs:
            kwargs["location"] = kwargs["address"]
        super().__init__(**kwargs)

    @validates("email")
    def validate_email(self, key, address):
        if not address or "@" not in address:
            raise ValueError(f"Invalid email address format: {address}")
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, address):
            raise ValueError(f"Invalid email address format: {address}")
        return address.lower().strip()

    @validates("name")
    def validate_name(self, key, name):
        if not name or len(name.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")
        return name.strip()

    @validates("phone")
    def validate_phone(self, key, phone):
        if phone:
            cleaned = re.sub(r"[\s\-\(\)\+]", "", phone)
            if len(cleaned) < 7:
                raise ValueError(f"Invalid phone number length: {phone}")
        return phone



class NGO(Base):
    """Represents verified charitable organizations, food banks, and shelters."""
    __tablename__ = "ngos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    registration_number: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    contact_person: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    city: Mapped[str] = mapped_column(String(100), default="Bengaluru", nullable=False)
    daily_meal_capacity: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    has_cold_storage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    operating_hours: Mapped[Optional[str]] = mapped_column(String(100), default="08:00 - 22:00", nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("daily_meal_capacity >= 0", name="check_ngo_capacity_non_negative"),
    )

    donation_requests: Mapped[List["DonationRequest"]] = relationship(
        "DonationRequest", back_populates="ngo", cascade="all, delete-orphan"
    )
    matches: Mapped[List["Match"]] = relationship(
        "Match", back_populates="ngo", cascade="all, delete-orphan"
    )
    pickups: Mapped[List["PickupStatus"]] = relationship(
        "PickupStatus", back_populates="ngo"
    )

    @validates("email")
    def validate_ngo_email(self, key, address):
        if not address or "@" not in address:
            raise ValueError(f"Invalid NGO email: {address}")
        return address.lower().strip()

    @validates("daily_meal_capacity")
    def validate_capacity(self, key, capacity):
        if capacity is not None and capacity < 0:
            raise ValueError("Daily meal capacity cannot be negative")
        return capacity

    @validates("name", "registration_number")
    def validate_non_empty(self, key, val):
        if not val or not val.strip():
            raise ValueError(f"{key} cannot be empty")
        return val.strip()



class SurplusFood(Base):
    """Surplus food items listed by commercial donors or households."""
    __tablename__ = "surplus_food"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    donor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(30), default="kg", nullable=False)
    storage_requirement: Mapped[str] = mapped_column(String(50), default="ambient", nullable=False)
    target_temp: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    dietary_tags: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    location: Mapped[str] = mapped_column(String(300), nullable=False)
    pickup_by: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default=FoodStatus.AVAILABLE.value, nullable=False, index=True)
    ai_tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_surplus_food_quantity_positive"),
    )

    donor: Mapped["User"] = relationship("User", back_populates="surplus_foods")
    matches: Mapped[List["Match"]] = relationship(
        "Match", back_populates="surplus_food", cascade="all, delete-orphan"
    )
    pickups: Mapped[List["PickupStatus"]] = relationship(
        "PickupStatus", back_populates="surplus_food", cascade="all, delete-orphan"
    )

    @property
    def donor_name(self) -> Optional[str]:
        return self.donor.name if self.donor else None

    @property
    def dietary(self) -> List[str]:
        if not self.dietary_tags:
            return []
        return [t.strip() for t in self.dietary_tags.split(",") if t.strip()]

    @validates("quantity")
    def validate_quantity(self, key, qty):
        if qty is None or float(qty) <= 0:
            raise ValueError(f"Surplus food quantity must be greater than 0, got {qty}")
        return float(qty)

    @validates("title")
    def validate_title(self, key, title):
        if not title or len(title.strip()) < 3:
            raise ValueError("Surplus food title must be at least 3 characters long")
        return title.strip()

    @validates("status")
    def validate_status(self, key, st):
        valid_statuses = [s.value for s in FoodStatus]
        if st not in valid_statuses:
            raise ValueError(f"Invalid food status '{st}'. Allowed: {valid_statuses}")
        return st


FoodListing = SurplusFood



class DonationRequest(Base):
    """Specific food needs requested by recipient NGOs and shelters."""
    __tablename__ = "donation_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ngo_id: Mapped[int] = mapped_column(Integer, ForeignKey("ngos.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category_needed: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity_needed: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(30), default="portions", nullable=False)
    urgency: Mapped[str] = mapped_column(String(30), default=RequestUrgency.MEDIUM.value, nullable=False)
    beneficiary_count: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    target_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=RequestStatus.OPEN.value, nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity_needed > 0", name="check_request_quantity_positive"),
        CheckConstraint("beneficiary_count >= 1", name="check_beneficiary_count_positive"),
    )

    ngo: Mapped["NGO"] = relationship("NGO", back_populates="donation_requests")
    matches: Mapped[List["Match"]] = relationship("Match", back_populates="donation_request")

    @validates("quantity_needed")
    def validate_quantity_needed(self, key, qty):
        if qty is None or float(qty) <= 0:
            raise ValueError(f"Quantity needed must be > 0, got {qty}")
        return float(qty)

    @validates("beneficiary_count")
    def validate_beneficiary_count(self, key, count):
        if count is None or int(count) < 1:
            raise ValueError(f"Beneficiary count must be at least 1, got {count}")
        return int(count)



class Match(Base):
    """AI-scored match pairing surplus food with an NGO or request."""
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    surplus_food_id: Mapped[int] = mapped_column(Integer, ForeignKey("surplus_food.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id: Mapped[int] = mapped_column(Integer, index=True, nullable=True)
    ngo_id: Mapped[int] = mapped_column(Integer, ForeignKey("ngos.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=True)
    request_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("donation_requests.id", ondelete="SET NULL"), nullable=True)
    compatibility_score: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=True)
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=MatchStatus.PENDING.value, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("compatibility_score >= 0.0 AND compatibility_score <= 1.0", name="check_match_score_range"),
    )

    surplus_food: Mapped["SurplusFood"] = relationship("SurplusFood", back_populates="matches")
    ngo: Mapped["NGO"] = relationship("NGO", back_populates="matches")
    donation_request: Mapped[Optional["DonationRequest"]] = relationship("DonationRequest", back_populates="matches")
    pickup: Mapped[Optional["PickupStatus"]] = relationship(
        "PickupStatus", back_populates="match", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def ngo_name(self) -> Optional[str]:
        return self.ngo.name if self.ngo else None

    @property
    def recipient_name(self) -> Optional[str]:
        return self.ngo.name if self.ngo else None

    @property
    def listing_title(self) -> Optional[str]:
        return self.surplus_food.title if self.surplus_food else None

    @property
    def ngo_city(self) -> Optional[str]:
        return self.ngo.city if self.ngo else None

    @property
    def ngo_address(self) -> Optional[str]:
        return self.ngo.address if self.ngo else None

    @property
    def daily_meal_capacity(self) -> Optional[int]:
        return self.ngo.daily_meal_capacity if self.ngo else None

    @property
    def has_cold_storage(self) -> Optional[bool]:
        return self.ngo.has_cold_storage if self.ngo else None

    def __init__(self, **kwargs):
        if "listing_id" in kwargs and "surplus_food_id" not in kwargs:
            kwargs["surplus_food_id"] = kwargs["listing_id"]
        if "surplus_food_id" in kwargs and "listing_id" not in kwargs:
            kwargs["listing_id"] = kwargs["surplus_food_id"]
        if "recipient_id" in kwargs and "ngo_id" not in kwargs:
            kwargs["ngo_id"] = kwargs["recipient_id"]
        if "ngo_id" in kwargs and "recipient_id" not in kwargs:
            kwargs["recipient_id"] = kwargs["ngo_id"]
        if "score" in kwargs and "compatibility_score" not in kwargs:
            kwargs["compatibility_score"] = kwargs["score"]
        if "compatibility_score" in kwargs and "score" not in kwargs:
            kwargs["score"] = kwargs["compatibility_score"]
        if "ai_reason" in kwargs and "ai_reasoning" not in kwargs:
            kwargs["ai_reasoning"] = kwargs["ai_reason"]
        if "ai_reasoning" in kwargs and "ai_reason" not in kwargs:
            kwargs["ai_reason"] = kwargs["ai_reasoning"]
        super().__init__(**kwargs)

    @validates("compatibility_score")
    def validate_score(self, key, val):
        if val is None or not (0.0 <= float(val) <= 1.0):
            raise ValueError(f"Compatibility score must be between 0.0 and 1.0, got {val}")
        return float(val)

    @validates("status")
    def validate_match_status(self, key, st):
        valid = [s.value for s in MatchStatus]
        if st not in valid:
            raise ValueError(f"Invalid match status '{st}'. Allowed: {valid}")
        return st



class PickupStatus(Base):
    """End-to-end logistics tracking and secure verification PIN handoff."""
    __tablename__ = "pickup_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pickup_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    surplus_food_id: Mapped[int] = mapped_column(Integer, ForeignKey("surplus_food.id", ondelete="CASCADE"), nullable=False, index=True)
    ngo_id: Mapped[int] = mapped_column(Integer, ForeignKey("ngos.id", ondelete="CASCADE"), nullable=False, index=True)
    courier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    courier_name: Mapped[str] = mapped_column(String(120), default="Volunteer Courier", nullable=False)
    courier_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    vehicle_type: Mapped[str] = mapped_column(String(80), default="Electric Cargo Van", nullable=False)
    verification_pin: Mapped[str] = mapped_column(String(10), nullable=False)
    current_status: Mapped[str] = mapped_column(String(40), default=PickupStage.CLAIMED.value, nullable=False, index=True)
    temperature_reading: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    estimated_arrival: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    match: Mapped["Match"] = relationship("Match", back_populates="pickup")
    surplus_food: Mapped["SurplusFood"] = relationship("SurplusFood", back_populates="pickups")
    ngo: Mapped["NGO"] = relationship("NGO", back_populates="pickups")
    courier: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_pickups")

    @property
    def food_title(self) -> Optional[str]:
        return self.surplus_food.title if self.surplus_food else None

    @property
    def recipient_name(self) -> Optional[str]:
        return self.ngo.name if self.ngo else None

    @property
    def donor_name(self) -> Optional[str]:
        return self.surplus_food.donor.name if (self.surplus_food and self.surplus_food.donor) else None

    @property
    def pickup_location(self) -> Optional[str]:
        return self.surplus_food.location if self.surplus_food else None

    @property
    def delivery_address(self) -> Optional[str]:
        return self.ngo.address if self.ngo else None

    @validates("verification_pin")
    def validate_pin(self, key, pin):
        if not pin or len(pin.strip()) < 4 or len(pin.strip()) > 8:
            raise ValueError(f"Verification PIN must be between 4 and 8 characters, got '{pin}'")
        return pin.strip()

    @validates("current_status")
    def validate_pickup_status(self, key, st):
        valid = [s.value for s in PickupStage]
        if st not in valid:
            raise ValueError(f"Invalid pickup stage '{st}'. Allowed: {valid}")
        return st


Pickup = PickupStatus



class ChatMessage(Base):
    """Stores AI chatbot conversation history."""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
