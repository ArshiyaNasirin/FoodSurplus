"""
routers/pickup.py - Live Pickup Logistics & Verification PIN Endpoints.

Endpoints:
  POST /api/pickups                     - Create a pickup logistics record
  GET  /api/pickups                     - List pickups (status, NGO, courier filters)
  GET  /api/pickups/{code}              - Get shipment tracking details
  PUT  /api/pickups/{code}/status       - Advance milestone stage & record temperature
  POST /api/pickups/{code}/verify-pin   - Authenticate 4-digit handover PIN
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    PickupStatus, PickupStage,
    SurplusFood, FoodStatus,
    Match, MatchStatus
)
from backend.schemas import (
    PickupStatusCreate, PickupStatusOut,
    PickupStatusUpdate, PickupVerifyPin
)

router = APIRouter(prefix="/pickups", tags=["Pickup Logistics & Tracking"])


@router.post("", response_model=PickupStatusOut, status_code=status.HTTP_201_CREATED)
def create_pickup_order(
    pickup: PickupStatusCreate,
    db: Session = Depends(get_db)
):
    """
    Initiate a new pickup order with verification PIN and courier assignment.
    """
    existing = db.query(PickupStatus).filter(PickupStatus.pickup_code == pickup.pickup_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pickup code '{pickup.pickup_code}' already exists."
        )

    db_pickup = PickupStatus(**pickup.model_dump())
    db.add(db_pickup)
    db.commit()
    db.refresh(db_pickup)
    return db_pickup


@router.get("", response_model=List[PickupStatusOut])
def list_pickups(
    current_status: Optional[str] = Query(None, description="Filter by stage (claimed, driver_assigned, at_restaurant, pin_verified, in_transit, delivered)"),
    ngo_id: Optional[int] = Query(None, description="Filter by recipient NGO ID"),
    courier_id: Optional[int] = Query(None, description="Filter by courier user ID"),
    db: Session = Depends(get_db)
):
    """
    List all pickup shipments with optional operational filters.
    """
    query = db.query(PickupStatus)
    if current_status:
        query = query.filter(PickupStatus.current_status == current_status)
    if ngo_id:
        query = query.filter(PickupStatus.ngo_id == ngo_id)
    if courier_id:
        query = query.filter(PickupStatus.courier_id == courier_id)
    return query.order_by(PickupStatus.created_at.desc()).all()


@router.get("/{pickup_code}", response_model=PickupStatusOut)
def get_pickup_details(pickup_code: str, db: Session = Depends(get_db)):
    """
    Retrieve real-time tracking details, temperature log, and courier telemetry for a shipment.
    """
    pickup = db.query(PickupStatus).filter(PickupStatus.pickup_code == pickup_code.upper()).first()
    if not pickup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment #{pickup_code} not found."
        )
    return pickup


@router.put("/{pickup_code}/status", response_model=PickupStatusOut)
def advance_pickup_stage(
    pickup_code: str,
    update: PickupStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Advance shipment milestone stage, log food temperature reading, and sync food listing status.
    """
    pickup = db.query(PickupStatus).filter(PickupStatus.pickup_code == pickup_code.upper()).first()
    if not pickup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment #{pickup_code} not found."
        )

    valid_stages = [s.value for s in PickupStage]
    if update.current_status not in valid_stages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage '{update.current_status}'. Allowed: {valid_stages}"
        )

    pickup.current_status = update.current_status
    if update.temperature_reading:
        pickup.temperature_reading = update.temperature_reading
    if update.notes:
        pickup.notes = update.notes

    if update.current_status == PickupStage.DELIVERED.value:
        pickup.completed_at = datetime.utcnow()
        food = db.query(SurplusFood).filter(SurplusFood.id == pickup.surplus_food_id).first()
        if food:
            food.status = FoodStatus.COMPLETED.value

    pickup.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(pickup)
    return pickup


@router.post("/{pickup_code}/verify-pin", status_code=status.HTTP_200_OK)
def verify_handover_pin(
    pickup_code: str,
    body: PickupVerifyPin,
    db: Session = Depends(get_db)
):
    """
    Authenticate the 4-digit verification PIN provided during food handover.
    Guarantees that food is transferred strictly to the authorized courier and recipient.
    """
    pickup = db.query(PickupStatus).filter(PickupStatus.pickup_code == pickup_code.upper()).first()
    if not pickup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment #{pickup_code} not found."
        )

    if pickup.verification_pin != body.pin.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification PIN. Handover cannot be authenticated."
        )

    pickup.current_status = PickupStage.PIN_VERIFIED.value
    pickup.notes = f"Handover PIN {body.pin} verified at {datetime.utcnow().strftime('%H:%M:%S')}."
    pickup.updated_at = datetime.utcnow()
    db.commit()

    return {
        "status": "success",
        "message": f"PIN {body.pin} verified! Food successfully handed over to {pickup.courier_name}.",
        "pickup_code": pickup.pickup_code,
        "current_status": pickup.current_status
    }

