"""
Smart Parking Management System (India / INR Edition)
Entry point for desktop application.
"""
from database import DatabaseManager
from parking_system import ParkingSystemController
from gui import SmartParkingApp


def main():
    print("=" * 60)
    print(">> Starting Smart Parking Management System (INR Edition)...")
    print("=" * 60)

    db = DatabaseManager()
    controller = ParkingSystemController(db)

    app = SmartParkingApp(controller)
    app.mainloop()


if __name__ == "__main__":
    main()
