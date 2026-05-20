import os
import json
import random
import string
from datetime import datetime, timedelta

BOOKINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "bookings.json")


def parse_intent(user_input: str) -> dict:
    """Extracts service_type, location, and time from user input using keyword matching."""
    logs = []
    logs.append(f"[INTENT AGENT] Received input: {user_input}")

    text = user_input.lower()

    # Language detection
    urdu_words = ["chahiye", "mujhe", "karo", "hai", "kal", "subah", "mein", "ka", "ki", "ko"]
    if any(w in text for w in urdu_words):
        lang = "Roman Urdu"
    elif any(ord(c) > 1535 for c in user_input):
        lang = "Urdu"
    else:
        lang = "English"
    logs.append(f"[INTENT AGENT] Detected language: {lang}")

    # Service type extraction
    service_map = {
        "AC Technician": ["ac", "air condition", "cooling", "ac technician", "thanda"],
        "Plumber": ["plumber", "plumbing", "pipe", "leak", "paani", "water", "nal"],
        "Electrician": ["electrician", "electric", "wiring", "bijli", "light", "switch"],
        "Tutor": ["tutor", "teacher", "padhai", "study", "math", "science", "ustad"],
        "Beautician": ["beautician", "beauty", "makeup", "salon", "mehndi", "facial"],
        "Carpenter": ["carpenter", "wood", "furniture", "darwaza", "door", "almari", "lakri"]
    }

    service_type = None
    for stype, keywords in service_map.items():
        if any(kw in text for kw in keywords):
            service_type = stype
            break
    logs.append(f"[INTENT AGENT] Extracted service_type: {service_type}")

    # Location extraction
    area_map = {
        "g-13": "G-13", "g13": "G-13",
        "f-7": "F-7", "f7": "F-7",
        "i-8": "I-8", "i8": "I-8",
        "g-11": "G-11", "g11": "G-11",
        "f-6": "F-6", "f6": "F-6",
        "e-7": "E-7", "e7": "E-7",
        "h-13": "H-13", "h13": "H-13",
        "g-9": "G-9", "g9": "G-9",
        "f-10": "F-10", "f10": "F-10",
        "f-11": "F-11", "f11": "F-11",
        "g-8": "G-8", "g8": "G-8",
        "i-9": "I-9", "i9": "I-9"
    }
    location = None
    for key, label in area_map.items():
        if key in text:
            location = label
            break
    if not location:
        location = "G-13"
        logs.append(f"[INTENT AGENT] No location found, defaulting to G-13")
    else:
        logs.append(f"[INTENT AGENT] Extracted location: {location}")

    # Time extraction
    time_val = None
    if "kal" in text or "tomorrow" in text:
        time_val = "Tomorrow"
    elif "aaj" in text or "today" in text:
        time_val = "Today"
    if "subah" in text or "morning" in text:
        time_val = (time_val + " " if time_val else "") + "Morning (9AM-12PM)"
    elif "dopahar" in text or "afternoon" in text:
        time_val = (time_val + " " if time_val else "") + "Afternoon (12PM-3PM)"
    elif "sham" in text or "evening" in text:
        time_val = (time_val + " " if time_val else "") + "Evening (4PM-7PM)"
    if not time_val:
        time_val = "Flexible"
    logs.append(f"[INTENT AGENT] Extracted time: {time_val}")

    return {
        "service_type": service_type,
        "location": location,
        "time": time_val,
        "language": lang,
        "logs": logs
    }


def discover_providers(service_type: str, location: str, all_providers: list) -> dict:
    """Filters providers by service type match."""
    logs = []
    logs.append(f"[DISCOVERY AGENT] Searching for: {service_type} near {location}")

    if not service_type:
        logs.append("[DISCOVERY AGENT] No service type provided, returning empty")
        return {"providers": [], "logs": logs}

    filtered = [
        p for p in all_providers
        if p["service_type"].lower() == service_type.lower()
    ]

    if not filtered:
        logs.append("[DISCOVERY AGENT] No exact match found. Expanding search to nearby categories.")
        sorted_providers = sorted(all_providers, key=lambda x: x.get("rating", 0), reverse=True)
        filtered = sorted_providers[:2]
        logs.append(f"[DISCOVERY AGENT] DECISION: Returning top {len(filtered)} highest rated providers overall as fallback.")

    logs.append(f"[DISCOVERY AGENT] Found {len(filtered)} providers: {[p['name'] for p in filtered]}")
    return {"providers": filtered, "logs": logs}


def rank_providers(providers: list) -> dict:
    logs = []
    logs.append(f"[RANKING AGENT] Evaluating {len(providers)} candidates")
    logs.append(f"[RANKING AGENT] Decision criteria: proximity to user location, service rating, slot availability")
    logs.append(f"[RANKING AGENT] Applying weighted scoring model")
    logs.append("[RANKING AGENT] Formula: (1/distance * 0.4) + (rating/5 * 0.4) + (slots/3 * 0.2)")

    ranked = []
    for p in providers:
        dist_score = (1 / (p["distance_from_g13_km"] + 0.1)) * 0.4
        rating_score = (p["rating"] / 5.0) * 0.4
        slots_score = (len(p["available_slots"]) / 3.0) * 0.2
        total_score = round(dist_score + rating_score + slots_score, 3)

        reasoning = (
            f"Distance {p['distance_from_g13_km']}km (score: {round(dist_score,3)}) + "
            f"Rating {p['rating']}★ (score: {round(rating_score,3)}) + "
            f"{len(p['available_slots'])} slots (score: {round(slots_score,3)})"
        )

        p_copy = dict(p)
        p_copy["score"] = total_score
        p_copy["reasoning"] = reasoning
        ranked.append(p_copy)
        logs.append(f"[RANKING AGENT] {p['name']}: total score = {total_score}")

    ranked.sort(key=lambda x: x["score"], reverse=True)
    for i, p in enumerate(ranked):
        logs.append(f"[RANKING AGENT] Rank {i+1}: {p['name']} ({p['score']})")

    logs.append(f"[RANKING AGENT] DECISION: Recommending {ranked[0]['name']} — highest composite score of {ranked[0]['score']}")
    logs.append(f"[RANKING AGENT] Reasoning: {ranked[0]['reasoning']}")

    return {"ranked": ranked, "logs": logs}


