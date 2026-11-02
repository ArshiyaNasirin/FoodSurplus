"""
routers/matching.py - AI & Heuristic Donation Matching Endpoints.

Endpoints:
  POST /api/match              - Run multi-factor matching for a surplus food listing
  GET  /api/matches            - List match records (filters by status, listing, NGO)
  GET  /api/matches/{id}       - Get single match details
  PUT  /api/matches/{id}/accept  - Accept match, mark food claimed & auto-generate pickup order
  PUT  /api/matches/{id}/status - Update match status (accepted, rejected, cancelled)
"""

from datetime import datetime, timedelta
import random
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    SurplusFood, FoodListing, NGO, User,
    Match, MatchStatus, FoodStatus,
    PickupStatus, PickupStage
)
from backend.schemas import AIMatchRequest, MatchOut, MatchStatusUpdate
from backend.services.matching_service import calculate_donation_matches

router = APIRouter(tags=["AI Donation Matching"])


@router.post("/match", response_model=List[MatchOut], status_code=status.HTTP_201_CREATED)
def create_matches(
    request: AIMatchRequest,
    db: Session = Depends(get_db)
):
    """
    Run multi-factor donation matching for a surplus food listing.
    Connects restaurants with suitable NGOs based on:
      - Food quantity (matches NGO daily meal capacity)
      - Location (neighborhood proximity)
      - Pickup deadline (urgency and storage feasibility)
    """
    listing = db.query(SurplusFood).filter(SurplusFood.id == request.listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surplus food listing #{request.listing_id} not found."
        )

    ngos = db.query(NGO).filter(NGO.verified == True).all()
    if not ngos:
        ngos = db.query(NGO).all()

    if not ngos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recipient NGOs registered yet in the system."
        )

    top_matches = calculate_donation_matches(listing, ngos)

    saved_matches = []
    for match_data in top_matches:
        recipient_id = match_data.get("id")
        score = match_data.get("score", 0.85)
        reason = match_data.get("reason", "Optimal beneficiary capacity match.")

        db_match = Match(
            surplus_food_id=listing.id,
            listing_id=listing.id,
            ngo_id=recipient_id,
            recipient_id=recipient_id,
            compatibility_score=score,
            score=score,
            ai_reasoning=reason,
            ai_reason=reason,
            status=MatchStatus.PENDING.value
        )
        db.add(db_match)
        saved_matches.append(db_match)

    db.commit()
    for m in saved_matches:
        db.refresh(m)

    return saved_matches


@router.get("/matches", response_model=List[MatchOut])
def list_matches(
    status: Optional[str] = Query(None, description="Filter by status (pending, accepted, rejected, cancelled)"),
    listing_id: Optional[int] = Query(None, description="Filter by surplus food listing ID"),
    ngo_id: Optional[int] = Query(None, description="Filter by NGO ID"),
    min_score: Optional[float] = Query(None, description="Filter by minimum compatibility score (0.0 to 1.0)"),
    db: Session = Depends(get_db)
):
    """
    List all generated match records with optional filters.
    """
    query = db.query(Match)
    if status:
        query = query.filter(Match.status == status)
    if listing_id:
        query = query.filter((Match.surplus_food_id == listing_id) | (Match.listing_id == listing_id))
    if ngo_id:
        query = query.filter((Match.ngo_id == ngo_id) | (Match.recipient_id == ngo_id))
    if min_score is not None:
        query = query.filter(Match.compatibility_score >= min_score)
    return query.order_by(Match.created_at.desc()).all()


@router.get("/matches/{match_id}", response_model=MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)):
    """
    Retrieve single match details by ID.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match #{match_id} not found."
        )
    return match


@router.put("/matches/{match_id}/accept", status_code=status.HTTP_200_OK)
def accept_match(match_id: int, db: Session = Depends(get_db)):
    """
    Recipient accepts match:
      1. Updates match status to 'accepted'.
      2. Updates corresponding surplus food listing to 'claimed'.
      3. Automatically generates an active PickupStatus shipment record with 4-digit verification PIN.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match #{match_id} not found."
        )

    match.status = MatchStatus.ACCEPTED.value
    match.accepted_at = datetime.utcnow()

    food = db.query(SurplusFood).filter(
        (SurplusFood.id == match.surplus_food_id) | (SurplusFood.id == match.listing_id)
    ).first()
    if food:
        food.status = FoodStatus.CLAIMED.value

    existing_pickup = db.query(PickupStatus).filter(PickupStatus.match_id == match.id).first()

    if existing_pickup:
        pickup_code = existing_pickup.pickup_code
        pin = existing_pickup.verification_pin
    else:
        pickup_code = f"PK-{random.randint(1000, 9999)}"
        pin = f"{random.randint(1000, 9999)}"
        if food:
            courier = db.query(User).filter(User.role == "courier").first()
            new_pickup = PickupStatus(
                pickup_code=pickup_code,
                match_id=match.id,
                surplus_food_id=food.id,
                ngo_id=match.ngo_id or 1,
                courier_id=courier.id if courier else None,
                courier_name=courier.name if courier else "Assigned Volunteer Courier",
                courier_phone=courier.phone if courier else "+91 98450 12345",
                vehicle_type="Electric Cargo Van (Insulated)",
                verification_pin=pin,
                current_status=PickupStage.CLAIMED.value,
                temperature_reading="Pending Pickup Inspection",
                estimated_arrival=datetime.utcnow() + timedelta(minutes=25),
                notes="Courier dispatched. Exchange 4-digit PIN upon arrival."
            )
            db.add(new_pickup)

    db.commit()
    return {
        "message": "Match accepted successfully! Pickup shipment generated.",
        "match_id": match.id,
        "pickup_code": pickup_code,
        "verification_pin": pin
    }


@router.put("/matches/{match_id}/status", response_model=MatchOut)
def update_match_status(
    match_id: int,
    status_update: MatchStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update match status (accepted, rejected, cancelled).
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match #{match_id} not found."
        )

    match.status = status_update.status
    if status_update.status == MatchStatus.ACCEPTED.value:
        match.accepted_at = datetime.utcnow()

    db.commit()
    db.refresh(match)
    return match
