"""
Smart Parking System - Data Models (Indian Rupee / INR Edition)
Defines vehicle types, slot representations, and parking tickets.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class VehicleType(str, Enum):
    CAR = "Car"
    BIKE = "Bike"
    BICYCLE = "Bicycle"

    @property
    def prefix(self) -> str:
        if self == VehicleType.CAR:
            return "C"
        elif self == VehicleType.BIKE:
            return "M"
        elif self == VehicleType.BICYCLE:
            return "B"
        return "S"

    @property
    def icon(self) -> str:
        if self == VehicleType.CAR:
            return "🚗"
        elif self == VehicleType.BIKE:
            return "🏍️"
        elif self == VehicleType.BICYCLE:
            return "🚲"
        return "🅿️"

    @property
    def zone_name(self) -> str:
        if self == VehicleType.CAR:
            return "Zone C (Cars & SUVs)"
        elif self == VehicleType.BIKE:
            return "Zone M (Two-Wheelers & Bikes)"
        elif self == VehicleType.BICYCLE:
            return "Zone B (Bicycles)"
        return "General Zone"

    @property
    def color(self) -> str:
        if self == VehicleType.CAR:
            return "#2563EB"   # Royal Blue
        elif self == VehicleType.BIKE:
            return "#D97706"   # Amber/Orange
        elif self == VehicleType.BICYCLE:
            return "#059669"   # Emerald Green
        return "#475569"


@dataclass
class PricingRule:
    vehicle_type: VehicleType
    base_fee: float        # First hour charge in INR (₹)
    hourly_rate: float     # Subsequent hours charge in INR (₹)
    minimum_charge: float  # Minimum billable charge in INR (₹)


@dataclass
class ParkingSlot:
    slot_id: str
    vehicle_type: VehicleType
    is_occupied: bool = False
    current_vehicle_no: Optional[str] = None
    current_ticket_id: Optional[str] = None
    occupied_since: Optional[datetime] = None


@dataclass
class ParkingTicket:
    ticket_id: str
    vehicle_no: str
    vehicle_type: VehicleType
    slot_id: str
    entry_time: datetime
    owner_name: str = ""
    phone: str = ""
    exit_time: Optional[datetime] = None
    duration_minutes: int = 0
    hourly_rate: float = 0.0
    total_fee: float = 0.0
    status: str = "ACTIVE"  # "ACTIVE" or "COMPLETED"