def simulate_booking(provider: dict, time_slot: str, service_type: str) -> dict:
    """Creates a confirmed booking and writes to bookings.json."""
    logs = []
    booking_id = "BK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    logs.append(f"[BOOKING AGENT] Generating booking ID: {booking_id}")

    booking = {
        "booking_id": booking_id,
        "provider_name": provider["name"],
        "provider_phone": provider.get("phone", "N/A"),
        "provider_area": provider.get("area", "N/A"),
        "service_type": service_type,
        "slot": time_slot,
        "price_per_hour": provider.get("price_per_hour", 0),
        "status": "confirmed",
        "timestamp": datetime.now().isoformat()
    }

    logs.append(f"[BOOKING AGENT] Provider assigned: {provider['name']}")
    logs.append(f"[BOOKING AGENT] Slot confirmed: {time_slot}")

    try:
        bookings = []
        if os.path.exists(BOOKINGS_FILE):
            with open(BOOKINGS_FILE, "r") as f:
                try:
                    bookings = json.load(f)
                except Exception:
                    bookings = []
        bookings.append(booking)
        with open(BOOKINGS_FILE, "w") as f:
            json.dump(bookings, f, indent=4)
        logs.append(f"[BOOKING AGENT] Booking written to bookings.json")
    except Exception as e:
        logs.append(f"[BOOKING AGENT] File error: {str(e)}")

    confirmation = (
        f"Booking {booking_id} confirmed! {service_type} with {provider['name']} "
        f"at {time_slot}. Contact: {provider.get('phone', 'N/A')}. "
        f"Rate: PKR {provider.get('price_per_hour', 0)}/hr"
    )

    return {
        "booking": booking,
        "confirmation_message": confirmation,
        "logs": logs
    }


def schedule_followup(booking: dict, reminder_minutes: int = 60) -> dict:
    logs = []
    logs.append(f"[FOLLOWUP AGENT] Scheduling reminder for booking {booking['booking_id']}")

    try:
        slot_time = datetime.strptime(booking["slot"], "%I:%M %p")
        reminder_time = (slot_time - timedelta(minutes=reminder_minutes)).strftime("%I:%M %p")
        logs.append(f"[FOLLOWUP AGENT] Reminder set for {reminder_time} ({reminder_minutes} mins before {booking['slot']})")

        if os.path.exists(BOOKINGS_FILE):
            with open(BOOKINGS_FILE, "r") as f:
                bookings = json.load(f)
            for b in bookings:
                if b["booking_id"] == booking["booking_id"]:
                    b["reminder"] = reminder_time
                    b["reminder_minutes"] = reminder_minutes
                    break
            with open(BOOKINGS_FILE, "w") as f:
                json.dump(bookings, f, indent=4)
            logs.append(f"[FOLLOWUP AGENT] Reminder saved to bookings.json")

        return {
            "reminder_time": reminder_time,
            "message": f"Reminder scheduled at {reminder_time}, {reminder_minutes} minutes before your appointment.",
            "logs": logs
        }

    except Exception as e:
        logs.append(f"[FOLLOWUP AGENT] Error: {str(e)}")
        return {
            "reminder_time": None,
            "message": "Reminder could not be scheduled",
            "logs": logs
        }


def update_booking_status(booking_id: str, status: str) -> dict:
    """Updates the status of an existing booking in bookings.json."""
    logs = []
    allowed_statuses = ["confirmed", "provider_notified", "en_route", "completed"]

    if status not in allowed_statuses:
        logs.append(f"[STATUS AGENT] Invalid status requested: {status}")
        return {
            "success": False,
            "message": f"Invalid status. Must be one of: {', '.join(allowed_statuses)}",
            "logs": logs
        }

    logs.append(f"[STATUS AGENT] Request to update booking {booking_id} to '{status}'")

    if not os.path.exists(BOOKINGS_FILE):
        logs.append("[STATUS AGENT] bookings.json does not exist")
        return {"success": False, "message": "No bookings file found.", "logs": logs}

    try:
        with open(BOOKINGS_FILE, "r") as f:
            bookings = json.load(f)

        booking_found = False
        updated_booking = None

        for b in bookings:
            if b["booking_id"] == booking_id:
                old_status = b.get("status", "unknown")
                b["status"] = status
                b["last_updated"] = datetime.now().isoformat()
                updated_booking = b
                booking_found = True
                logs.append(f"[STATUS AGENT] Transition: {old_status} -> {status}")
                break

        if not booking_found:
            logs.append(f"[STATUS AGENT] Booking {booking_id} not found")
            return {"success": False, "message": f"Booking {booking_id} not found.", "logs": logs}

        with open(BOOKINGS_FILE, "w") as f:
            json.dump(bookings, f, indent=4)

        logs.append(f"[STATUS AGENT] Successfully updated status and saved to disk")
        return {"success": True, "booking": updated_booking, "logs": logs}

    except Exception as e:
        logs.append(f"[STATUS AGENT] Critical error: {str(e)}")
        return {"success": False, "message": str(e), "logs": logs}