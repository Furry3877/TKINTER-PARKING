"""
Smart Parking System - Database Management Layer (Indian Rupee / INR)
Handles SQLite persistence for slots, tickets, and segregated tariff rules in INR (₹).
"""
import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from models import VehicleType, ParkingSlot, ParkingTicket, PricingRule

DB_FILE = os.path.join(os.path.dirname(__file__), "smart_parking.db")


class DatabaseManager:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Yields an SQLite connection that automatically commits and closes."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_database(self) -> None:
        """Initializes database schema and populates slots if empty."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Slots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS slots (
                    slot_id TEXT PRIMARY KEY,
                    vehicle_type TEXT NOT NULL,
                    is_occupied INTEGER NOT NULL DEFAULT 0,
                    current_vehicle_no TEXT,
                    current_ticket_id TEXT,
                    occupied_since TEXT
                )
            """)

            # 2. Tickets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    vehicle_no TEXT NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    slot_id TEXT NOT NULL,
                    owner_name TEXT,
                    phone TEXT,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT,
                    duration_minutes INTEGER DEFAULT 0,
                    hourly_rate REAL DEFAULT 0.0,
                    total_fee REAL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    FOREIGN KEY (slot_id) REFERENCES slots(slot_id)
                )
            """)

            # 3. Pricing Rules table (Tariffs in INR ₹)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pricing_rules (
                    vehicle_type TEXT PRIMARY KEY,
                    base_fee REAL NOT NULL,
                    hourly_rate REAL NOT NULL,
                    minimum_charge REAL NOT NULL
                )
            """)

        # Seed initial slots & INR pricing
        self._seed_default_data()

    def _seed_default_data(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Seed pricing rules in Indian Rupees (₹)
            cursor.execute("SELECT COUNT(*) FROM pricing_rules")
            if cursor.fetchone()[0] == 0:
                inr_pricing = [
                    # Type, Base Fee (1st hr), Subsequent Hourly Rate, Min Charge
                    (VehicleType.CAR.value, 40.0, 20.0, 40.0),      # Cars: ₹40 base + ₹20/hr
                    (VehicleType.BIKE.value, 20.0, 10.0, 20.0),     # Two-Wheelers: ₹20 base + ₹10/hr
                    (VehicleType.BICYCLE.value, 10.0, 5.0, 10.0),   # Bicycles: ₹10 base + ₹5/hr
                ]
                cursor.executemany(
                    "INSERT INTO pricing_rules (vehicle_type, base_fee, hourly_rate, minimum_charge) VALUES (?, ?, ?, ?)",
                    inr_pricing
                )

            # Seed parking slots segregated by vehicle type
            cursor.execute("SELECT COUNT(*) FROM slots")
            if cursor.fetchone()[0] == 0:
                slots = []
                # Cars: 12 slots (C-01 to C-12)
                for i in range(1, 13):
                    slots.append((f"C-{i:02d}", VehicleType.CAR.value, 0, None, None, None))
                
                # Bikes: 16 slots (M-01 to M-16)
                for i in range(1, 17):
                    slots.append((f"M-{i:02d}", VehicleType.BIKE.value, 0, None, None, None))
                
                # Bicycles: 20 slots (B-01 to B-20)
                for i in range(1, 21):
                    slots.append((f"B-{i:02d}", VehicleType.BICYCLE.value, 0, None, None, None))

                cursor.executemany(
                    """INSERT INTO slots 
                       (slot_id, vehicle_type, is_occupied, current_vehicle_no, current_ticket_id, occupied_since) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    slots
                )

    def get_pricing_rule(self, vehicle_type: VehicleType) -> PricingRule:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pricing_rules WHERE vehicle_type = ?", (vehicle_type.value,))
            row = cursor.fetchone()
            if row:
                return PricingRule(
                    vehicle_type=VehicleType(row["vehicle_type"]),
                    base_fee=float(row["base_fee"]),
                    hourly_rate=float(row["hourly_rate"]),
                    minimum_charge=float(row["minimum_charge"])
                )
            return PricingRule(vehicle_type, 40.0, 20.0, 40.0)

    def get_all_slots(self, vehicle_type: Optional[VehicleType] = None) -> List[ParkingSlot]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if vehicle_type:
                cursor.execute("SELECT * FROM slots WHERE vehicle_type = ? ORDER BY slot_id", (vehicle_type.value,))
            else:
                cursor.execute("SELECT * FROM slots ORDER BY slot_id")
            
            rows = cursor.fetchall()
            slots = []
            for r in rows:
                occupied_since = datetime.fromisoformat(r["occupied_since"]) if r["occupied_since"] else None
                slots.append(ParkingSlot(
                    slot_id=r["slot_id"],
                    vehicle_type=VehicleType(r["vehicle_type"]),
                    is_occupied=bool(r["is_occupied"]),
                    current_vehicle_no=r["current_vehicle_no"],
                    current_ticket_id=r["current_ticket_id"],
                    occupied_since=occupied_since
                ))
            return slots

    def get_slot_by_id(self, slot_id: str) -> Optional[ParkingSlot]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM slots WHERE slot_id = ?", (slot_id,))
            r = cursor.fetchone()
            if not r:
                return None
            occupied_since = datetime.fromisoformat(r["occupied_since"]) if r["occupied_since"] else None
            return ParkingSlot(
                slot_id=r["slot_id"],
                vehicle_type=VehicleType(r["vehicle_type"]),
                is_occupied=bool(r["is_occupied"]),
                current_vehicle_no=r["current_vehicle_no"],
                current_ticket_id=r["current_ticket_id"],
                occupied_since=occupied_since
            )

    def get_active_ticket_by_vehicle(self, vehicle_no: str) -> Optional[ParkingTicket]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tickets WHERE vehicle_no = ? AND status = 'ACTIVE' LIMIT 1", (vehicle_no.upper().strip(),))
            r = cursor.fetchone()
            if not r:
                return None
            return self._row_to_ticket(r)

    def get_active_ticket_by_slot(self, slot_id: str) -> Optional[ParkingTicket]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tickets WHERE slot_id = ? AND status = 'ACTIVE' LIMIT 1", (slot_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return self._row_to_ticket(r)

    def get_ticket_by_id(self, ticket_id: str) -> Optional[ParkingTicket]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tickets WHERE ticket_id = ? LIMIT 1", (ticket_id.strip(),))
            r = cursor.fetchone()
            if not r:
                return None
            return self._row_to_ticket(r)

    def _row_to_ticket(self, r: sqlite3.Row) -> ParkingTicket:
        entry_time = datetime.fromisoformat(r["entry_time"])
        exit_time = datetime.fromisoformat(r["exit_time"]) if r["exit_time"] else None
        return ParkingTicket(
            ticket_id=r["ticket_id"],
            vehicle_no=r["vehicle_no"],
            vehicle_type=VehicleType(r["vehicle_type"]),
            slot_id=r["slot_id"],
            owner_name=r["owner_name"] or "",
            phone=r["phone"] or "",
            entry_time=entry_time,
            exit_time=exit_time,
            duration_minutes=r["duration_minutes"] or 0,
            hourly_rate=r["hourly_rate"] or 0.0,
            total_fee=r["total_fee"] or 0.0,
            status=r["status"]
        )

    def create_ticket_and_occupy_slot(self, ticket: ParkingTicket) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tickets (ticket_id, vehicle_no, vehicle_type, slot_id, owner_name, phone, entry_time, hourly_rate, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
            """, (
                ticket.ticket_id,
                ticket.vehicle_no.upper().strip(),
                ticket.vehicle_type.value,
                ticket.slot_id,
                ticket.owner_name.strip(),
                ticket.phone.strip(),
                ticket.entry_time.isoformat(),
                ticket.hourly_rate
            ))

            cursor.execute("""
                UPDATE slots
                SET is_occupied = 1,
                    current_vehicle_no = ?,
                    current_ticket_id = ?,
                    occupied_since = ?
                WHERE slot_id = ?
            """, (
                ticket.vehicle_no.upper().strip(),
                ticket.ticket_id,
                ticket.entry_time.isoformat(),
                ticket.slot_id
            ))
            return True

    def complete_ticket_and_free_slot(self, ticket_id: str, exit_time: datetime, duration_minutes: int, total_fee: float) -> Tuple[bool, Optional[str]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT slot_id, vehicle_no FROM tickets WHERE ticket_id = ?", (ticket_id,))
            row = cursor.fetchone()
            if not row:
                return False, None
            
            slot_id = row["slot_id"]

            cursor.execute("""
                UPDATE tickets
                SET exit_time = ?,
                    duration_minutes = ?,
                    total_fee = ?,
                    status = 'COMPLETED'
                WHERE ticket_id = ?
            """, (exit_time.isoformat(), duration_minutes, total_fee, ticket_id))

            cursor.execute("""
                UPDATE slots
                SET is_occupied = 0,
                    current_vehicle_no = NULL,
                    current_ticket_id = NULL,
                    occupied_since = NULL
                WHERE slot_id = ?
            """, (slot_id,))
            return True, slot_id

    def fetch_tickets(self, vehicle_type_filter: str = "ALL", status_filter: str = "ALL", search_query: str = "") -> List[ParkingTicket]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM tickets WHERE 1=1"
            params = []

            if vehicle_type_filter != "ALL":
                query += " AND vehicle_type = ?"
                params.append(vehicle_type_filter)

            if status_filter != "ALL":
                query += " AND status = ?"
                params.append(status_filter)

            if search_query:
                clean_query = f"%{search_query.strip()}%"
                query += " AND (vehicle_no LIKE ? OR ticket_id LIKE ? OR slot_id LIKE ? OR owner_name LIKE ?)"
                params.extend([clean_query, clean_query, clean_query, clean_query])

            query += " ORDER BY entry_time DESC"
            cursor.execute(query, params)
            return [self._row_to_ticket(r) for r in cursor.fetchall()]

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Calculates segregated occupancy stats and total revenue in INR (₹)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {
                "Car": {"total": 0, "occupied": 0, "available": 0},
                "Bike": {"total": 0, "occupied": 0, "available": 0},
                "Bicycle": {"total": 0, "occupied": 0, "available": 0},
                "total_slots": 0,
                "total_occupied": 0,
                "total_available": 0,
                "total_revenue": 0.0,
                "active_count": 0,
                "completed_count": 0
            }

            cursor.execute("SELECT vehicle_type, is_occupied, COUNT(*) as cnt FROM slots GROUP BY vehicle_type, is_occupied")
            for r in cursor.fetchall():
                v_type = r["vehicle_type"]
                is_occ = bool(r["is_occupied"])
                count = r["cnt"]
                if v_type in stats:
                    stats[v_type]["total"] += count
                    if is_occ:
                        stats[v_type]["occupied"] += count
                        stats["total_occupied"] += count
                    else:
                        stats[v_type]["available"] += count
                        stats["total_available"] += count
                    stats["total_slots"] += count

            cursor.execute("SELECT SUM(total_fee) FROM tickets WHERE status = 'COMPLETED'")
            rev = cursor.fetchone()[0]
            stats["total_revenue"] = float(rev or 0.0)

            cursor.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status")
            for r in cursor.fetchall():
                if r[0] == "ACTIVE":
                    stats["active_count"] = r[1]
                elif r[0] == "COMPLETED":
                    stats["completed_count"] = r[1]

            return stats

    def reset_and_seed_demo_data(self) -> None:
        """Clears existing data and populates realistic Indian demo vehicles for testing."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tickets")
            cursor.execute("""
                UPDATE slots
                SET is_occupied = 0,
                    current_vehicle_no = NULL,
                    current_ticket_id = NULL,
                    occupied_since = NULL
            """)

        now = datetime.now()

        # Authentic Indian registration numbers across states (DL, MH, KA, HR, UP, TN)
        demo_data = [
            ("DL-01-AB-1234", VehicleType.CAR, "C-01", "Aarav Sharma", "+91 98112 23344", now - timedelta(hours=2, minutes=30)),
            ("MH-12-DE-9981", VehicleType.CAR, "C-04", "Ananya Verma", "+91 98223 34455", now - timedelta(hours=1, minutes=15)),
            ("KA-05-MJ-2024", VehicleType.CAR, "C-08", "Rajesh Patel", "+91 98334 45566", now - timedelta(minutes=45)),
            ("DL-3C-TY-7890", VehicleType.BIKE, "M-02", "Vikram Singh", "+91 98445 56677", now - timedelta(hours=3, minutes=10)),
            ("HR-26-EX-3344", VehicleType.BIKE, "M-07", "Sneha Rao", "+91 98556 67788", now - timedelta(hours=1, minutes=40)),
            ("BYC-HERO-001", VehicleType.BICYCLE, "B-03", "Rohan Joshi", "+91 98667 78899", now - timedelta(hours=4, minutes=0)),
            ("BYC-ATLAS-88", VehicleType.BICYCLE, "B-11", "Pooja Nair", "+91 98778 89900", now - timedelta(minutes=30)),
        ]

        ticket_counter = 1001
        for veh_no, vtype, slot_id, name, phone, entry in demo_data:
            rule = self.get_pricing_rule(vtype)
            ticket = ParkingTicket(
                ticket_id=f"TK-{ticket_counter}",
                vehicle_no=veh_no,
                vehicle_type=vtype,
                slot_id=slot_id,
                owner_name=name,
                phone=phone,
                entry_time=entry,
                hourly_rate=rule.hourly_rate
            )
            self.create_ticket_and_occupy_slot(ticket)
            ticket_counter += 1
