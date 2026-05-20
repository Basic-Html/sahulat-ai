# Sahulat.ai — 5-Agent Pipeline Implementation Plan

## Goal Description
Implement an agentic AI system that automates the end-to-end lifecycle of service booking for Islamabad's informal economy. The system will take natural language requests (English, Urdu, Roman Urdu) and orchestrate 5 specialized AI agents to process the intent, discover providers, rank them, confirm the booking, and schedule a follow-up.

## Architecture & Data Contracts

### 1. Intent Agent
- **Input**: Raw user text in any language
- **Process**: Keyword matching across English, Urdu, Roman Urdu vocabularies (with Gemini API fallback)
- **Output**: `service_type`, `location`, `time`, `detected_language`

### 2. Discovery Agent
- **Input**: `service_type`, `location`
- **Process**: Filters mock dataset (`data/providers.json`) by service category match. Fallback expands search to nearby categories if no exact match.
- **Output**: Filtered provider list with count

### 3. Ranking Agent
- **Input**: Filtered provider list
- **Process**: Weighted scoring formula:
  - Distance score: (1 / distance+0.1) × 0.4
  - Rating score: (rating / 5.0) × 0.4
  - Availability score: (slots / 3.0) × 0.2
- **Output**: Ranked list with scores and reasoning per provider

### 4. Booking Agent
- **Input**: Selected provider, time slot, service type
- **Process**: Generates unique booking ID (e.g., BK-XAUH), writes confirmed booking to `bookings.json`
- **Output**: Booking object with ID, provider, slot, status, timestamp

### 5. Followup Agent
- **Input**: Booking object, `reminder_minutes` (30 / 60 / 120)
- **Process**: Calculates reminder time, updates booking record in database
- **Output**: Reminder time, confirmation message

## Verification Plan
- Send test queries in Urdu and Roman Urdu.
- Verify fallback triggered for missing locations.
- Verify `bookings.json` updates correctly upon successful booking.
