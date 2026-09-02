# Accessible Multimodal Health & Safety Companion

## Problem
Accessing rapid, structured guidance during minor campus medical emergencies or physical safety hazards can be overwhelming. Standard AI chatbots provide dense paragraphs of text, which are difficult to read under stress.

## Solution
A lightweight, multimodal web application built with Vanilla HTML/JS and Python (FastAPI). It takes text and/or image inputs and returns structured, actionable first-aid and safety guidance. The application includes a "Focus Mode" that strips away unnecessary UI during stressful situations and natively supports multiple languages (English and Hindi).

## Key Features
- **Multimodal Input:** Describe the situation, upload a photo, or both.
- **Client-Side Compression:** Images are compressed in the browser before upload to ensure rapid API response times even on slow campus networks.
- **Structured Guidance:** Actionable step-by-step instructions, clear "Avoid" warnings, and warning signs to watch for.
- **Focus Mode:** A specialized UI toggle that hides non-essential elements and enlarges critical steps and emergency contacts for maximum readability under stress.
- **Local Languages:** One-click translation of safety-critical instructions into Hindi.
- **Emergency Escalation:** Persistent, clear buttons to immediately contact Campus Medical or Security.

## Gemini's Role
We use **Gemini 2.5 Pro** via the official `google-genai` SDK on the backend. Gemini analyzes the multimodal input (text + image) and is strictly prompted to return structured JSON adhering to a Pydantic schema (`SafetyAssessment`). This ensures the UI can reliably render the urgency, summary, actions, and warnings. Gemini is instructed to provide conservative guidance and emphasize professional help for severe incidents.

## Architecture
- **Frontend:** Vanilla HTML5, CSS3, and JavaScript. No build step, no bundlers. Total asset size is under 50KB.
- **Backend:** Python + FastAPI. Serves static files and securely handles the `/api/analyze` endpoint.
- **Validation:** Pydantic is used to enforce the Gemini output schema, while FastAPI handles request payload validation (size limits, MIME types).

## Security Approach
- **Server-Side API:** The Gemini API key is never exposed to the frontend.
- **Payload Validation:** Images are restricted to 5MB and specific MIME types (`image/jpeg`, `image/png`, `image/webp`). Text is capped at 1000 characters.
- **Untrusted Output:** The backend validates Gemini's JSON output before returning it to the client.
- **Safe Fallbacks:** Any API failure results in a safe, generic emergency fallback message.
- **Disclaimer:** The UI clearly separates immediate action steps from professional medical help, explicitly stating when to seek emergency services.

## Accessibility Approach
- **Semantic HTML:** Proper use of `<header>`, `<main>`, `<section>`, and heading hierarchies.
- **ARIA Attributes:** `aria-live="polite"` is used to announce loading states and result rendering to screen readers.
- **Keyboard Navigation:** Explicit `:focus` outlines and fully keyboard-navigable forms and buttons.
- **Contrast & Sizing:** WCAG AAA compliant color contrast. Touch targets are a minimum of 44x44px.
- **Cognitive Accessibility:** "Focus Mode" reduces cognitive load by eliminating visual clutter during emergencies.

## Testing Approach
Testing focuses on the critical user journeys to ensure safety and reliability.
- **Automated Tests:** `test_api.py` uses `pytest` and `FastAPI.testclient` to validate text-only, image-only, multimodal inputs, input limits, invalid file types, and simulated Gemini responses.
- **Manual Verification:** Tested against various scenarios (minor burn, chemical spill, general fall) to ensure proper categorization and language translation.

## Local Setup
1. Clone the repository.
2. Install Python 3.10+
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your Gemini API key:
   ```bash
   GEMINI_API_KEY=your_actual_key
   ```
5. Run the server:
   ```bash
   uvicorn main:app --reload
   ```
6. Open `http://localhost:8000` in your browser.

## Cloud Run Deployment
The project includes a `Dockerfile` optimized for Google Cloud Run.
1. Build the image:
   ```bash
   docker build -t campus-safety-companion .
   ```
2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy campus-safety-companion --image campus-safety-companion --set-env-vars GEMINI_API_KEY=your_actual_key --allow-unauthenticated
   ```

## Safety Disclaimer
*This application is a prototype designed for a hackathon. It provides general first-aid and safety guidance. It is not a substitute for professional medical diagnosis or emergency services. In a true emergency, always contact local emergency services immediately.*
