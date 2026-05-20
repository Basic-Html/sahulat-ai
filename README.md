# Sahulat.ai — AI Service Orchestrator for Islamabad's Informal Economy

# What It Does
Sahulat.ai is an agentic AI system that automates the end-to-end lifecycle of service
booking for Islamabad's informal economy. Instead of searching through WhatsApp groups
and phone calls, users describe what they need in English, Urdu, or Roman Urdu — and
five specialized AI agents handle everything from understanding the request to confirming
a booking and scheduling a follow-up reminder.

---

# System Architecture

```
User Input (English / Urdu / Roman Urdu)
        ↓
[INTENT AGENT] — Extracts service type, location, time
        ↓
[DISCOVERY AGENT] — Filters providers by service category
        ↓
[RANKING AGENT] — Scores providers by distance, rating, availability
        ↓
[BOOKING AGENT] — Simulates booking, writes to database, generates confirmation
        ↓
[FOLLOWUP AGENT] — Schedules reminder at user-selected interval
```

**Tech Stack:**
- Backend: Python 3.11, FastAPI
- Frontend: HTML, CSS, JavaScript (PWA-ready)
- Map: Leaflet.js with OpenStreetMap + CartoDB tiles
- Storage: JSON flat-file database (bookings.json)
- NLP: Keyword-based multilingual intent extraction with Gemini API fallback
- Development: Google Antigravity IDE with Gemini 3 Pro

---

# How Google Antigravity Was Used

Antigravity served as the central orchestration and development platform:

- **Architecture Design**: Used Antigravity Plan Mode to design the 5-agent pipeline
  before writing any code. The agent sequence, data contracts, and log format were
  all planned as a task artifact inside Antigravity.
- **Code Generation**: All agent modules generated and iterated inside Antigravity
  using Gemini 3 Pro. Each agent was prompted, reviewed, and refined through the
  Antigravity agent chat.
- **Multi-step Reasoning**: Antigravity managed the reasoning flow across agents —
  each agent receives structured output from the previous one, creating a traceable
  decision chain.
- **Tool Integration**: Antigravity terminal used to install dependencies, run the
  server, and debug errors autonomously. Import conflicts and syntax errors were
  identified and resolved by the agent.
- **Workflow Execution**: The complete planning → decision → action → follow-up
  pipeline was designed, built, and tested entirely within Antigravity.
- **Model**: Gemini 3 Pro (Antigravity) + Gemini 2.0 Flash (API fallback for NLP)

---

# Agent Pipeline Detail

# Agent 1: Intent Agent
- Input: Raw user text in any language
- Process: Keyword matching across English, Urdu, Roman Urdu vocabularies
- Output: service_type, location, time, detected language
- Logs: Language detection, field extraction, defaults applied

# Agent 2: Discovery Agent
- Input: service_type, location
- Process: Filters mock dataset by service category match
- Fallback: If no exact match, expands search to nearby categories
- Output: Filtered provider list with count
- Logs: Search criteria, providers found, fallback triggered if needed

# Agent 3: Ranking Agent
- Input: Filtered provider list
- Process: Weighted scoring formula:
  - Distance score: (1 / distance+0.1) × 0.4
  - Rating score: (rating / 5.0) × 0.4
  - Availability score: (slots / 3.0) × 0.2
- Output: Ranked list with scores and reasoning per provider
- Logs: Score breakdown per provider, final ranking decision

# Agent 4: Booking Agent
- Input: Selected provider, time slot, service type
- Process: Generates unique booking ID, writes confirmed booking to bookings.json
- Output: Booking object with ID, provider, slot, status, timestamp
- Logs: Booking ID generated, provider assigned, slot confirmed, database updated

# Agent 5: Followup Agent
- Input: Booking object, reminder_minutes (30 / 60 / 120)
- Process: Calculates reminder time, updates booking record in database
- Output: Reminder time, confirmation message
- Logs: Reminder scheduled, database updated

---

# Data Schema

# Provider Object
```json
{
  "id": 1,
  "name": "Ali Hassan",
  "service_type": "AC Technician",
  "area": "G-13",
  "lat": 33.6493,
  "long": 72.9692,
  "distance_from_g13_km": 0.0,
  "rating": 4.8,
  "available_slots": ["9:00 AM", "11:00 AM", "2:00 PM"],
  "phone": "0300-1234567",
  "price_per_hour": 1500,
  "experience_years": 7,
  "bio": "Certified AC technician with 200+ clients served.",
  "jobs_completed": 214
}
```

