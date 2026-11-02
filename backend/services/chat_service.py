"""
services/chat_service.py - FoodResQ Conversational AI Service.

Provides:
  - Food waste reduction & kitchen optimization guidance
  - Safe storage temperatures (chilled <= 4°C, hot-holding >= 60°C)
  - Zero-waste culinary repurposing recipes
  - Good Samaritan & FSSAI donor liability protections
  - Multi-tier provider support: Cloud API (xAI/OpenAI), Local Ollama, and built-in domain knowledge
"""

import os
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are FoodBridge, an intelligent sustainability and food surplus management assistant.

Core Expertise:
🥗 Food Waste Reduction & Kitchen Optimization
🤝 Connecting Food Donors (Restaurants, Caterers) with Verified NGOs & Shelters
📦 Cold-chain Logistics & Safe Preservation Temperatures (Chilled <= 4°C, Hot-holding >= 60°C)
🌱 Environmental Impact Metrics (CO2 emission diversion, water footprint conservation)
🍳 Creative Zero-Waste Recipes & Repurposing for Surplus Perishables
⚖️ Food Safety Liability Protections & Legal Donor Guidelines (Good Samaritan Protections)
"""

DOMAIN_KNOWLEDGE_BASE = [
    {
        "keywords": ["rice", "cooked rice", "chawal", "leftover rice", "spoilage"],
        "reply": (
            "🍚 **Safe Leftover Cooked Rice Handling Protocol**:\n\n"
            "• **Immediate Chilling**: Bacillus cereus spores can survive boiling. Cool cooked rice rapidly within 1 hour and refrigerate immediately.\n"
            "• **Temperature**: Keep below **4°C (40°F)**. Never leave cooked rice at room temperature for over 2 hours.\n"
            "• **Shelf-life**: Consume or donate within **24 to 48 hours**.\n"
            "• **Reheating**: Reheat only once to a core steaming temperature of at least **74°C (165°F)**.\n"
            "• **Culinary Reuse**: Perfect for Asian-style egg fried rice, crispy rice cakes, or vegetable arancini balls."
        )
    },
    {
        "keywords": ["legal", "liability", "protection", "law", "good samaritan", "fssai", "safety"],
        "reply": (
            "🛡️ **Donor Legal Protections & Food Safety Regulations**:\n\n"
            "• **Good Samaritan Protection**: In India, the FSSAI (Recovery and Distribution of Surplus Food) Regulations, 2019 protects food donors donating in good faith from civil and criminal liability.\n"
            "• **Hygiene Obligations**: Food must remain safe at the point of donation (packaged cleanly, within shelf-life, and maintained at required holding temperature).\n"
            "• **Chain of Custody**: Once handed over with 4-digit PIN verification to an accredited NGO, custody transitions to the recipient charity.\n"
            "• **Tax Benefit**: Donors are eligible for CSR documentation and verified sustainability certificates through FoodBridge."
        )
    },
    {
        "keywords": ["sourdough", "bread", "bakery", "roti", "stale bread"],
        "reply": (
            "🍞 **Creative Zero-Waste Sourdough & Bakery Upcycling**:\n\n"
            "• **Garlic Herb Croutons**: Toss cubed stale sourdough in olive oil, crushed garlic, and sea salt; bake at 180°C for 12 minutes.\n"
            "• **Classic Tuscan Panzanella**: Soak rustic cubes in red wine vinegar and extra virgin olive oil with heirloom tomatoes, basil, and cucumbers.\n"
            "• **Golden Panko / Breadcrumbs**: Pulse dried crusts in a processor; freeze in airtight jars for up to 6 months for crispy toppings.\n"
            "• **Caramel Bread Pudding**: Soak sourdough chunks in cinnamon custard with raisins; bake until golden and puffed."
        )
    },
    {
        "keywords": ["hot food", "temperature", "holding", "transport", "guidelines", "celsius"],
        "reply": (
            "🌡️ **Hot-Holding & Transport Safety Protocols**:\n\n"
            "• **Holding Temperature**: Hot cooked food must be maintained at **>= 60°C (140°F)** throughout storage and dispatch.\n"
            "• **Danger Zone**: 5°C to 60°C is the danger zone where bacteria multiply rapidly. Avoid lingering in this zone.\n"
            "• **Transport Window**: Hot food in insulated transit containers (cambros) must reach the NGO distribution point within **4 hours**.\n"
            "• **Verification**: Log core temperature upon pickup and upon delivery using our live courier tracker."
        )
    },
    {
        "keywords": ["match", "matching", "ngo", "shelter", "donate", "pickup"],
        "reply": (
            "🤝 **How FoodBridge Donation Matching Works**:\n\n"
            "1. **List Surplus**: Head to the **Food Listings** page and post details (category, quantity, pickup deadline, storage temp).\n"
            "2. **AI Compatibility**: Our matching engine evaluates nearby registered NGOs based on beneficiary count, daily capacity, and cold-chain readiness.\n"
            "3. **Accept & Schedule**: Accept the optimal match to generate an instant 4-digit pickup verification PIN.\n"
            "4. **Live Logistics**: Track the courier's insulated delivery progress and confirm handover with PIN verification."
        )
    }
]


def normalize_provider_name(provider: Optional[str]) -> str:
    p = (provider or "xai").lower().strip()
    return "ollama" if "ollama" in p or "qwen" in p else "xai"


def is_fallback_enabled() -> bool:
    val = os.getenv("AI_FALLBACK_ENABLED", "true").lower()
    return val not in ("false", "0", "no")


def get_all_providers_info() -> List[Dict[str, Any]]:
    xai_configured = bool(os.getenv("XAI_API_KEY"))
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    ollama_online = False
    try:
        r = httpx.get(f"{ollama_url}/api/tags", timeout=1.0)
        ollama_online = r.status_code == 200
    except Exception:
        ollama_online = False

    default_p = normalize_provider_name(os.getenv("DEFAULT_AI_PROVIDER", "xai"))

    return [
        {
            "id": "xai",
            "name": "xAI Grok",
            "type": "cloud",
            "model": "grok-beta",
            "endpoint": "https://api.x.ai/v1",
            "available": xai_configured,
            "status_message": "Configured (Cloud API)" if xai_configured else "Requires XAI_API_KEY in .env",
            "is_default": default_p == "xai"
        },
        {
            "id": "ollama",
            "name": "Ollama (Qwen 2.5)",
            "type": "local",
            "model": "qwen2.5:latest",
            "endpoint": ollama_url,
            "available": ollama_online,
            "status_message": "Running (Local Port 11434)" if ollama_online else "Offline (Start Ollama locally)",
            "is_default": default_p == "ollama"
        }
    ]


def _match_domain_knowledge(query: str) -> Optional[str]:
    q = query.lower()
    for entry in DOMAIN_KNOWLEDGE_BASE:
        if any(kw in q for kw in entry["keywords"]):
            return entry["reply"]
    return None


def get_ai_response_sync(
    user_input: str,
    history: Optional[List[Dict[str, str]]] = None,
    provider: Optional[str] = "xai",
    allow_fallback: bool = True
) -> Dict[str, Any]:
    """
    Generate an assistant reply using the requested provider or domain knowledge base.
    """
    resolved_p = normalize_provider_name(provider)

    if resolved_p == "ollama":
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            r = httpx.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": "qwen2.5:latest",
                    "prompt": f"{SYSTEM_PROMPT}\n\nUser: {user_input}\nAssistant:",
                    "stream": False
                },
                timeout=10.0
            )
            if r.status_code == 200:
                reply = r.json().get("response", "").strip()
                if reply:
                    return {
                        "reply": reply,
                        "model_used": "qwen2.5:latest",
                        "provider_used": "ollama",
                        "status": "success"
                    }
        except Exception:
            pass

    if resolved_p == "xai":
        api_key = os.getenv("XAI_API_KEY")
        if api_key:
            try:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                if history:
                    for h in history[-4:]:
                        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                messages.append({"role": "user", "content": user_input})

                r = httpx.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers=headers,
                    json={"model": "grok-beta", "messages": messages, "temperature": 0.3},
                    timeout=10.0
                )
                if r.status_code == 200:
                    reply = r.json()["choices"][0]["message"]["content"].strip()
                    return {
                        "reply": reply,
                        "model_used": "grok-beta",
                        "provider_used": "xai",
                        "status": "success"
                    }
            except Exception:
                pass

    matched_reply = _match_domain_knowledge(user_input)
    if not matched_reply:
        matched_reply = (
            "🌱 **FoodBridge Assistant**:\n\n"
            "Surplus food should be categorized, packaged in food-grade containers, and posted promptly on the platform. "
            "Our multi-factor matching engine connects your surplus with nearby verified shelters based on portion quantity, "
            "neighborhood proximity, and pickup deadline to eliminate food waste."
        )

    return {
        "reply": matched_reply,
        "model_used": "Domain Knowledge Base (Offline Resilient)",
        "provider_used": "domain_rules",
        "status": "fallback",
        "fallback_notice": "Offline resilient domain intelligence active."
    }
