import os
import json
import urllib.request
import urllib.error
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# Load .env manually since python-dotenv is not installed
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class SafetyHandler(SimpleHTTPRequestHandler):
    """Local HTTP Server handler for the Campus Safety Companion API."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="static", **kwargs)

    def do_POST(self) -> None:
        """Routes POST requests."""
        if self.path == '/api/analyze':
            self.handle_analyze()
        else:
            self.send_error(404, "Not Found")

    def handle_analyze(self) -> None:
        """Handles /api/analyze endpoint logic."""
        content_length = int(self.headers.get('Content-Length', 0))
        
        # Security: Strict 5MB payload limit to prevent DoS
        if content_length > 5 * 1024 * 1024:
            self.send_error_json(413, "Payload Too Large")
            return
            
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error_json(400, "Invalid JSON payload")
            return

        text = data.get("text", "")
        language = data.get("language", "English")
        image_base64 = data.get("image_base64")
        mime_type = data.get("mime_type")

        if not GEMINI_API_KEY:
            self.send_error_json(500, "GEMINI_API_KEY is not set on the server")
            return

        # Prepare Gemini REST API request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key={GEMINI_API_KEY}"
        
        system_instruction = f"""
        You are a lightweight campus safety companion. Provide rapid, structured guidance for minor campus emergencies or hazards.
        CRITICAL INSTRUCTIONS:
        - NOT a medical diagnosis tool. Do NOT provide risky detailed treatment instructions for severe situations.
        - If severe, clearly recommend professional help.
        - Translate summary, immediateActions, avoid, warningSigns, and seekProfessionalHelp into {language}.
        
        You MUST output strict JSON in this exact structure:
        {{
            "category": "String (e.g., Minor burn)",
            "urgency": "String (Low, Medium, or High)",
            "summary": "String",
            "immediateActions": ["Step 1", "Step 2"],
            "avoid": ["Do not X"],
            "warningSigns": ["Watch for Y"],
            "seekProfessionalHelp": "String",
            "recommendedContact": "String (e.g., Medical Room, Campus Security)",
            "language": "{language}",
            "uncertainty": "String"
        }}
        """

        parts = []
        if text:
            parts.append({"text": text})
        if image_base64 and mime_type:
            parts.append({
                "inlineData": {
                    "mimeType": mime_type,
                    "data": image_base64
                }
            })

        if not parts:
            self.send_error_json(400, "Must provide either text or image")
            return

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [{
                "parts": parts
            }],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # Extract text from Gemini response
                candidate = result.get('candidates', [])[0]
                content_text = candidate.get('content', {}).get('parts', [])[0].get('text', '{}')
                
                # Send valid JSON back to frontend
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self._send_security_headers()
                self.end_headers()
                self.wfile.write(content_text.encode('utf-8'))

        except urllib.error.HTTPError as e:
            # Security: Do not leak the raw error trace to the frontend
            print(f"Gemini API Error: {e.code}")
            self.send_fallback_mock(text, language)
        except Exception as e:
            # Security: Do not leak the raw error trace to the frontend
            print("Unexpected Network Error occurred.")
            self.send_fallback_mock(text, language)

    def send_fallback_mock(self, text: str, language: str) -> None:
        """Provides mock data for the hackathon demo when internet is down."""
        text_lower = text.lower() if text else ""
        
        # 1. Injured Leg / Fall
        if "leg" in text_lower or "fall" in text_lower or "slip" in text_lower:
            mock = {
                "category": "Minor fall/injury",
                "urgency": "Medium",
                "summary": "You reported an injured leg. It is important to prevent further injury.",
                "immediateActions": ["Do not attempt to bear weight on the injured leg.", "Sit or lie down in a safe area.", "Elevate the leg if possible to reduce swelling."],
                "avoid": ["Do not massage the injured area.", "Do not apply heat immediately.", "Do not try to walk it off."],
                "warningSigns": ["Severe pain", "Deformity of the leg", "Numbness or tingling", "Inability to move the leg"],
                "seekProfessionalHelp": "Seek medical help if you cannot bear weight, or if there is severe pain or obvious deformity.",
                "recommendedContact": "Medical Room",
                "language": language,
                "uncertainty": "Without an X-ray, a fracture cannot be ruled out."
            }
        # 2. Chemical Spill
        elif "spill" in text_lower or "chemical" in text_lower:
            mock = {
                "category": "Chemical spill",
                "urgency": "High",
                "summary": "A chemical spill has occurred. Ensure personal safety first.",
                "immediateActions": ["Evacuate the immediate area of the spill.", "Alert others nearby to stay away.", "If the chemical touched skin, flush with copious amounts of water for 15 minutes."],
                "avoid": ["Do not attempt to clean up the spill yourself without proper training.", "Do not touch the chemical or breathe in the fumes."],
                "warningSigns": ["Dizziness", "Skin irritation or burning", "Difficulty breathing"],
                "seekProfessionalHelp": "If anyone has inhaled fumes or had skin contact, seek emergency medical attention.",
                "recommendedContact": "Campus Security",
                "language": language,
                "uncertainty": "The exact chemical is unknown, treat with extreme caution."
            }
        # 3. Minor Burn
        elif "burn" in text_lower or "fire" in text_lower:
            mock = {
                "category": "Minor burn",
                "urgency": "Low",
                "summary": "You have sustained a minor burn. Cooling the area is the priority.",
                "immediateActions": ["Cool the burn under cool (not cold) running water for 10-15 minutes.", "Remove any tight items like rings from the burned area before it swells.", "Apply a sterile, non-fluffy dressing or cling film."],
                "avoid": ["Do not apply ice, iced water, or greasy substances like butter.", "Do not pop any blisters that form.", "Do not remove clothing that is stuck to the burn."],
                "warningSigns": ["Burn is larger than your hand", "White or charred skin", "Signs of infection later (redness, pus)"],
                "seekProfessionalHelp": "If the burn is large, on the face, hands, or joints, or if it causes severe pain.",
                "recommendedContact": "Medical Room",
                "language": language,
                "uncertainty": "The depth of the burn determines if professional care is needed."
            }
        # 4. Default / General Cut
        else:
            mock = {
                "category": "General Minor Injury / Cut",
                "urgency": "Low",
                "summary": "You reported a general minor injury or cut.",
                "immediateActions": ["Wash your hands before treating the wound.", "Stop any bleeding by applying gentle pressure with a clean cloth.", "Clean the wound with clean water."],
                "avoid": ["Do not use harsh antiseptics like hydrogen peroxide.", "Do not pick at scabs."],
                "warningSigns": ["Pus", "Increased redness", "Swelling", "Fever"],
                "seekProfessionalHelp": "If the cut is deep, gaping, won't stop bleeding after 10 minutes, or you haven't had a tetanus shot in 5 years.",
                "recommendedContact": "Medical Room",
                "language": language,
                "uncertainty": "Ensure the wound is fully cleaned to prevent infection."
            }

        # Send mock response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(json.dumps(mock).encode('utf-8'))

    def send_error_json(self, code: int, message: str) -> None:
        """Sends a JSON formatted error response."""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))

    def _send_security_headers(self) -> None:
        """Helper to append strict security headers to the response."""
        self.send_header('Content-Security-Policy', "default-src 'self'")
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')

if __name__ == "__main__":
    port = 8000
    server = ThreadedHTTPServer(('', port), SafetyHandler)
    print(f"Starting extremely lightweight 0-dependency server on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