# Booking Object
```json
{
  "booking_id": "BK-XAUH",
  "provider_name": "Ali Hassan",
  "provider_phone": "0300-1234567",
  "provider_area": "G-13",
  "service_type": "AC Technician",
  "slot": "9:00 AM",
  "price_per_hour": 1500,
  "status": "confirmed",
  "timestamp": "2026-05-19T10:00:00",
  "reminder": "08:00 AM",
  "reminder_minutes": 60,
  "status_updated_at": "2026-05-19T10:05:00"
}
```

---

# APIs and Tools Used

| Tool | Purpose |
|---|---|
| Google Antigravity | Development, orchestration, agent design |
| Gemini 3 Pro | Code generation and iteration inside Antigravity |
| Gemini 2.0 Flash API | NLP intent parsing (with keyword fallback) |
| FastAPI | REST API backend |
| Leaflet.js | Interactive map with provider markers |
| CartoDB Tiles | Dark/light map themes |
| OpenStreetMap | Map data |
| DM Sans / DM Mono | Typography |

---

# Setup Steps

```bash
# 1. Install Python 3.11 from python.org

# 2. Install dependencies
python -m pip install fastapi uvicorn google-generativeai python-dotenv pydantic aiofiles

# 3. Run the server
python run.py

# 4. Open in browser
http://localhost:8000
```

---

# Baseline Comparison

| Feature | Traditional (WhatsApp/Calls) | Sahulat.ai |
|---|---|---|
| Service discovery | Manual search, ask friends | Automated in under 1 second |
| Provider matching | Gut feeling, no criteria | Weighted scoring algorithm |
| Multi-language | Depends on person | English, Urdu, Roman Urdu |
| Booking | Phone call, no confirmation | Instant confirmation with unique ID |
| Follow-up | User has to remember | Automated reminder at chosen interval |
| Reasoning visible | None | Full agent trace logged and displayed |
| Edge case handling | Human judgment | Graceful fallback with error message |

A simple heuristic system would return the closest provider with no scoring,
no reasoning, no logging, and no follow-up automation. Sahulat.ai adds
weighted multi-criteria ranking, traceable decisions, a complete booking
lifecycle, and real database state change on every booking.

---

# Robustness Evidence

- **Invalid input**: Typing gibberish returns a graceful error from Intent Agent
  with a clear message — pipeline stops cleanly without crashing
- **No provider found**: Discovery Agent falls back to top-rated providers
  across all categories and logs the fallback decision
- **Missing location**: Intent Agent defaults to G-13 and logs the assumption
- **API quota exceeded**: System falls back to keyword-based NLP automatically
  with no user-facing error

---

# Cost and Scalability

**Current cost per request:**
- Intent parsing: ~$0 (keyword matching, no API call)
- Provider matching and ranking: ~$0 (local computation)
- Booking simulation: ~$0 (local JSON write)
- Total: effectively $0 per request

**With Gemini API enabled:**
- ~$0.00015 per intent parsing call (Gemini 2.0 Flash pricing)
- 1,000 requests/day = ~$0.15/day

**Scaling to 10x (1,000 daily users):**
- FastAPI handles concurrent async requests natively
- Replace bookings.json with PostgreSQL (minimal code change)
- Add Redis caching for provider dataset
- Estimated cost: ~$1.50/day
- Latency: under 500ms per request

**Scaling to 100x (10,000 daily users):**
- Deploy on Google Cloud Run with auto-scaling
- Provider dataset moves to Firestore
- Gemini API batch processing for intent parsing
- Estimated cost: ~$15/day
- Latency target: under 2 seconds end-to-end

---

# Privacy Note

- All provider data is fully synthetic mock data
- No real personal information is stored or transmitted
- Booking records contain only provider names and time slots
- No user authentication or personal data collection
- No cookies, tracking, or analytics

---

# Assumptions and Limitations

- Provider dataset is mocked with 12 providers across 6 service categories
- All providers are based in Islamabad — system is not generalized to other cities
- Distance values are pre-calculated from G-13, not computed dynamically
- Notifications are simulated — no real SMS or push notification is sent
- Language detection uses keyword matching, not a full NLP model
- Booking slots are not checked for conflicts in this version