"""
schemas.py - Comprehensive Pydantic schemas for request/response validation.
Covers Authentication, Food Listings, NGOs, Donation Requests, Matches, Pickups, and Impact Reports.
"""

from datetime import datetime
from typing import Optional, List
import re
from pydantic import BaseModel, field_validator, ConfigDict, Field



class UserBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    role: Optional[str] = "donor"
    user_type: Optional[str] = "donor"
    address: Optional[str] = None
    city: Optional[str] = "Bengaluru"
    location: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, v):
            raise ValueError(f"Invalid email address: {v}")
        return v.lower().strip()


class UserCreate(UserBase):
    password: Optional[str] = "password123"


class UserRegister(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut



class NGOBase(BaseModel):
    name: str
    registration_number: str
    contact_person: str
    email: str
    phone: str
    address: str
    city: Optional[str] = "Bengaluru"
    daily_meal_capacity: int = 100
    has_cold_storage: bool = False
    operating_hours: Optional[str] = "08:00 - 22:00"
    verified: bool = True

    @field_validator("daily_meal_capacity")
    @classmethod
    def capacity_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Daily meal capacity cannot be negative")
        return v

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, v):
            raise ValueError(f"Invalid NGO email: {v}")
        return v.lower().strip()


class NGOCreate(NGOBase):
    pass


class NGOUpdate(BaseModel):
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    daily_meal_capacity: Optional[int] = None
    has_cold_storage: Optional[bool] = None
    operating_hours: Optional[str] = None


class NGOOut(NGOBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)



class SurplusFoodBase(BaseModel):
    donor_id: int
    title: str
    description: Optional[str] = None
    category: str
    quantity: float
    unit: str = "kg"
    storage_requirement: str = "ambient"
    target_temp: Optional[str] = None
    dietary_tags: Optional[str] = None
    location: str
    pickup_by: datetime

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be greater than zero")
        return v

    @field_validator("title")
    @classmethod
    def title_min_length(cls, v: str) -> str:
        if not v or len(v.strip()) < 3:
            raise ValueError("Title must be at least 3 characters")
        return v.strip()


class SurplusFoodCreate(SurplusFoodBase):
    pass


class SurplusFoodUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    storage_requirement: Optional[str] = None
    pickup_by: Optional[datetime] = None
    status: Optional[str] = None


class SurplusFoodOut(SurplusFoodBase):
    id: int
    status: str
    ai_tags: Optional[str] = None
    created_at: datetime
    donor_name: Optional[str] = None
    dietary: Optional[List[str]] = None
    model_config = ConfigDict(from_attributes=True)


FoodListingCreate = SurplusFoodCreate
FoodListingOut = SurplusFoodOut



class DonationRequestBase(BaseModel):
    ngo_id: int
    title: str
    category_needed: str
    quantity_needed: float
    unit: str = "portions"
    urgency: str = "medium"
    beneficiary_count: int = 50
    target_date: datetime
    notes: Optional[str] = None

    @field_validator("quantity_needed")
    @classmethod
    def quantity_needed_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity needed must be greater than zero")
        return v

    @field_validator("beneficiary_count")
    @classmethod
    def beneficiary_count_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Beneficiary count must be at least 1")
        return v


class DonationRequestCreate(DonationRequestBase):
    pass


class DonationRequestUpdate(BaseModel):
    quantity_needed: Optional[float] = None
    beneficiary_count: Optional[int] = None
    urgency: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class DonationRequestOut(DonationRequestBase):
    id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)



class MatchBase(BaseModel):
    surplus_food_id: Optional[int] = None
    listing_id: Optional[int] = None
    ngo_id: Optional[int] = None
    recipient_id: Optional[int] = None
    request_id: Optional[int] = None
    compatibility_score: float = 0.85
    score: Optional[float] = None
    ai_reasoning: Optional[str] = None
    ai_reason: Optional[str] = None
    status: str = "pending"

    @field_validator("compatibility_score")
    @classmethod
    def score_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Compatibility score must be between 0.0 and 1.0")
        return v


