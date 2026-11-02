# 🌱 FoodBridge — Intelligent Food Surplus & Community Platform

A streamlined, reliable web platform connecting commercial food donors (restaurants, bakeries, caterers) with verified NGOs, shelters, and food banks to eliminate food waste and support communities.

Built strictly using **HTML, CSS, JavaScript, Python, FastAPI, and SQLite**.

---

## 🏛️ Clean Architecture & Project Structure

The project follows a clean layered architecture with clear separation of concerns across database models, validation schemas, business logic services, API routers, and single-page frontend:

```
FoodSurplus/
├── backend/
│   ├── main.py                         # FastAPI app entry point, CORS, router mounting, static serving
│   ├── database.py                     # SQLite engine, thread-safe session generator, table initializer
│   ├── models.py                       # SQLAlchemy ORM models (User, NGO, SurplusFood, Matches, Pickups, Chat)
│   ├── schemas.py                      # Pydantic request & response validation schemas
│   ├── services/                       # Pure Business Logic Layer
│   │   ├── __init__.py
│   │   ├── matching_service.py         # Multi-factor matching algorithm (Quantity, Location, Deadline)
│   │   └── chat_service.py             # Food safety, zero-waste recipes, and donor legal guidelines
│   └── routers/                        # API Endpoint Route Controllers
│       ├── __init__.py
│       ├── auth.py                     # User registration, login, JWT token authentication
│       ├── food.py                     # Surplus food inventory CRUD, category & urgency filtering
│       ├── ngos.py                     # NGO profiles and community food need requests
│       ├── matching.py                 # Donation match scoring & acceptance endpoints
│       ├── pickup.py                   # 6-stage logistics tracking & 4-digit PIN verification
│       ├── impact.py                   # Aggregated sustainability, CO2e, and water diversion metrics
│       └── chat.py                     # Conversational assistant endpoints with session memory
├── frontend/
│   ├── index.html                      # Single-page application with collapsible sidebar & role views
│   ├── css/
│   │   └── style.css                   # Clean neutral UI design system (slate/charcoal) & responsive layout
│   ├── js/
│   │   └── app.js                      # SPA routing, API integration, live donation matching, modals
│   └── images/
│       └── hero-bg.jpg                 # Background banner asset
├── foodresq.db                         # SQLite persistent database
├── init_database.py                    # Standalone database reset & seed data script
├── test_comprehensive_workflow.py      # Automated end-to-end verification test suite
├── requirements.txt                    # Lean production dependencies (no bloated/unused packages)
├── start.bat                           # One-click Windows startup script
├── .env                                # Local environment configuration
└── README.md                           # Documentation
```

---

## ✨ Core Features & Workflows

1. **User Authentication & Role Management** (`/api/auth`):
   - Secure PBKDF2-HMAC-SHA256 password hashing.
   - JWT access tokens with 24-hour expiration.
   - Participant roles: Restaurant/Donor, NGO/Shelter, Volunteer Courier, Coordinator.

2. **Surplus Food Inventory** (`/api/food`):
   - Real-time inventory of perishable surplus with portion counts, storage conditions, and pickup deadlines.
   - Dynamic search filters by category (`cooked`, `bakery`, `produce`, `dairy`, `raw`, `packaged`), status (`available`, `claimed`, `completed`), and dietary tags (`veg`, `vegan`, `halal`, `gluten-free`).

3. **Multi-Factor Food Donation Matching** (`/api/match`):
   - **Factor 1: Food Quantity & Meal Capacity (35% weight)**: Matches surplus volume against the NGO's daily meal capacity and cold storage infrastructure.
   - **Factor 2: Location Proximity (40% weight)**: Measures locality proximity and transit radius between restaurant and shelter.
   - **Factor 3: Pickup Deadline & Urgency (25% weight)**: Evaluates remaining time before spoilage to prevent food waste.
   - **Human-Readable Rationales**: Clear explanations detailing why each NGO is recommended.

4. **Donation Confirmation & Pickup Dispatch** (`/api/matches/{id}/accept`):
   - Restaurant or admin confirms the match with one click.
   - Automatically updates Match status to `accepted` and Surplus Food to `claimed`.
   - Generates an active `PickupStatus` shipment with a unique order code (`PK-XXXX`) and a secure **4-digit verification PIN**.

5. **Logistics & Handover Verification** (`/api/pickups`):
   - 6-stage milestone tracker: `claimed` ➔ `driver_assigned` ➔ `at_restaurant` ➔ `pin_verified` ➔ `in_transit` ➔ `delivered`.
   - Temperature compliance logging (hot-holding >= 60°C, chilled <= 4°C).
   - Food handover PIN authentication preventing unauthorized pickups.
   - Final delivery milestone auto-completes the food listing.

6. **Impact & Sustainability Reports** (`/api/impact`):
   - Quantified metrics: Total meals rescued, edible kilograms diverted from landfills, $\text{CO}_2\text{e}$ prevented, and water conserved.
   - Instant printable Verified Impact Certificates for donors.

7. **FoodResQ Assistant** (`/api/chat`):
   - Domain-specific culinary upcycling recipes, FSSAI / Good Samaritan food donation liability protections, and microbial safety protocols.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ installed

### 1. Run via Windows Batch Script (Easiest)
Simply double-click:
```powershell
start.bat
```

### 2. Run Manually via Command Line
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Re-seed demonstration database
python init_database.py

# 3. Start the FastAPI application
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open in Browser
- **Web Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc Docs**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Running Automated Tests

Run the complete end-to-end verification suite anytime to confirm database operations, authentication, surplus creation, matching, acceptance, and pickup tracking:
```powershell
python test_comprehensive_workflow.py
```
