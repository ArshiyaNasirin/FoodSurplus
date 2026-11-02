import sys
from datetime import datetime, timedelta
import random

sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import SurplusFood, NGO, Match, PickupStatus, User

client = TestClient(app)

def run_tests():
    print("=" * 70)
    print("FOODBRIDGE: COMPREHENSIVE END-TO-END VERIFICATION SUITE")
    print("=" * 70)

    print("\n[TEST 1] Testing Health Endpoint & Static Asset Serving...")
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("  ✓ /api/health returned 200 OK:", r.json()["service"])

    r_index = client.get("/")
    assert r_index.status_code == 200, "Frontend index.html serving failed"
    assert "FoodBridge" in r_index.text
    print("  ✓ GET / serves frontend index.html correctly (length:", len(r_index.text), "bytes)")

    r_css = client.get("/css/style.css")
    assert r_css.status_code == 200, "CSS serving failed"
    print("  ✓ GET /css/style.css returned 200 OK (length:", len(r_css.text), "bytes)")

    r_js = client.get("/js/app.js")
    assert r_js.status_code == 200, "JS serving failed"
    assert "confirmDonationMatch" in r_js.text
    print("  ✓ GET /js/app.js returned 200 OK with confirmDonationMatch logic")

    print("\n[TEST 2] Testing User Registration & Authentication...")
    test_email = f"chef_test_{random.randint(1000, 9999)}@bistro.com"
    r_reg = client.post("/api/auth/register", json={
        "name": "Head Chef Marco",
        "email": test_email,
        "password": "password123",
        "role": "donor",
        "user_type": "donor",
        "city": "Bengaluru",
        "location": "Indiranagar 100ft Road"
    })
    assert r_reg.status_code == 201, f"Registration failed: {r_reg.text}"
    user_id = r_reg.json()["id"]
    print(f"  ✓ Registered new donor user ID #{user_id} ({test_email})")

    r_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "password123"
    })
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    token = r_login.json()["access_token"]
    print("  ✓ Logged in and received JWT Bearer token:", token[:25] + "...")

    print("\n[TEST 3] Testing Surplus Food Listing Creation & Listing...")
    deadline = (datetime.utcnow() + timedelta(hours=3.5)).isoformat()
    food_payload = {
        "donor_id": user_id,
        "title": "Fresh Hyderabadi Paneer Biryani & Raita",
        "category": "cooked",
        "quantity": 25.0,
        "unit": "portions",
        "storage_requirement": "hot",
        "target_temp": "65°C",
        "dietary_tags": "veg,halal",
        "location": "12 Green St, 100ft Rd, Indiranagar, Bengaluru",
        "pickup_by": deadline,
        "description": "25 hot sealed meal boxes freshly cooked for corporate lunch, ready for immediate shelter dispatch."
    }
    r_food = client.post("/api/food", json=food_payload)
    assert r_food.status_code == 201, f"Food creation failed: {r_food.text}"
    listing = r_food.json()
    listing_id = listing["id"]
    print(f"  ✓ Created surplus listing #{listing_id}: '{listing['title']}' ({listing['quantity']} {listing['unit']})")
    assert listing["status"] == "available"

    r_avail = client.get("/api/food?status=available")
    assert r_avail.status_code == 200
    avail_ids = [item["id"] for item in r_avail.json()]
    assert listing_id in avail_ids, f"Listing #{listing_id} not found in available listings"
    print(f"  ✓ Listing #{listing_id} confirmed in active inventory (total available: {len(avail_ids)})")

    print("\n[TEST 4] Testing Multi-Factor Donation Matching (Quantity, Location, Deadline)...")
    r_match = client.post("/api/match", json={"listing_id": listing_id})
    assert r_match.status_code == 201, f"Matching failed: {r_match.text}"
    matches = r_match.json()
    assert len(matches) > 0, "No matches generated"
    print(f"  ✓ Generated {len(matches)} suitable recipient NGO matches:")
    for idx, m in enumerate(matches, 1):
        print(f"    Match #{idx}: {m.get('ngo_name') or m.get('recipient_name')} | Compatibility: {int(m['compatibility_score']*100)}%")
        print(f"      Rationale: {m.get('ai_reason')}")
        reason_lower = m.get('ai_reason', '').lower()
        assert "location" in reason_lower or "km" in reason_lower, "Location not in reason"
        assert "capacity" in reason_lower, "Capacity/Quantity not in reason"
        assert "deadline" in reason_lower, "Deadline not in reason"

    selected_match = matches[0]
    match_id = selected_match["id"]
    chosen_ngo_name = selected_match.get("ngo_name") or selected_match.get("recipient_name")

    print(f"\n[TEST 5] Testing Confirm Donation (Accept Match #{match_id})...")
    r_accept = client.put(f"/api/matches/{match_id}/accept")
    assert r_accept.status_code == 200, f"Match acceptance failed: {r_accept.text}"
    accept_data = r_accept.json()
    pickup_code = accept_data["pickup_code"]
    pin = accept_data["verification_pin"]
    print(f"  ✓ Donation confirmed with {chosen_ngo_name}!")
    print(f"    - Generated Pickup Order Code: {pickup_code}")
    print(f"    - Secure 4-Digit Handover PIN: {pin}")

    db = SessionLocal()
    db_match = db.query(Match).filter(Match.id == match_id).first()
    assert db_match.status == "accepted", f"Expected match status 'accepted', got '{db_match.status}'"
    print("  ✓ Database Verification: Match record status updated to 'accepted'")

    db_food = db.query(SurplusFood).filter(SurplusFood.id == listing_id).first()
    assert db_food.status == "claimed", f"Expected surplus food status 'claimed', got '{db_food.status}'"
    print("  ✓ Database Verification: Surplus food listing status updated to 'claimed'")

    db_pickup = db.query(PickupStatus).filter(PickupStatus.pickup_code == pickup_code).first()
    assert db_pickup is not None, "PickupStatus record not found in database"
    assert db_pickup.verification_pin == pin, "Verification PIN mismatch in database"
    print(f"  ✓ Database Verification: PickupStatus #{pickup_code} created with PIN '{pin}' and stage '{db_pickup.current_status}'")
    db.close()

    print("\n[TEST 6] Testing Pickup Logistics Lifecycle & PIN Verification...")
    r_get_pickup = client.get(f"/api/pickups/{pickup_code}")
    assert r_get_pickup.status_code == 200
    p_info = r_get_pickup.json()
    print(f"  ✓ Retrieved shipment details: Courier '{p_info['courier_name']}' ({p_info['vehicle_type']})")

    r_stage = client.put(f"/api/pickups/{pickup_code}/status", json={
        "current_status": "at_restaurant",
        "temperature_reading": "64.2°C (Food Safe)",
        "notes": "Courier arrived at restaurant kitchen"
    })
    assert r_stage.status_code == 200
    print("  ✓ Advanced milestone to 'at_restaurant' with temp 64.2°C")

    r_wrong_pin = client.post(f"/api/pickups/{pickup_code}/verify-pin", json={"pin": "0000"})
    assert r_wrong_pin.status_code == 400, "Wrong PIN should have been rejected"
    print("  ✓ Tested invalid PIN '0000': correctly rejected with 400 Bad Request")

    r_correct_pin = client.post(f"/api/pickups/{pickup_code}/verify-pin", json={"pin": pin})
    assert r_correct_pin.status_code == 200, f"Valid PIN verification failed: {r_correct_pin.text}"
    print(f"  ✓ Tested valid PIN '{pin}': Handover successfully authenticated!")

    r_delivered = client.put(f"/api/pickups/{pickup_code}/status", json={
        "current_status": "delivered",
        "temperature_reading": "61.0°C (Safe Distribution)",
        "notes": "Delivered to community shelter table"
    })
    assert r_delivered.status_code == 200
    print("  ✓ Advanced milestone to 'delivered'")

    db = SessionLocal()
    db_food_final = db.query(SurplusFood).filter(SurplusFood.id == listing_id).first()
    assert db_food_final.status == "completed", f"Expected food status 'completed', got '{db_food_final.status}'"
    print("  ✓ Database Verification: Food listing status auto-updated to 'completed' upon delivery")
    db.close()

    print("\n[TEST 7] Testing Sustainability & Environmental Impact Aggregation...")
    r_impact = client.get("/api/impact/stats")
    assert r_impact.status_code == 200
    impact = r_impact.json()
    print(f"  ✓ Total Food Diverted: {impact['total_kg_saved']} kg")
    print(f"  ✓ Total Meals Rescued: {impact['meals_provided']} meals")
    print(f"  ✓ CO2e Avoided: {impact['co2_saved_kg']} kg")
    print(f"  ✓ Water Conserved: {impact['water_saved_liters']} Liters")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()

