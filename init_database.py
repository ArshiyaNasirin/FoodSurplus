"""
init_database.py - Database Initializer & Seed Script for FoodResQ AI.

This script:
1. Creates the SQLite database using SQLAlchemy with foreign keys enabled.
2. Creates all 6 required tables:
   - users
   - ngos
   - surplus_food
   - donation_requests
   - matches
   - pickup_status
   (plus chat_messages)
3. Verifies relationships and runs comprehensive validation test cases.
4. Seeds rich, realistic demonstration data across all tables.
5. Prints a complete summary report with row counts and relational traversals.
"""

from datetime import datetime, timedelta
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select, inspect
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database import sync_engine, SyncSessionLocal, Base, init_sync_db
from backend.routers.auth import hash_password
from backend.models import (
    User, UserRole,
    NGO,
    SurplusFood, FoodCategory, FoodStatus,
    DonationRequest, RequestUrgency, RequestStatus,
    Match, MatchStatus,
    PickupStatus, PickupStage,
    ChatMessage
)


def create_database_schema():
    """Build all tables in SQLite database via SQLAlchemy Base metadata."""
    print("=================================================================")
    print("  🌱 FoodResQ AI - SQLAlchemy SQLite Database Setup")
    print("=================================================================")
    print("Dropping existing tables and rebuilding schema...")
    Base.metadata.drop_all(bind=sync_engine)
    init_sync_db()

    inspector = inspect(sync_engine)
    tables = inspector.get_table_names()
    print(f"✅ Created {len(tables)} tables: {', '.join(tables)}")

    for t in tables:
        cols = [c["name"] for c in inspector.get_columns(t)]
        fks = [f"{fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}" for fk in inspector.get_foreign_keys(t)]
        fk_str = f" | FKs: {', '.join(fks)}" if fks else ""
        print(f"  • {t:18} ({len(cols)} columns: {', '.join(cols[:5])}...{fk_str})")
    print()


def test_model_validations():
    """Verify that SQLAlchemy @validates and CheckConstraints reject invalid data."""
    print("Testing Model Validations...")

    try:
        User(name="Invalid User", email="not-an-email", phone="1234567890", role="donor")
        print("  ❌ Failed: User email validation did not trigger!")
    except ValueError as e:
        print(f"  ✅ Validation passed: Rejected invalid email ({e})")

    try:
        SurplusFood(
            donor_id=1,
            title="Expired Bread",
            category="bakery",
            quantity=-5.0,
            unit="kg",
            location="City Center",
            pickup_by=datetime.utcnow() + timedelta(hours=2)
        )
        print("  ❌ Failed: SurplusFood quantity validation did not trigger!")
    except ValueError as e:
        print(f"  ✅ Validation passed: Rejected non-positive quantity ({e})")

    try:
        Match(
            surplus_food_id=1,
            ngo_id=1,
            compatibility_score=1.85,
            status="pending"
        )
        print("  ❌ Failed: Match score validation did not trigger!")
    except ValueError as e:
        print(f"  ✅ Validation passed: Rejected invalid compatibility score ({e})")

    try:
        PickupStatus(
            pickup_code="PK-TEST",
            match_id=1,
            surplus_food_id=1,
            ngo_id=1,
            verification_pin="12",
            current_status="claimed"
        )
        print("  ❌ Failed: Pickup PIN validation did not trigger!")
    except ValueError as e:
        print(f"  ✅ Validation passed: Rejected invalid PIN length ({e})")

    try:
        NGO(
            name="Test NGO",
            registration_number="REG-1234",
            contact_person="Person",
            email="ngo@test.org",
            phone="9876543210",
            address="Test St",
            daily_meal_capacity=-20
        )
        print("  ❌ Failed: NGO negative capacity validation did not trigger!")
    except ValueError as e:
        print(f"  ✅ Validation passed: Rejected negative meal capacity ({e})")

    print()


