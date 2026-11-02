"""
routers/ngos.py - Endpoints for NGOs, Food Banks, and Community Donation Requests.

Endpoints:
  POST /api/ngos             - Register an NGO / shelter
  GET  /api/ngos             - List registered NGOs (city, cold storage filters)
  GET  /api/ngos/{id}        - Get full details for an NGO
  PUT  /api/ngos/{id}        - Update NGO capacity or operating info
  POST /api/requests         - Submit a community food need request
  GET  /api/requests         - List donation requests (urgency, status, category filters)
  GET  /api/requests/{id}    - Get request details
  PUT  /api/requests/{id}/status - Update request status
  DELETE /api/requests/{id}  - Cancel a donation request
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import NGO, DonationRequest, RequestStatus, RequestUrgency
from backend.schemas import (
    NGOCreate, NGOOut, NGOUpdate,
    DonationRequestCreate, DonationRequestOut, DonationRequestUpdate
)

router = APIRouter(tags=["NGOs & Donation Requests"])



@router.post("/ngos", response_model=NGOOut, status_code=status.HTTP_201_CREATED)
def register_ngo(
    ngo: NGOCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new charitable shelter, food bank, or community kitchen.
    """
    existing_reg = db.query(NGO).filter(NGO.registration_number == ngo.registration_number).first()
    if existing_reg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration number '{ngo.registration_number}' is already registered."
        )

    existing_email = db.query(NGO).filter(NGO.email == ngo.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{ngo.email}' is already registered to another NGO."
        )

    db_ngo = NGO(**ngo.model_dump())
    db.add(db_ngo)
    db.commit()
    db.refresh(db_ngo)
    return db_ngo


@router.get("/ngos", response_model=List[NGOOut])
def list_ngos(
    city: Optional[str] = Query(None, description="Filter by city"),
    has_cold_storage: Optional[bool] = Query(None, description="Filter by refrigeration capacity"),
    verified: Optional[bool] = Query(None, description="Filter by verification status"),
    db: Session = Depends(get_db)
):
    """
    List all registered NGOs, food banks, and shelters.
    """
    query = db.query(NGO)
    if city:
        query = query.filter(NGO.city.ilike(f"%{city}%"))
    if has_cold_storage is not None:
        query = query.filter(NGO.has_cold_storage == has_cold_storage)
    if verified is not None:
        query = query.filter(NGO.verified == verified)
    return query.order_by(NGO.created_at.desc()).all()


@router.get("/ngos/{ngo_id}", response_model=NGOOut)
def get_ngo(ngo_id: int, db: Session = Depends(get_db)):
    """
    Retrieve single NGO profile by ID.
    """
    ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if not ngo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NGO #{ngo_id} not found."
        )
    return ngo


@router.put("/ngos/{ngo_id}", response_model=NGOOut)
def update_ngo(
    ngo_id: int,
    updates: NGOUpdate,
    db: Session = Depends(get_db)
):
    """
    Update NGO operational details (capacity, operating hours, cold storage).
    """
    ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if not ngo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NGO #{ngo_id} not found."
        )

    for field, val in updates.model_dump(exclude_unset=True).items():
        setattr(ngo, field, val)

    ngo.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ngo)
    return ngo



@router.post("/requests", response_model=DonationRequestOut, status_code=status.HTTP_201_CREATED)
def create_donation_request(
    req: DonationRequestCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a specific food need request for an NGO or shelter.
    """
    ngo = db.query(NGO).filter(NGO.id == req.ngo_id).first()
    if not ngo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NGO #{req.ngo_id} not found. Register the NGO first."
        )

    db_req = DonationRequest(**req.model_dump())
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req


@router.get("/requests", response_model=List[DonationRequestOut])
def list_donation_requests(
    ngo_id: Optional[int] = Query(None, description="Filter by NGO ID"),
    status: Optional[str] = Query(None, description="Filter by status (open, matched, fulfilled, cancelled)"),
    urgency: Optional[str] = Query(None, description="Filter by urgency (immediate, high, medium, low)"),
    category: Optional[str] = Query(None, description="Filter by food category needed"),
    db: Session = Depends(get_db)
):
    """
    List community donation requests.
    """
    query = db.query(DonationRequest)
    if ngo_id:
        query = query.filter(DonationRequest.ngo_id == ngo_id)
    if status:
        query = query.filter(DonationRequest.status == status)
    if urgency:
        query = query.filter(DonationRequest.urgency == urgency)
    if category:
        query = query.filter(DonationRequest.category_needed == category)
    return query.order_by(DonationRequest.created_at.desc()).all()


@router.get("/requests/{request_id}", response_model=DonationRequestOut)
def get_donation_request(request_id: int, db: Session = Depends(get_db)):
    """
    Retrieve single donation request by ID.
    """
    req = db.query(DonationRequest).filter(DonationRequest.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation request #{request_id} not found."
        )
    return req


@router.put("/requests/{request_id}/status", response_model=DonationRequestOut)
def update_request_status(
    request_id: int,
    new_status: str = Query(..., description="Target status: open, matched, fulfilled, cancelled"),
    db: Session = Depends(get_db)
):
    """
    Update status of a donation request.
    """
    req = db.query(DonationRequest).filter(DonationRequest.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation request #{request_id} not found."
        )

    valid_statuses = [s.value for s in RequestStatus]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request status '{new_status}'. Allowed: {valid_statuses}"
        )

    req.status = new_status
    req.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(req)
    return req


@router.delete("/requests/{request_id}", status_code=status.HTTP_200_OK)
def delete_donation_request(request_id: int, db: Session = Depends(get_db)):
    """
    Cancel or delete a donation request.
    """
    req = db.query(DonationRequest).filter(DonationRequest.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation request #{request_id} not found."
        )

    db.delete(req)
    db.commit()
    return {"message": f"Donation request #{request_id} deleted", "id": request_id}

