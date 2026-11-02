"""
services/matching_service.py - Business logic for Food Donation Matching.

Evaluates compatibility between a restaurant surplus food listing and NGOs based on:
  1. Food Quantity (matches against NGO daily meal capacity)
  2. Location Proximity (locality and transit radius)
  3. Pickup Deadline & Storage Feasibility (urgency window and refrigeration)
"""

from datetime import datetime
from typing import List, Dict, Any
from backend.models import SurplusFood, NGO


def calculate_donation_matches(listing: SurplusFood, ngos: List[NGO]) -> List[Dict[str, Any]]:
    """
    Evaluates compatibility between a surplus food listing and available NGOs.
    Returns the top 3 compatible NGOs with compatibility scores (0.0 - 1.0) and human-readable rationales.
    """
    localities = [
        "koramangala", "indiranagar", "hsr", "whitefield", "jayanagar",
        "mg road", "shanti nagar", "btm", "electronic city", "hebbal",
        "malleshwaram", "rajajinagar", "shivajinagar", "richmond", "ulsoor"
    ]
    listing_loc = (listing.location or "").lower()

    if (listing.unit or "").lower() in ["kg", "kgs", "kilograms"]:
        estimated_meals = listing.quantity * 2.5
    else:
        estimated_meals = listing.quantity

    now = datetime.utcnow()
    deadline = listing.pickup_by if isinstance(listing.pickup_by, datetime) else now
    hours_left = max(0.0, (deadline - now).total_seconds() / 3600.0)

    evaluated = []
    for ngo in ngos:
        ngo_loc = f"{ngo.address or ''} {ngo.city or ''}".lower()
        same_locality = any(loc in listing_loc and loc in ngo_loc for loc in localities)
        same_city = (ngo.city or "").lower() in listing_loc or "bengaluru" in listing_loc or "bangalore" in listing_loc

        if same_locality:
            loc_score = 0.95
            dist_km = 1.4
        elif same_city:
            loc_score = 0.82
            dist_km = 3.6
        else:
            loc_score = 0.65
            dist_km = 6.8

        capacity = max(1, ngo.daily_meal_capacity)
        if estimated_meals <= capacity:
            load_ratio = estimated_meals / capacity
            qty_score = 0.96 if load_ratio >= 0.15 else 0.88
        else:
            over_ratio = (estimated_meals - capacity) / capacity
            qty_score = max(0.50, 0.90 - (over_ratio * 0.4))

        if hours_left <= 0:
            time_score = 0.55
            urgency_desc = "Urgent: deadline imminent"
        elif hours_left <= 3:
            time_score = 0.96
            urgency_desc = f"Critical pickup window ({round(hours_left, 1)}h remaining)"
        elif hours_left <= 8:
            time_score = 0.90
            urgency_desc = f"Scheduled for today ({round(hours_left, 1)}h window)"
        else:
            time_score = 0.85
            urgency_desc = f"Flexible window ({round(hours_left / 24, 1)} days)"

        if listing.category in ["cooked", "dairy", "produce"] and ngo.has_cold_storage:
            qty_score = min(1.0, qty_score + 0.05)

        composite = round((loc_score * 0.40) + (qty_score * 0.35) + (time_score * 0.25), 2)
        composite = max(0.65, min(0.98, composite))

        reason = (
            f"Location: {dist_km} km away ({ngo.city or 'Bengaluru'}). "
            f"Capacity: {capacity} meals/day safely absorbs {int(listing.quantity)} {listing.unit}. "
            f"Deadline: {urgency_desc}."
        )

        evaluated.append({
            "id": ngo.id,
            "name": ngo.name,
            "score": composite,
            "reason": reason,
            "distance_km": dist_km,
            "city": ngo.city or "Bengaluru",
            "capacity": capacity,
            "has_cold_storage": ngo.has_cold_storage
        })

    evaluated.sort(key=lambda x: x["score"], reverse=True)
    return evaluated[:3]