def seed_database():
    """Populate database with rich demonstration records demonstrating all relationships."""
    print("Seeding database with realistic sample data...")
    session: Session = SyncSessionLocal()

    try:
        existing_users = session.query(User).count()
        if existing_users > 0:
            print(f"Database already contains {existing_users} users. Refreshing seed data...")
            session.query(PickupStatus).delete()
            session.query(Match).delete()
            session.query(DonationRequest).delete()
            session.query(SurplusFood).delete()
            session.query(NGO).delete()
            session.query(User).delete()
            session.commit()

        default_pwd = hash_password("password123")
        rest1 = User(
            name="The Green Bistro",
            email="contact@greenbistro.com",
            hashed_password=default_pwd,
            phone="+91 98450 11223",
            role=UserRole.DONOR.value,
            address="12 Green St, 100ft Rd, Indiranagar",
            city="Bengaluru"
        )
        rest2 = User(
            name="Royal Spice Restaurant",
            email="contact@royalspice.in",
            hashed_password=default_pwd,
            phone="+91 98451 22334",
            role=UserRole.DONOR.value,
            address="45 MG Road, Brigade Junction",
            city="Bengaluru"
        )
        rest3 = User(
            name="Fresh Bites Kitchen",
            email="hello@freshbiteskitchen.com",
            hashed_password=default_pwd,
            phone="+91 98452 33445",
            role=UserRole.DONOR.value,
            address="78 80ft Rd, Koramangala 4th Block",
            city="Bengaluru"
        )
        rest4 = User(
            name="Spice Garden",
            email="manager@spicegarden.com",
            hashed_password=default_pwd,
            phone="+91 98453 44556",
            role=UserRole.DONOR.value,
            address="19 Residency Road, Central District",
            city="Bengaluru"
        )
        rest5 = User(
            name="Urban Tiffin House",
            email="orders@urbantiffin.in",
            hashed_password=default_pwd,
            phone="+91 98454 55667",
            role=UserRole.DONOR.value,
            address="102 Outer Ring Road, Bellandur",
            city="Bengaluru"
        )
        rest6 = User(
            name="Annapoorna Restaurant",
            email="service@annapoornarestaurant.in",
            hashed_password=default_pwd,
            phone="+91 98455 66778",
            role=UserRole.DONOR.value,
            address="33 Gandhi Bazaar Main Rd, Basavanagudi",
            city="Bengaluru"
        )
        rest7 = User(
            name="Golden Crust Bakery",
            email="bake@goldencrustbakery.com",
            hashed_password=default_pwd,
            phone="+91 98456 77889",
            role=UserRole.DONOR.value,
            address="15 Commercial Street, Tasker Town",
            city="Bengaluru"
        )
        courier1 = User(
            name="Rajesh Kumar",
            email="rajesh.courier@foodresq.org",
            hashed_password=default_pwd,
            phone="+91 98450 12345",
            role=UserRole.COURIER.value,
            address="Indiranagar Transit Depot",
            city="Bengaluru"
        )
        courier2 = User(
            name="Priya Sharma",
            email="priya.sharma@foodresq.org",
            hashed_password=default_pwd,
            phone="+91 97411 67890",
            role=UserRole.COURIER.value,
            address="Koramangala Hub",
            city="Bengaluru"
        )
        session.add_all([rest1, rest2, rest3, rest4, rest5, rest6, rest7, courier1, courier2])
        session.flush()

        ngo1 = NGO(
            name="City Hope Food Bank",
            registration_number="NGO-KA-2021-0891",
            contact_person="Sarah Mathew",
            email="coordinator@cityhope.org",
            phone="+91 99001 88776",
            address="14 Hope Plaza, 5th Block, Koramangala",
            city="Bengaluru",
            daily_meal_capacity=600,
            has_cold_storage=True,
            operating_hours="07:00 - 23:00",
            verified=True
        )
        ngo2 = NGO(
            name="Helping Hands Foundation",
            registration_number="NGO-KA-2019-0412",
            contact_person="David Paul",
            email="support@helpinghands.org",
            phone="+91 99002 77665",
            address="56 Victoria Rd, Shanti Nagar",
            city="Bengaluru",
            daily_meal_capacity=350,
            has_cold_storage=True,
            operating_hours="08:00 - 22:00",
            verified=True
        )
        ngo3 = NGO(
            name="Care & Share Trust",
            registration_number="NGO-KA-2018-0244",
            contact_person="Sister Mary",
            email="care@caresharetrust.org",
            phone="+91 99004 55443",
            address="9 Ashram Rd, Whitefield",
            city="Bengaluru",
            daily_meal_capacity=200,
            has_cold_storage=True,
            operating_hours="08:00 - 20:00",
            verified=True
        )
        session.add_all([ngo1, ngo2, ngo3])
        session.flush()

        food1 = SurplusFood(
            donor_id=rest1.id,
            title="Surplus Vegetable Biryani & Paneer Curry",
            description="Fresh catering surplus from corporate luncheon. Prepared at 1:30 PM. Stored in hot-holding thermal carriers.",
            category=FoodCategory.COOKED.value,
            quantity=18.0,
            unit="kg",
            storage_requirement="hot",
            target_temp="60°C",
            dietary_tags="veg, halal",
            location=rest1.address,
            pickup_by=datetime.utcnow() + timedelta(hours=3),
            status=FoodStatus.AVAILABLE.value
        )
        food2 = SurplusFood(
            donor_id=rest1.id,
            title="Farm Fresh Organic Greek Yogurt & Paneer Blocks",
            description="Sealed vacuum packs of fresh cottage cheese paneer and pasteurized natural Greek yogurt tubs.",
            category=FoodCategory.DAIRY.value,
            quantity=15.0,
            unit="kg",
            storage_requirement="chilled",
            target_temp="4°C",
            dietary_tags="veg",
            location=rest1.address,
            pickup_by=datetime.utcnow() + timedelta(hours=14),
            status=FoodStatus.AVAILABLE.value
        )
        food3 = SurplusFood(
            donor_id=rest1.id,
            title="Assorted Whole Wheat Vegetable Wraps & Rolls",
            description="Individually wrapped rolls filled with spiced grilled veggies, mint chutney, and paneer.",
            category=FoodCategory.COOKED.value,
            quantity=30.0,
            unit="portions",
            storage_requirement="ambient",
            target_temp="20°C",
            dietary_tags="veg",
            location=rest1.address,
            pickup_by=datetime.utcnow() + timedelta(hours=4),
            status=FoodStatus.CLAIMED.value
        )

        food4 = SurplusFood(
            donor_id=rest2.id,
            title="Mughlai Paneer Butter Masala & Roti Platter",
            description="Rich royal paneer butter masala paired with fresh tandoori rotis. Kept in hot-holding units.",
            category=FoodCategory.COOKED.value,
            quantity=25.0,
            unit="portions",
            storage_requirement="hot",
            target_temp="65°C",
            dietary_tags="veg, halal",
            location=rest2.address,
            pickup_by=datetime.utcnow() + timedelta(hours=2),
            status=FoodStatus.AVAILABLE.value
        )
        food5 = SurplusFood(
            donor_id=rest2.id,
            title="Dum Pukht Fragrant Jeera Rice & Dal Makhani",
            description="Slow-cooked black lentils in butter and cream served with fragrant cumin basmati rice.",
            category=FoodCategory.COOKED.value,
            quantity=30.0,
            unit="portions",
            storage_requirement="hot",
            target_temp="65°C",
            dietary_tags="veg, gluten_free, halal",
            location=rest2.address,
            pickup_by=datetime.utcnow() + timedelta(hours=3),
            status=FoodStatus.AVAILABLE.value
        )

        food6 = SurplusFood(
            donor_id=rest3.id,
            title="Mediterranean Quinoa Bowls & Roasted Vegetables",
            description="Protein-packed quinoa bowls with grilled bell peppers, zucchini, hummus, and lemon herb dressing.",
            category=FoodCategory.COOKED.value,
            quantity=20.0,
            unit="portions",
            storage_requirement="chilled",
            target_temp="4°C",
            dietary_tags="vegan, veg, gluten_free",
            location=rest3.address,
            pickup_by=datetime.utcnow() + timedelta(hours=5),
            status=FoodStatus.AVAILABLE.value
        )
        food7 = SurplusFood(
            donor_id=rest3.id,
            title="Organic Tomatoes, Cucumbers & Bell Peppers",
            description="Surplus organic produce crates, crisp and farm-fresh. Ideal for community soup kitchen stew.",
            category=FoodCategory.PRODUCE.value,
            quantity=40.0,
            unit="kg",
            storage_requirement="chilled",
            target_temp="8°C",
            dietary_tags="vegan, veg, gluten_free",
            location=rest3.address,
            pickup_by=datetime.utcnow() + timedelta(hours=36),
            status=FoodStatus.AVAILABLE.value
        )

        food8 = SurplusFood(
            donor_id=rest4.id,
            title="South Indian Sambar, Rasam & Steamed Rice",
            description="Authentic drumstick vegetable sambar, pepper rasam, and steamed sona masoori rice.",
            category=FoodCategory.COOKED.value,
            quantity=40.0,
            unit="portions",
            storage_requirement="hot",
            target_temp="65°C",
            dietary_tags="veg, gluten_free",
            location=rest4.address,
            pickup_by=datetime.utcnow() + timedelta(hours=2),
            status=FoodStatus.AVAILABLE.value
        )
        food9 = SurplusFood(
            donor_id=rest4.id,
            title="Crispy Medu Vada & Coconut Chutney Packs",
            description="Freshly fried lentil vadas packed in food-grade insulated parcels with grated coconut chutney.",
            category=FoodCategory.COOKED.value,
            quantity=35.0,
            unit="portions",
            storage_requirement="ambient",
            target_temp="20°C",
            dietary_tags="veg",
            location=rest4.address,
            pickup_by=datetime.utcnow() + timedelta(hours=4),
            status=FoodStatus.AVAILABLE.value
        )

        food10 = SurplusFood(
            donor_id=rest5.id,
            title="Homestyle Dal Tadka & Phulka Roti Tiffins",
            description="Yellow lentil tadka cooked with cumin, ginger, and garlic alongside 100 soft wheat phulkas.",
            category=FoodCategory.COOKED.value,
            quantity=50.0,
            unit="portions",
            storage_requirement="hot",
            target_temp="60°C",
            dietary_tags="veg",
            location=rest5.address,
            pickup_by=datetime.utcnow() + timedelta(hours=3.5),
            status=FoodStatus.AVAILABLE.value
        )
        food11 = SurplusFood(
            donor_id=rest5.id,
            title="Mixed Vegetable Pulao & Cucumber Raita",
            description="Mildly spiced basmati rice tossed with garden peas, carrots, beans, and fresh curd raita.",
            category=FoodCategory.COOKED.value,
            quantity=30.0,
            unit="portions",
            storage_requirement="hot",
            target_temp="60°C",
            dietary_tags="veg",
            location=rest5.address,
            pickup_by=datetime.utcnow() + timedelta(hours=2.5),
            status=FoodStatus.AVAILABLE.value
        )

        food12 = SurplusFood(
            donor_id=rest6.id,
            title="Traditional Bisi Bele Bath & Boondi",
            description="Karnataka specialty lentil rice dish loaded with vegetables, ghee tadka, and crispy kara boondi.",
            category=FoodCategory.COOKED.value,
            quantity=35.0,
            unit="kg",
            storage_requirement="hot",
            target_temp="65°C",
            dietary_tags="veg, gluten_free",
            location=rest6.address,
            pickup_by=datetime.utcnow() + timedelta(hours=3),
            status=FoodStatus.AVAILABLE.value
        )
        food13 = SurplusFood(
            donor_id=rest6.id,
            title="Steamed Idli & Podi Breakfast Trays",
            description="Fluffy steamed rice and lentil cakes served with spiced gun powder (podi) and sesame oil.",
            category=FoodCategory.COOKED.value,
            quantity=60.0,
            unit="portions",
            storage_requirement="hot",
            target_temp="60°C",
            dietary_tags="veg, vegan",
            location=rest6.address,
            pickup_by=datetime.utcnow() + timedelta(hours=4),
            status=FoodStatus.AVAILABLE.value
        )

        food14 = SurplusFood(
            donor_id=rest7.id,
            title="Fresh Artisan Sourdough Loaves & Croissants",
            description="Morning artisanal bake surplus with sourdough country loaves, baguettes, and butter croissants in kraft packaging.",
            category=FoodCategory.BAKERY.value,
            quantity=25.0,
            unit="portions",
            storage_requirement="ambient",
            target_temp="Room Temp",
            dietary_tags="veg",
            location=rest7.address,
            pickup_by=datetime.utcnow() + timedelta(hours=8),
            status=FoodStatus.AVAILABLE.value
        )
        food15 = SurplusFood(
            donor_id=rest7.id,
            title="Whole Wheat Multi-Grain Bread & Bagels",
            description="Nutritious multi-grain bread loaves, flax seed bagels, and dinner rolls packed fresh.",
            category=FoodCategory.BAKERY.value,
            quantity=40.0,
            unit="portions",
            storage_requirement="ambient",
            target_temp="Room Temp",
            dietary_tags="vegan, veg",
            location=rest7.address,
            pickup_by=datetime.utcnow() + timedelta(hours=12),
            status=FoodStatus.AVAILABLE.value
        )
        food16 = SurplusFood(
            donor_id=rest7.id,
            title="Assorted Brioche Buns & Danish Pastries",
            description="Golden brioche slider buns and custard-filled Danish pastries in bakery boxes.",
            category=FoodCategory.BAKERY.value,
            quantity=20.0,
            unit="portions",
            storage_requirement="ambient",
            target_temp="Room Temp",
            dietary_tags="veg",
            location=rest7.address,
            pickup_by=datetime.utcnow() + timedelta(hours=6),
            status=FoodStatus.AVAILABLE.value
        )

        session.add_all([
            food1, food2, food3, food4, food5, food6, food7, food8,
            food9, food10, food11, food12, food13, food14, food15, food16
        ])
        session.flush()

        req1 = DonationRequest(
            ngo_id=ngo1.id,
            title="Need 120 Cooked Dinner Meals for Koramangala Night Shelter",
            category_needed=FoodCategory.COOKED.value,
            quantity_needed=120.0,
            unit="portions",
            urgency=RequestUrgency.IMMEDIATE.value,
            beneficiary_count=120,
            target_date=datetime.utcnow() + timedelta(hours=4),
            status=RequestStatus.OPEN.value,
            notes="Homeless residents evening dinner service at Koramangala Shelter."
        )
        req2 = DonationRequest(
            ngo_id=ngo2.id,
            title="Bakery Bread & Breakfast Supplies for 80 Community Residents",
            category_needed=FoodCategory.BAKERY.value,
            quantity_needed=80.0,
            unit="portions",
            urgency=RequestUrgency.HIGH.value,
            beneficiary_count=80,
            target_date=datetime.utcnow() + timedelta(hours=16),
            status=RequestStatus.OPEN.value,
            notes="Morning community breakfast table at Shanti Nagar community hall."
        )
        req3 = DonationRequest(
            ngo_id=ngo3.id,
            title="Bulk Fresh Produce & Meals for 60 Children and Seniors",
            category_needed=FoodCategory.PRODUCE.value,
            quantity_needed=50.0,
            unit="kg",
            urgency=RequestUrgency.HIGH.value,
            beneficiary_count=60,
            target_date=datetime.utcnow() + timedelta(days=1),
            status=RequestStatus.OPEN.value,
            notes="Wholesome vegetable stew and nourishment program in Whitefield."
        )
        session.add_all([req1, req2, req3])
        session.flush()

        match1 = Match(
            surplus_food_id=food1.id,
            ngo_id=ngo1.id,
            request_id=req1.id,
            compatibility_score=0.96,
            ai_reasoning="Immediate proximity (1.4 km) meets urgent 2-hour cooked meal expiry. Evening shelter service feeds 120 at 7:30 PM.",
            status=MatchStatus.ACCEPTED.value,
            accepted_at=datetime.utcnow() - timedelta(minutes=25)
        )
        match2 = Match(
            surplus_food_id=food14.id,
            ngo_id=ngo2.id,
            request_id=req2.id,
            compatibility_score=0.92,
            ai_reasoning="Fresh bakery shelf-life matches scheduled morning breakfast distribution window for 80 residents.",
            status=MatchStatus.ACCEPTED.value,
            accepted_at=datetime.utcnow() - timedelta(minutes=10)
        )
        match3 = Match(
            surplus_food_id=food4.id,
            ngo_id=ngo3.id,
            request_id=req3.id,
            compatibility_score=0.89,
            ai_reasoning="Hot royal paneer platter ready for immediate evening child nutrition service in Whitefield.",
            status=MatchStatus.ACCEPTED.value,
            accepted_at=datetime.utcnow() - timedelta(minutes=5)
        )
        session.add_all([match1, match2, match3])
        session.flush()

        pickup1 = PickupStatus(
            pickup_code="PK-8921",
            match_id=match1.id,
            surplus_food_id=food1.id,
            ngo_id=ngo1.id,
            courier_id=courier1.id,
            courier_name=courier1.name,
            courier_phone=courier1.phone,
            vehicle_type="Electric Cargo Van (Temp Controlled)",
            verification_pin="7842",
            current_status=PickupStage.AT_RESTAURANT.value,
            temperature_reading="63.5°C",
            estimated_arrival=datetime.utcnow() + timedelta(minutes=15),
            notes="Courier arrived at The Green Bistro kitchen. Insulated bags verified. Ready for chef PIN exchange."
        )
        pickup2 = PickupStatus(
            pickup_code="PK-4412",
            match_id=match2.id,
            surplus_food_id=food14.id,
            ngo_id=ngo2.id,
            courier_id=courier2.id,
            courier_name=courier2.name,
            courier_phone=courier2.phone,
            vehicle_type="Eco Cargo E-Bike",
            verification_pin="3190",
            current_status=PickupStage.IN_TRANSIT.value,
            temperature_reading="Room Temp (22°C)",
            estimated_arrival=datetime.utcnow() + timedelta(minutes=20),
            notes="En route from Golden Crust Bakery to Helping Hands Foundation in Shanti Nagar."
        )
        pickup3 = PickupStatus(
            pickup_code="PK-7731",
            match_id=match3.id,
            surplus_food_id=food4.id,
            ngo_id=ngo3.id,
            courier_id=courier1.id,
            courier_name=courier1.name,
            courier_phone=courier1.phone,
            vehicle_type="Insulated Transit Van",
            verification_pin="5524",
            current_status=PickupStage.DRIVER_ASSIGNED.value,
            temperature_reading="65.0°C",
            estimated_arrival=datetime.utcnow() + timedelta(minutes=30),
            notes="Dispatched from Royal Spice Restaurant to Care & Share Trust in Whitefield."
        )
        session.add_all([pickup1, pickup2, pickup3])
        session.commit()

        print("✅ Database seeding completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"❌ Error during seeding: {e}")
        raise e
    finally:
        session.close()


def verify_relationships():
    """Verify that SQLAlchemy object relationships navigate seamlessly across foreign keys."""
    print()
    print("Verifying Object Relationships & Traversal...")
    session: Session = SyncSessionLocal()

    try:
        donor = session.query(User).filter(User.email == "contact@greenbistro.com").first()
        print(f"  • User '{donor.name}' has {len(donor.surplus_foods)} surplus food listings:")
        for sf in donor.surplus_foods:
            print(f"    - [{sf.category.upper()}] {sf.title} ({sf.quantity} {sf.unit})")

        biryani = session.query(SurplusFood).filter(SurplusFood.title.like("%Biryani%")).first()
        print(f"\n  • Surplus Food '{biryani.title}' matches:")
        for m in biryani.matches:
            print(f"    - Matched to NGO '{m.ngo.name}' (Score: {m.compatibility_score * 100:.0f}%)")
            print(f"      AI Reasoning: {m.ai_reasoning}")
            if m.pickup:
                print(f"      Associated Pickup: #{m.pickup.pickup_code} | Stage: {m.pickup.current_status} | PIN: {m.pickup.verification_pin}")
                print(f"      Courier: {m.pickup.courier.name} ({m.pickup.courier.phone})")

        hope_ngo = session.query(NGO).filter(NGO.name == "City Hope Food Bank").first()
        print(f"\n  • NGO '{hope_ngo.name}' has {len(hope_ngo.donation_requests)} active requests:")
        for req in hope_ngo.donation_requests:
            print(f"    - Need: {req.title} (Urgency: {req.urgency.upper()}, Feeds: {req.beneficiary_count} people)")

        print()
        print("-----------------------------------------------------------------")
        print("  📊 Database Summary (foodresq.db)")
        print("-----------------------------------------------------------------")
        print(f"  Users:             {session.query(User).count()} rows")
        print(f"  NGOs:              {session.query(NGO).count()} rows")
        print(f"  Surplus Food:      {session.query(SurplusFood).count()} rows")
        print(f"  Donation Requests: {session.query(DonationRequest).count()} rows")
        print(f"  Matches:           {session.query(Match).count()} rows")
        print(f"  Pickup Status:     {session.query(PickupStatus).count()} rows")
        print("=================================================================")

    finally:
        session.close()


if __name__ == "__main__":
    create_database_schema()
    test_model_validations()
    seed_database()
    verify_relationships()
