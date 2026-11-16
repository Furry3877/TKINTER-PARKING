"""
Unit tests for the Web Server & REST API endpoints (INR ₹ Edition)
"""
import unittest
import io
import json
import random
from web_server import ParkingWebHandler


class MockServer:
    pass


class DummyHandler(ParkingWebHandler):
    def __init__(self, request_bytes: bytes):
        self.rfile = io.BytesIO(request_bytes)
        self.wfile = io.BytesIO()
        self.server = MockServer()
        self.client_address = ('127.0.0.1', 12345)
        line = self.rfile.readline().decode('utf-8')
        self.requestline = line.strip()
        words = line.split()
        self.command = words[0]
        self.path = words[1]
        self.request_version = words[2]
        self.headers = {}
        while True:
            hline = self.rfile.readline().decode('utf-8').strip()
            if not hline:
                break
            k, v = hline.split(':', 1)
            self.headers[k.strip()] = v.strip()


class TestWebServerINR(unittest.TestCase):
    def test_get_index_html(self):
        h = DummyHandler(b'GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n')
        h.do_GET()
        resp = h.wfile.getvalue().decode('utf-8')
        self.assertIn("200 OK", resp)
        self.assertIn("SMART PARKING SYSTEM", resp)
        self.assertIn("INR", resp)

    def test_get_offline_assets(self):
        # 1. Manifest
        h1 = DummyHandler(b'GET /manifest.json HTTP/1.1\r\nHost: localhost\r\n\r\n')
        h1.do_GET()
        resp1 = h1.wfile.getvalue().decode('utf-8')
        self.assertIn("200 OK", resp1)
        self.assertIn("SmartParking", resp1)

        # 2. Service Worker
        h2 = DummyHandler(b'GET /service-worker.js HTTP/1.1\r\nHost: localhost\r\n\r\n')
        h2.do_GET()
        resp2 = h2.wfile.getvalue().decode('utf-8')
        self.assertIn("200 OK", resp2)
        self.assertIn("CACHE_NAME", resp2)

        # 3. SVG Icon
        h3 = DummyHandler(b'GET /icon.svg HTTP/1.1\r\nHost: localhost\r\n\r\n')
        h3.do_GET()
        resp3 = h3.wfile.getvalue().decode('utf-8')
        self.assertIn("200 OK", resp3)
        self.assertIn("<svg", resp3)

    def test_get_api_stats(self):
        h = DummyHandler(b'GET /api/stats HTTP/1.1\r\nHost: localhost\r\n\r\n')
        h.do_GET()
        resp = h.wfile.getvalue().decode('utf-8')
        self.assertIn("200 OK", resp)
        self.assertIn('"success": true', resp)
        self.assertIn('"currency": "\u20b9"', resp)

    def test_get_api_slots(self):
        h = DummyHandler(b'GET /api/slots HTTP/1.1\r\nHost: localhost\r\n\r\n')
        h.do_GET()
        resp = h.wfile.getvalue().decode('utf-8')
        self.assertIn("200 OK", resp)
        self.assertIn('"slot_id": "C-01"', resp)
        self.assertIn('"slot_id": "M-01"', resp)
        self.assertIn('"slot_id": "B-01"', resp)

    def test_park_and_checkout_flow_inr(self):
        test_plate = f"DL-01-INR-{random.randint(1000, 9999)}"
        # 1. Park car via POST /api/park
        body = json.dumps({
            "vehicle_no": test_plate,
            "vehicle_type": "Car",
            "owner_name": "Rohan Gupta",
            "phone": "+91 98111 22233"
        }).encode('utf-8')

        req = (
            b'POST /api/park HTTP/1.1\r\n'
            b'Host: localhost\r\n'
            b'Content-Length: ' + str(len(body)).encode('utf-8') + b'\r\n\r\n' + body
        )
        h = DummyHandler(req)
        h.do_POST()
        resp = h.wfile.getvalue().decode('utf-8')
        self.assertIn("200 OK", resp)
        self.assertIn('"success": true', resp)
        self.assertIn(test_plate, resp)

        # 2. Preview Checkout via GET /api/preview_checkout
        h_prev = DummyHandler(f'GET /api/preview_checkout?id={test_plate} HTTP/1.1\r\nHost: localhost\r\n\r\n'.encode('utf-8'))
        h_prev.do_GET()
        resp_prev = h_prev.wfile.getvalue().decode('utf-8')
        self.assertIn("200 OK", resp_prev)
        self.assertIn('"currency": "\u20b9"', resp_prev)

        # 3. Complete Checkout via POST /api/checkout
        body_co = json.dumps({"identifier": test_plate}).encode('utf-8')
        req_co = (
            b'POST /api/checkout HTTP/1.1\r\n'
            b'Host: localhost\r\n'
            b'Content-Length: ' + str(len(body_co)).encode('utf-8') + b'\r\n\r\n' + body_co
        )
        h_co = DummyHandler(req_co)
        h_co.do_POST()
        resp_co = h_co.wfile.getvalue().decode('utf-8')
        self.assertIn("200 OK", resp_co)
        self.assertIn('"success": true', resp_co)
        self.assertIn("checked out successfully", resp_co)


if __name__ == '__main__':
    unittest.main()
