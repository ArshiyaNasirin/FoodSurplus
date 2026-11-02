"""
routers/food.py - CRUD Endpoints for Food Surplus Listings.

Endpoints:
  POST /api/food           - Create a surplus food listing
  GET  /api/food           - List surplus food with search, category, status, and dietary filters
  GET  /api/food/{id}      - Retrieve full details of a specific listing
  PUT  /api/food/{id}      - Update an existing listing
  PUT  /api/food/{id}/status - Update listing status (available, matched, claimed, completed)
  DELETE /api/food/{id}    - Remove a listing
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database import get_db
from backend.models import SurplusFood, FoodListing, User, FoodStatus
from backend.schemas import (
    SurplusFoodCreate, SurplusFoodOut, SurplusFoodUpdate,
    FoodListingCreate, FoodListingOut
)

router = APIRouter(prefix="/food", tags=["Food Surplus Listings"])


@router.post("", response_model=SurplusFoodOut, status_code=status.HTTP_201_CREATED)
def create_listing(
    listing: SurplusFoodCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new surplus food listing.
    Enforces positive quantity, future pickup deadline, and category validation.
    """
    donor = db.query(User).filter(User.id == listing.donor_id).first()
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donor user with ID {listing.donor_id} not found."
        )

    db_listing = SurplusFood(**listing.model_dump())
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing


@router.get("", response_model=List[SurplusFoodOut])
def list_food(
    status: Optional[str] = Query(None, description="Filter by status (available, matched, claimed, completed)"),
    category: Optional[str] = Query(None, description="Filter by food category (cooked, bakery, produce, dairy, raw, packaged)"),
    donor_id: Optional[int] = Query(None, description="Filter by donor user ID"),
    search: Optional[str] = Query(None, description="Search term for title, description, or location"),
    dietary: Optional[str] = Query(None, description="Filter by dietary tag (e.g. veg, vegan, halal, gluten_free)"),
    db: Session = Depends(get_db)
):
    """
    List food listings with multi-attribute filtering, search, and sorting.
    """
    query = db.query(SurplusFood)

    if status:
        query = query.filter(SurplusFood.status == status)
    if category:
        query = query.filter(SurplusFood.category == category)
    if donor_id:
        query = query.filter(SurplusFood.donor_id == donor_id)
    if dietary:
        query = query.filter(SurplusFood.dietary_tags.ilike(f"%{dietary}%"))
    if search:
        s = f"%{search}%"
        query = query.outerjoin(User, SurplusFood.donor_id == User.id).filter(
            or_(
                SurplusFood.title.ilike(s),
                SurplusFood.description.ilike(s),
                SurplusFood.location.ilike(s),
                SurplusFood.category.ilike(s),
                SurplusFood.dietary_tags.ilike(s),
                User.name.ilike(s)
            )
        )

    return query.order_by(SurplusFood.created_at.desc()).all()


@router.get("/{listing_id}", response_model=SurplusFoodOut)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """
    Retrieve single food listing by ID.
    """
    listing = db.query(SurplusFood).filter(SurplusFood.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surplus food listing #{listing_id} not found."
        )
    return listing


@router.put("/{listing_id}", response_model=SurplusFoodOut)
def update_listing(
    listing_id: int,
    updates: SurplusFoodUpdate,
    db: Session = Depends(get_db)
):
    """
    Update listing information (quantity, deadline, storage conditions, description).
    """
    listing = db.query(SurplusFood).filter(SurplusFood.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surplus food listing #{listing_id} not found."
        )

    for field, val in updates.model_dump(exclude_unset=True).items():
        setattr(listing, field, val)

    listing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(listing)
    return listing


@router.put("/{listing_id}/status", response_model=SurplusFoodOut)
def update_status(
    listing_id: int,
    new_status: str = Query(..., description="Target status: available, matched, claimed, completed, expired"),
    db: Session = Depends(get_db)
):
    """
    Update status of a food listing.
    """
    listing = db.query(SurplusFood).filter(SurplusFood.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surplus food listing #{listing_id} not found."
        )

    valid_statuses = [s.value for s in FoodStatus]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{new_status}'. Allowed: {valid_statuses}"
        )

    listing.status = new_status
    listing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/{listing_id}", status_code=status.HTTP_200_OK)
def delete_listing(listing_id: int, db: Session = Depends(get_db)):
    """
    Delete a surplus food listing.
    """
    listing = db.query(SurplusFood).filter(SurplusFood.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surplus food listing #{listing_id} not found."
        )

    db.delete(listing)
    db.commit()
    return {"message": f"Listing #{listing_id} successfully deleted", "id": listing_id}
