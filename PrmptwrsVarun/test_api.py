import unittest
import json
import os
from unittest.mock import patch, MagicMock
from io import BytesIO

# Import the Vercel handler
from api.index import handler

class MockRequest:
    def makefile(self, *args, **kwargs):
        return BytesIO(b"")

class TestSafetyAPI(unittest.TestCase):
    
    def setUp(self):
        # Setup a mock handler instance
        self.mock_req = MockRequest()
        self.mock_client_address = ('127.0.0.1', 8080)
        self.mock_server = MagicMock()
        
    def test_missing_payload(self):
        """Test that sending an empty payload returns a 400 JSON decode error."""
        class TestHandler(handler):
            def __init__(self, *args, **kwargs):
                self.rfile = BytesIO(b"")
                self.headers = {'Content-Length': '0'}
                self.wfile = BytesIO()
                
            def send_response(self, code, message=None):
                self.response_code = code
                
            def send_header(self, *args): pass
            def end_headers(self): pass

        h = TestHandler()
        h.do_POST()
        
        self.assertEqual(h.response_code, 400)
        response_data = json.loads(h.wfile.getvalue().decode())
        self.assertEqual(response_data["error"], "Invalid JSON payload")

    def test_payload_too_large(self):
        """Test that the 5MB strict payload limit is enforced."""
        class TestHandler(handler):
            def __init__(self, *args, **kwargs):
                self.rfile = BytesIO(b"a" * 6000000)
                self.headers = {'Content-Length': '6000000'} # > 5MB
                self.wfile = BytesIO()
                
            def send_response(self, code, message=None):
                self.response_code = code
                
            def send_header(self, *args): pass
            def end_headers(self): pass

        h = TestHandler()
        h.do_POST()
        
        self.assertEqual(h.response_code, 413)
        response_data = json.loads(h.wfile.getvalue().decode())
        self.assertEqual(response_data["error"], "Payload Too Large")

    @patch('api.index.urllib.request.urlopen')
    def test_successful_gemini_parsing(self, mock_urlopen):
        """Test successful interaction with mocked Gemini API."""
        # Mock Gemini Response
        mock_gemini_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": '{"category": "Test", "urgency": "Low"}'}]
                    }
                }
            ]
        }
        
        cm = MagicMock()
        cm.read.return_value = json.dumps(mock_gemini_response).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = cm

        class TestHandler(handler):
            def __init__(self, *args, **kwargs):
                valid_payload = json.dumps({"text": "cut on finger"}).encode()
                self.rfile = BytesIO(valid_payload)
                self.headers = {'Content-Length': str(len(valid_payload))}
                self.wfile = BytesIO()
                
            def send_response(self, code, message=None):
                self.response_code = code
                
            def send_header(self, *args): pass
            def end_headers(self): pass
            
        h = TestHandler()
        # Set dummy API key to bypass key check
        with patch('api.index.GEMINI_API_KEY', 'dummy_key'):
            h.do_POST()
            
        self.assertEqual(h.response_code, 200)
        response_data = json.loads(h.wfile.getvalue().decode())
        self.assertEqual(response_data["category"], "Test")
        self.assertEqual(response_data["urgency"], "Low")

    def test_security_headers_present(self):
        """Test that strict security headers are injected into the response."""
        class TestHandler(handler):
            def __init__(self, *args, **kwargs):
                self.headers_sent = {}
            def send_header(self, keyword, value):
                self.headers_sent[keyword] = value

        h = TestHandler()
        h._send_security_headers()
        
        self.assertEqual(h.headers_sent['Content-Security-Policy'], "default-src 'self'")
        self.assertEqual(h.headers_sent['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(h.headers_sent['X-Frame-Options'], 'DENY')
        self.assertEqual(h.headers_sent['Strict-Transport-Security'], 'max-age=31536000; includeSubDomains')

if __name__ == '__main__':
    unittest.main()