class MatchCreate(MatchBase):
    pass


class MatchOut(MatchBase):
    id: int
    ngo_name: Optional[str] = None
    recipient_name: Optional[str] = None
    listing_title: Optional[str] = None
    ngo_city: Optional[str] = None
    ngo_address: Optional[str] = None
    daily_meal_capacity: Optional[int] = None
    has_cold_storage: Optional[bool] = None
    created_at: datetime
    accepted_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class MatchStatusUpdate(BaseModel):
    status: str



class PickupStatusBase(BaseModel):
    pickup_code: str
    match_id: int
    surplus_food_id: int
    ngo_id: int
    courier_id: Optional[int] = None
    courier_name: str = "Volunteer Courier"
    courier_phone: Optional[str] = None
    vehicle_type: str = "Electric Cargo Van"
    verification_pin: str
    current_status: str = "claimed"
    temperature_reading: Optional[str] = None
    estimated_arrival: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator("verification_pin")
    @classmethod
    def pin_valid(cls, v: str) -> str:
        if not v or len(v.strip()) < 4 or len(v.strip()) > 8:
            raise ValueError("Verification PIN must be between 4 and 8 characters")
        return v.strip()


class PickupStatusCreate(PickupStatusBase):
    pass


class PickupStatusOut(PickupStatusBase):
    id: int
    food_title: Optional[str] = None
    recipient_name: Optional[str] = None
    donor_name: Optional[str] = None
    pickup_location: Optional[str] = None
    delivery_address: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PickupStatusUpdate(BaseModel):
    current_status: str
    temperature_reading: Optional[str] = None
    notes: Optional[str] = None


class PickupVerifyPin(BaseModel):
    pin: str



class ImpactStatsResponse(BaseModel):
    total_listings: int
    active_listings: int
    claimed_listings: int
    completed_listings: int
    total_donors: int
    total_ngos: int
    total_kg_saved: float
    meals_provided: int
    co2_saved_kg: float
    water_saved_liters: int


class DonorImpactResponse(BaseModel):
    donor_id: int
    donor_name: str
    total_meals_donated: int
    total_kg_diverted: float
    co2_avoided_kg: float
    csr_tax_deduction_inr: float
    active_listings_count: int
    completed_listings_count: int


class NGOImpactResponse(BaseModel):
    ngo_id: int
    ngo_name: str
    daily_capacity: int
    total_meals_distributed: int
    total_beneficiaries_reached: int
    completed_pickups_count: int
    active_pickups_count: int


class MonthlyImpactItem(BaseModel):
    month: str
    kg_rescued: float
    meals_served: int
    co2_saved_kg: float


class ImpactCertificateResponse(BaseModel):
    certificate_id: str
    awarded_to: str
    organization_type: str
    meals_rescued: int
    kg_diverted: float
    co2_avoided_kg: float
    verification_status: str = "Blockchain & FSSAI Verified"
    issue_date: datetime



class AIMatchRequest(BaseModel):
    listing_id: int


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique conversation session identifier")
    message: str = Field(..., min_length=1, max_length=4000, description="User prompt or food surplus query")
    provider: Optional[str] = Field("xai", description="AI Provider: 'xai' (cloud Grok) or 'ollama' (local Qwen)")
    use_ollama: Optional[bool] = Field(None, description="Legacy toggle: true = ollama local, false = xai cloud")

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, v: Optional[str]) -> str:
        if not v:
            return "xai"
        v_clean = str(v).lower().strip()
        if v_clean in ("ollama", "qwen", "local"):
            return "ollama"
        if v_clean in ("xai", "grok", "cloud"):
            return "xai"
        return v_clean


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    model_used: str
    provider: str = "xai"
    status: str = "success"
    fallback_notice: Optional[str] = None


class ProviderInfo(BaseModel):
    id: str
    name: str
    type: str
    model: str
    endpoint: str
    available: bool
    status_message: str
    is_default: bool


class ProvidersResponse(BaseModel):
    default_provider: str
    fallback_enabled: bool
    providers: list[ProviderInfo]
