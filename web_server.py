"""
Smart Parking Management System - Web Server & REST API (Indian Rupee / INR Edition)
Built using Python standard library (http.server, urllib, json).
Requires ZERO external pip packages!
"""
import os
import json
import mimetypes
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from models import VehicleType, ParkingTicket
from database import DatabaseManager
from parking_system import ParkingSystemController

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "web")

# Ensure static directory exists
os.makedirs(STATIC_DIR, exist_ok=True)

# Shared controller instance
db_manager = DatabaseManager()
controller = ParkingSystemController(db_manager)


class ParkingWebHandler(BaseHTTPRequestHandler):
    server_version = "SmartParkingServer-INR/2.0"

    def send_json(self, data: dict, status: int = 200):
        response_bytes = json.dumps(data, default=str, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # -------------------------------------------------------------
        # REST API Endpoints
        # -------------------------------------------------------------
        if path == "/api/stats":
            stats = controller.db.get_summary_statistics()
            self.send_json({"success": True, "currency": "₹", "stats": stats})
            return

        elif path == "/api/slots":
            v_type_str = query.get("type", [None])[0]
            vtype = None
            if v_type_str and v_type_str in [v.value for v in VehicleType]:
                vtype = VehicleType(v_type_str)
            
            slots = controller.db.get_all_slots(vtype)
            result = []
            for s in slots:
                occupied_since_str = s.occupied_since.strftime("%I:%M %p") if s.occupied_since else None
                elapsed_str = ""
                if s.is_occupied and s.occupied_since:
                    delta = datetime.now() - s.occupied_since
                    mins = int(delta.total_seconds() // 60)
                    elapsed_str = f"{mins // 60}h {mins % 60}m"

                result.append({
                    "slot_id": s.slot_id,
                    "vehicle_type": s.vehicle_type.value,
                    "zone_name": s.vehicle_type.zone_name,
                    "icon": s.vehicle_type.icon,
                    "color": s.vehicle_type.color,
                    "is_occupied": s.is_occupied,
                    "current_vehicle_no": s.current_vehicle_no,
                    "current_ticket_id": s.current_ticket_id,
                    "occupied_since": occupied_since_str,
                    "elapsed_str": elapsed_str
                })
            self.send_json({"success": True, "slots": result})
            return

        elif path == "/api/tickets":
            vtype = query.get("type", ["ALL"])[0]
            status = query.get("status", ["ALL"])[0]
            search = query.get("search", [""])[0]

            tickets = controller.db.fetch_tickets(
                vehicle_type_filter=vtype,
                status_filter=status,
                search_query=search
            )

            result = []
            for t in tickets:
                result.append({
                    "ticket_id": t.ticket_id,
                    "vehicle_no": t.vehicle_no,
                    "vehicle_type": t.vehicle_type.value,
                    "icon": t.vehicle_type.icon,
                    "slot_id": t.slot_id,
                    "owner_name": t.owner_name or "--",
                    "phone": t.phone or "--",
                    "entry_time": t.entry_time.strftime("%d-%b %I:%M %p"),
                    "exit_time": t.exit_time.strftime("%d-%b %I:%M %p") if t.exit_time else "--",
                    "duration_str": f"{t.duration_minutes // 60}h {t.duration_minutes % 60}m" if t.status == "COMPLETED" else "Parked",
                    "total_fee": round(t.total_fee, 2),
                    "currency": "₹",
                    "status": t.status
                })
            self.send_json({"success": True, "tickets": result})
            return

        elif path == "/api/preview_checkout":
            ident = query.get("id", [""])[0]
            ticket = controller.db.get_active_ticket_by_vehicle(ident)
            if not ticket:
                ticket = controller.db.get_ticket_by_id(ident)
            if not ticket:
                ticket = controller.db.get_active_ticket_by_slot(ident)

            if not ticket or ticket.status != "ACTIVE":
                self.send_json({"success": False, "message": f"No active vehicle found for '{ident}'"}, 404)
                return

            bill = controller.calculate_bill(ticket)
            self.send_json({
                "success": True,
                "currency": "₹",
                "bill": {
                    "ticket_id": bill["ticket_id"],
                    "vehicle_no": bill["vehicle_no"],
                    "vehicle_type": bill["vehicle_type"],
                    "slot_id": bill["slot_id"],
                    "entry_time": bill["entry_time"].strftime("%d-%b-%Y %I:%M %p"),
                    "exit_time": bill["exit_time"].strftime("%d-%b-%Y %I:%M %p"),
                    "duration_str": bill["duration_str"],
                    "base_fee": bill["base_fee"],
                    "hourly_rate": bill["hourly_rate"],
                    "billable_hours": bill["billable_hours"],
                    "total_fee": bill["total_fee"]
                }
            })
            return

        elif path == "/api/export_csv":
            export_path = os.path.join(STATIC_DIR, "parking_logs_inr.csv")
            success, msg = controller.export_tickets_to_csv(export_path)
            if success and os.path.exists(export_path):
                with open(export_path, "rb") as f:
                    csv_data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", "attachment; filename=parking_logs_inr.csv")
                self.send_header("Content-Length", str(len(csv_data)))
                self.end_headers()
                self.wfile.write(csv_data)
                return
            else:
                self.send_json({"success": False, "message": msg}, 500)
                return

        # -------------------------------------------------------------
        # Static Asset Delivery (HTML, CSS, JS)
        # -------------------------------------------------------------
        if path == "/" or path == "":
            path = "/index.html"

        safe_path = os.path.normpath(os.path.join(STATIC_DIR, path.lstrip("/")))
        if not safe_path.startswith(STATIC_DIR) or not os.path.isfile(safe_path):
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>404 Not Found</h1>")
            return

        mime_type, _ = mimetypes.guess_type(safe_path)
        mime_type = mime_type or "application/octet-stream"
        if "text" in mime_type or "javascript" in mime_type or "json" in mime_type:
            mime_type += "; charset=utf-8"

        with open(safe_path, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        if safe_path.endswith("service-worker.js"):
            self.send_header("Service-Worker-Allowed", "/")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}

        # -------------------------------------------------------------
        # Check-In: /api/park
        # -------------------------------------------------------------
        if path == "/api/park":
            veh_no = payload.get("vehicle_no", "").strip().upper()
            v_type_str = payload.get("vehicle_type", "Car")
            slot_id = payload.get("slot_id") or None
            owner_name = payload.get("owner_name", "").strip()
            phone = payload.get("phone", "").strip()
            sim_hours = int(payload.get("sim_hours", 0))

            try:
                vtype = VehicleType(v_type_str)
            except ValueError:
                self.send_json({"success": False, "message": f"Invalid vehicle type '{v_type_str}'"}, 400)
                return

            entry_time = datetime.now() - timedelta(hours=sim_hours) if sim_hours > 0 else datetime.now()

            success, msg, ticket = controller.park_vehicle(
                vehicle_no=veh_no,
                vehicle_type=vtype,
                slot_id=slot_id,
                owner_name=owner_name,
                phone=phone,
                simulated_entry_time=entry_time
            )

            if success and ticket:
                ticket_slip = controller.generate_ticket_text(ticket)
                self.send_json({
                    "success": True,
                    "message": msg,
                    "currency": "₹",
                    "ticket": {
                        "ticket_id": ticket.ticket_id,
                        "vehicle_no": ticket.vehicle_no,
                        "vehicle_type": ticket.vehicle_type.value,
                        "slot_id": ticket.slot_id,
                        "entry_time": ticket.entry_time.strftime("%d-%b-%Y %I:%M %p"),
                        "slip_text": ticket_slip
                    }
                })
            else:
                self.send_json({"success": False, "message": msg}, 400)
            return

        # -------------------------------------------------------------
        # Check-Out: /api/checkout
        # -------------------------------------------------------------
        elif path == "/api/checkout":
            identifier = payload.get("identifier", "").strip().upper()
            success, msg, bill = controller.checkout_vehicle(identifier)

            if success and bill:
                receipt_text = controller.generate_receipt_text(bill)
                self.send_json({
                    "success": True,
                    "message": msg,
                    "currency": "₹",
                    "bill": {
                        "ticket_id": bill["ticket_id"],
                        "vehicle_no": bill["vehicle_no"],
                        "vehicle_type": bill["vehicle_type"],
                        "slot_id": bill["slot_id"],
                        "duration_str": bill["duration_str"],
                        "total_fee": bill["total_fee"],
                        "receipt_text": receipt_text
                    }
                })
            else:
                self.send_json({"success": False, "message": msg}, 400)
            return

        # -------------------------------------------------------------
        # Load Demo Data: /api/demo
        # -------------------------------------------------------------
        elif path == "/api/demo":
            controller.db.reset_and_seed_demo_data()
            self.send_json({"success": True, "message": "7 sample Indian demo vehicles successfully loaded!"})
            return

        self.send_json({"success": False, "message": "Not found"}, 404)


def run_web_server(port: int = 5000):
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, ParkingWebHandler)
    print("=" * 60)
    print(f">> Smart Parking Web Application (INR Edition) is RUNNING at:")
    print(f"   Local URL:    http://localhost:{port}")
    print(f"   Network URL:  http://127.0.0.1:{port}")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    run_web_server(port)
