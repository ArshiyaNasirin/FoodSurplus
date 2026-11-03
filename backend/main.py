"""
main.py - FoodResQ AI FastAPI Application Entry Point.

Features:
  - Full OpenAPI / Swagger UI interactive documentation at /docs
  - ReDoc alternative API documentation at /redoc
  - Modular Routers:
      • /api/auth    - JWT authentication, password hashing, and user roles
      • /api/food    - Food surplus listings CRUD & search filters
      • /api/ngos    - NGO registrations & community donation requests
      • /api/match   - Multi-factor AI donation matching (LangGraph)
      • /api/pickups - Logistics tracking & 4-digit verification PIN handoff
      • /api/impact  - Sustainability, carbon diversion, and certification metrics
      • /api/chat    - Conversational assistant with Grok & Qwen
  - Static file hosting for frontend HTML, CSS, and JS
"""

import sys
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from backend.database import init_db
from backend.routers import auth, food, ngos, matching, pickup, impact, chat, db_viewer



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize SQLite database tables on server startup."""
    init_db()
    print("[OK] FoodBridge Database connected and ready!")
    yield
    print("[INFO] FoodBridge server shutdown.")



app = FastAPI(
    title="FoodBridge API",
    description=(
        "Comprehensive REST API for the FoodBridge Platform.\n\n"
        "Features:\n"
        "• **Authentication**: JWT token bearer auth and PBKDF2 password hashing\n"
        "• **Surplus Food Listings**: Real-time inventory, category, and urgency filtering\n"
        "• **NGOs & Requests**: Shelter profiles, cold-chain capacity, and food need submissions\n"
        "• **Food Donation Matching**: Multi-factor compatibility scoring (Quantity, Location, Pickup Deadline)\n"
        "• **Pickup Logistics**: 6-stage milestone tracker with secure 4-digit PIN verification\n"
        "• **Impact Reports**: Carbon diversion, meal equivalents, and verified sustainability certificates\n"
        "• **Conversational Assistant**: Resilient guidance on food safety, recipes, and donor regulations"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    swagger_ui_parameters={"defaultModelsExpandDepth": 1, "persistAuthorization": True}
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(auth.router,     prefix="/api")
app.include_router(food.router,     prefix="/api")
app.include_router(ngos.router,     prefix="/api")
app.include_router(matching.router, prefix="/api")
app.include_router(pickup.router,   prefix="/api")
app.include_router(impact.router,   prefix="/api")
app.include_router(chat.router,     prefix="/api")
app.include_router(db_viewer.router)



@app.get("/api/health", tags=["System Health"])
def health_check():
    """Verify backend API and database operational status."""
    return {
        "status": "healthy",
        "service": "FoodBridge Backend",
        "version": "2.0.0",
        "database": "SQLite (foodresq.db)",
        "docs": "/docs"
    }



frontend_path = os.path.join(base_dir, "frontend")
css_path = os.path.join(frontend_path, "css")
js_path = os.path.join(frontend_path, "js")
images_path = os.path.join(frontend_path, "images")

if os.path.isdir(css_path):
    app.mount("/css", StaticFiles(directory=css_path), name="css")
if os.path.isdir(js_path):
    app.mount("/js", StaticFiles(directory=js_path), name="js")
if os.path.isdir(images_path):
    app.mount("/images", StaticFiles(directory=images_path), name="images")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
def serve_index():
    """Serve the single-page application frontend."""
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "FoodBridge API is running. Visit /docs for API documentation."}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
