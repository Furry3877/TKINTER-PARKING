"""
Automated Unit & Integration Tests for Smart Parking System (INR Edition)
Verifies vehicle segregation, slot allocation, tariff calculation (₹), and data persistence.
"""
import unittest
import os
import tempfile
from datetime import datetime, timedelta

from models import VehicleType, ParkingSlot, ParkingTicket
from database import DatabaseManager
from parking_system import ParkingSystemController


class TestSmartParkingSystemINR(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_db_path = os.path.join(self.temp_dir.name, "test_parking_inr.db")
        self.db = DatabaseManager(self.temp_db_path)
        self.ctrl = ParkingSystemController(self.db)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_slot_initialization_and_segregation(self):
        """Verifies slots are partitioned correctly across vehicle types."""
        car_slots = self.db.get_all_slots(VehicleType.CAR)
        bike_slots = self.db.get_all_slots(VehicleType.BIKE)
        bicycle_slots = self.db.get_all_slots(VehicleType.BICYCLE)

        self.assertEqual(len(car_slots), 12, "Should initialize 12 Car bays (C-01 to C-12)")
        self.assertEqual(len(bike_slots), 16, "Should initialize 16 Bike bays (M-01 to M-16)")
        self.assertEqual(len(bicycle_slots), 20, "Should initialize 20 Bicycle racks (B-01 to B-20)")

        self.assertTrue(all(s.slot_id.startswith("C-") for s in car_slots))
        self.assertTrue(all(s.slot_id.startswith("M-") for s in bike_slots))
        self.assertTrue(all(s.slot_id.startswith("B-") for s in bicycle_slots))

    def test_park_vehicle_auto_allocation(self):
        """Tests automatic allocation into the correct vehicle zone."""
        success, msg, ticket = self.ctrl.park_vehicle("DL-01-AB-1234", VehicleType.CAR)
        self.assertTrue(success, f"Failed to park car: {msg}")
        self.assertEqual(ticket.slot_id, "C-01", "First car should be placed in C-01")
        self.assertEqual(ticket.vehicle_type, VehicleType.CAR)

        success2, msg2, ticket2 = self.ctrl.park_vehicle("MH-12-DE-5678", VehicleType.CAR)
        self.assertTrue(success2)
        self.assertEqual(ticket2.slot_id, "C-02")

        success3, msg3, ticket3 = self.ctrl.park_vehicle("KA-05-BK-9999", VehicleType.BIKE)
        self.assertTrue(success3)
        self.assertEqual(ticket3.slot_id, "M-01")

        success4, msg4, ticket4 = self.ctrl.park_vehicle("CYC-HERO-01", VehicleType.BICYCLE)
        self.assertTrue(success4)
        self.assertEqual(ticket4.slot_id, "B-01")

    def test_prevent_segregation_mismatch(self):
        """Enforces that a vehicle cannot park in an incompatible zone."""
        success, msg, ticket = self.ctrl.park_vehicle("DL-01-AB-1234", VehicleType.CAR, slot_id="M-01")
        self.assertFalse(success)
        self.assertIn("Slot mismatch", msg)

        success2, msg2, ticket2 = self.ctrl.park_vehicle("MH-12-BK-1111", VehicleType.BIKE, slot_id="B-01")
        self.assertFalse(success2)
        self.assertIn("Slot mismatch", msg2)

    def test_prevent_duplicate_entry(self):
        """Ensures the same vehicle cannot check in twice while already parked."""
        self.ctrl.park_vehicle("DL-01-AB-1234", VehicleType.CAR)
        success, msg, ticket = self.ctrl.park_vehicle("DL-01-AB-1234", VehicleType.CAR)
        self.assertFalse(success)
        self.assertIn("already parked", msg)

    def test_car_tariff_in_rupees(self):
        """Tests duration and segregated fee calculation in INR: Base ₹40 + ₹20/hr."""
        entry_time = datetime.now() - timedelta(hours=2, minutes=30)
        success, msg, ticket = self.ctrl.park_vehicle(
            vehicle_no="HR-26-AB-1234",
            vehicle_type=VehicleType.CAR,
            simulated_entry_time=entry_time
        )
        self.assertTrue(success)

        success, msg, bill = self.ctrl.checkout_vehicle("HR-26-AB-1234")
        self.assertTrue(success)
        self.assertIsNotNone(bill)
        self.assertEqual(bill["vehicle_no"], "HR-26-AB-1234")
        self.assertEqual(bill["slot_id"], "C-01")
        # 2h 30m = 1st hr (₹40) + 2 extra hrs at ₹20/hr = ₹80.00
        self.assertEqual(bill["total_fee"], 80.0)

        slot = self.db.get_slot_by_id("C-01")
        self.assertFalse(slot.is_occupied)

    def test_bicycle_tariff_in_rupees(self):
        """Tests bicycle pricing in INR: Base ₹10 + ₹5/hr."""
        entry_time = datetime.now() - timedelta(hours=1, minutes=45)
        success, msg, ticket = self.ctrl.park_vehicle(
            vehicle_no="CYCLE-ATLAS-9",
            vehicle_type=VehicleType.BICYCLE,
            simulated_entry_time=entry_time
        )
        self.assertTrue(success)

        success, msg, bill = self.ctrl.checkout_vehicle("CYCLE-ATLAS-9")
        self.assertTrue(success)
        # 1h 45m = 1st hr (₹10) + 1 extra hr at ₹5/hr = ₹15.00
        self.assertEqual(bill["total_fee"], 15.0)

    def test_csv_export_in_rupees(self):
        """Tests exporting logs to CSV with INR currency formatting."""
        self.ctrl.park_vehicle("UP-16-AB-1234", VehicleType.CAR)
        csv_path = os.path.join(tempfile.gettempdir(), "test_parking_inr_export.csv")
        success, msg = self.ctrl.export_tickets_to_csv(csv_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(csv_path))
        if os.path.exists(csv_path):
            os.remove(csv_path)


if __name__ == "__main__":
    unittest.main()
