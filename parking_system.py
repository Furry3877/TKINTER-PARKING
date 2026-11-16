"""
Smart Parking System - Business Logic & Controller Layer (Indian Rupee / INR)
Manages vehicle segregation, slot allocation, fee calculation, and receipt generation in INR (₹).
"""
import math
import csv
import random
from datetime import datetime
from typing import Tuple, Optional, List, Dict, Any
from models import VehicleType, ParkingSlot, ParkingTicket, PricingRule
from database import DatabaseManager


class ParkingSystemController:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_segregated_slots(self, vehicle_type: Optional[VehicleType] = None) -> List[ParkingSlot]:
        """Returns all slots or slots segregated by vehicle type."""
        return self.db.get_all_slots(vehicle_type)

    def find_available_slot(self, vehicle_type: VehicleType) -> Optional[ParkingSlot]:
        """Auto-allocation: Finds the lowest-numbered vacant slot in the segregated zone."""
        slots = self.db.get_all_slots(vehicle_type)
        for slot in slots:
            if not slot.is_occupied:
                return slot
        return None

    def get_available_slots_count(self, vehicle_type: VehicleType) -> int:
        """Returns the number of free slots in the given vehicle zone."""
        slots = self.db.get_all_slots(vehicle_type)
        return sum(1 for s in slots if not s.is_occupied)

    def park_vehicle(
        self,
        vehicle_no: str,
        vehicle_type: VehicleType,
        slot_id: Optional[str] = None,
        owner_name: str = "",
        phone: str = "",
        simulated_entry_time: Optional[datetime] = None
    ) -> Tuple[bool, str, Optional[ParkingTicket]]:
        """
        Validates, segregates, and checks in a vehicle.
        Assigns the designated slot or auto-allocates one.
        """
        clean_no = vehicle_no.strip().upper()
        if not clean_no:
            return False, "Vehicle registration number cannot be empty.", None

        # Check if already parked
        existing_ticket = self.db.get_active_ticket_by_vehicle(clean_no)
        if existing_ticket:
            return False, f"Vehicle '{clean_no}' is already parked in Slot {existing_ticket.slot_id}!", None

        # Verify or auto-allocate slot
        target_slot: Optional[ParkingSlot] = None
        if slot_id:
            target_slot = self.db.get_slot_by_id(slot_id)
            if not target_slot:
                return False, f"Invalid slot '{slot_id}' specified.", None
            if target_slot.vehicle_type != vehicle_type:
                return False, (
                    f"Slot mismatch! Slot '{slot_id}' is reserved for {target_slot.vehicle_type.value}s, "
                    f"cannot park a {vehicle_type.value} here."
                ), None
            if target_slot.is_occupied:
                return False, f"Slot '{slot_id}' is already occupied!", None
        else:
            target_slot = self.find_available_slot(vehicle_type)
            if not target_slot:
                return False, f"No vacant slots available in {vehicle_type.zone_name}!", None

        # Generate ticket ID
        random_suffix = random.randint(100, 999)
        ticket_id = f"TK-{target_slot.slot_id}-{random_suffix}"

        pricing = self.db.get_pricing_rule(vehicle_type)
        entry_time = simulated_entry_time or datetime.now()

        ticket = ParkingTicket(
            ticket_id=ticket_id,
            vehicle_no=clean_no,
            vehicle_type=vehicle_type,
            slot_id=target_slot.slot_id,
            owner_name=owner_name.strip(),
            phone=phone.strip(),
            entry_time=entry_time,
            hourly_rate=pricing.hourly_rate
        )

        success = self.db.create_ticket_and_occupy_slot(ticket)
        if success:
            return True, f"Vehicle '{clean_no}' parked successfully in Bay {target_slot.slot_id}!", ticket
        return False, "Database error occurred while parking vehicle.", None

    def calculate_bill(self, ticket: ParkingTicket, exit_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculates itemized parking duration and segregated tariff charges in INR (₹).
        Standard Indian Parking Tariff Policy:
        - First 15 minutes grace period: 50% concession on base fee
        - Up to 60 minutes: standard base fee (₹40 Car, ₹20 Bike, ₹10 Bicycle)
        - Extended stay (>60 minutes): Base fee + additional hourly rate per extra hour
        """
        end_time = exit_time or datetime.now()
        duration_delta = end_time - ticket.entry_time
        total_seconds = max(0, duration_delta.total_seconds())
        total_minutes = int(total_seconds // 60)
        hours = total_minutes // 60
        mins = total_minutes % 60

        pricing = self.db.get_pricing_rule(ticket.vehicle_type)

        if total_minutes <= 15:
            # 15-minute quick drop/pickup concession
            total_fee = round(pricing.minimum_charge * 0.5, 2)
            billable_hours = 0.25
        elif total_minutes <= 60:
            total_fee = pricing.base_fee
            billable_hours = 1.0
        else:
            extra_minutes = total_minutes - 60
            extra_hours = math.ceil(extra_minutes / 60)
            total_fee = pricing.base_fee + (extra_hours * pricing.hourly_rate)
            billable_hours = 1 + extra_hours

        return {
            "ticket_id": ticket.ticket_id,
            "vehicle_no": ticket.vehicle_no,
            "vehicle_type": ticket.vehicle_type.value,
            "slot_id": ticket.slot_id,
            "entry_time": ticket.entry_time,
            "exit_time": end_time,
            "duration_str": f"{hours}h {mins}m ({total_minutes} mins)",
            "duration_minutes": total_minutes,
            "base_fee": pricing.base_fee,
            "hourly_rate": pricing.hourly_rate,
            "billable_hours": billable_hours,
            "total_fee": round(total_fee, 2)
        }

    def checkout_vehicle(
        self,
        identifier: str,
        simulated_exit_time: Optional[datetime] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Checks out vehicle by Vehicle Number, Ticket ID, or Slot ID.
        Calculates fee in INR (₹), updates database, and releases slot.
        """
        clean_id = identifier.strip().upper()
        if not clean_id:
            return False, "Please enter a Vehicle Number, Ticket ID, or Slot ID.", None

        # Search ticket
        ticket = self.db.get_active_ticket_by_vehicle(clean_id)
        if not ticket:
            ticket = self.db.get_ticket_by_id(clean_id)
        if not ticket:
            ticket = self.db.get_active_ticket_by_slot(clean_id)

        if not ticket or ticket.status != "ACTIVE":
            return False, f"No active parking ticket found for '{clean_id}'.", None

        exit_time = simulated_exit_time or datetime.now()
        bill = self.calculate_bill(ticket, exit_time)

        success, slot_id = self.db.complete_ticket_and_free_slot(
            ticket_id=ticket.ticket_id,
            exit_time=exit_time,
            duration_minutes=bill["duration_minutes"],
            total_fee=bill["total_fee"]
        )

        if success:
            return True, f"Vehicle '{ticket.vehicle_no}' checked out successfully from Bay {slot_id}!", bill
        return False, "Failed to complete checkout in database.", None

    def generate_ticket_text(self, ticket: ParkingTicket) -> str:
        """Generates a neat monospace printable parking slip in Indian Rupees (₹)."""
        divider = "=" * 38
        sub_div = "-" * 38
        entry_str = ticket.entry_time.strftime("%d-%b-%Y  %I:%M %p")
        pricing = self.db.get_pricing_rule(ticket.vehicle_type)

        lines = [
            divider,
            "       SMART PARKING SYSTEM INDIA     ",
            "     AUTOMATED VEHICLE SEGREGATION    ",
            divider,
            f" TICKET NO  : {ticket.ticket_id}",
            f" VEHICLE NO : {ticket.vehicle_no}",
            f" CATEGORY   : {ticket.vehicle_type.value.upper()} ({ticket.vehicle_type.icon})",
            f" ZONE / BAY : {ticket.slot_id} [{ticket.vehicle_type.zone_name}]",
            f" ENTRY TIME : {entry_str}",
            sub_div,
            f" Base Charge: Rs. {pricing.base_fee:.2f} (1st hr)",
            f" Hourly Rate: Rs. {pricing.hourly_rate:.2f}/hr after",
            f" Driver Name: {ticket.owner_name or 'N/A'}",
            f" Contact No : {ticket.phone or 'N/A'}",
            sub_div,
            "   |||| ||| ||||||| |||| || |||||   ",
            f"       * {ticket.ticket_id} *       ",
            sub_div,
            " * Pay via FASTag / UPI at exit * ",
            " * Please retain ticket for checkout * ",
            " * Park in designated bays only * ",
            divider
        ]
        return "\n".join(lines)

    def generate_receipt_text(self, bill: Dict[str, Any]) -> str:
        """Generates a neat monospace printable tax invoice receipt in Indian Rupees (₹)."""
        divider = "=" * 40
        sub_div = "-" * 40
        entry_str = bill["entry_time"].strftime("%d-%b-%Y %I:%M %p")
        exit_str = bill["exit_time"].strftime("%d-%b-%Y %I:%M %p")

        # GST breakdown simulation (18% GST: 9% CGST + 9% SGST inclusive)
        total_fee = bill["total_fee"]
        taxable_amt = round(total_fee / 1.18, 2)
        gst_amt = round(total_fee - taxable_amt, 2)
        cgst = round(gst_amt / 2, 2)
        sgst = round(gst_amt / 2, 2)

        lines = [
            divider,
            "      SMART PARKING MANAGEMENT SYSTEM   ",
            "             TAX INVOICE / RECEIPT      ",
            divider,
            f" TICKET ID     : {bill['ticket_id']}",
            f" VEHICLE NO    : {bill['vehicle_no']}",
            f" VEHICLE TYPE  : {bill['vehicle_type']}",
            f" BAY RELEASED  : {bill['slot_id']}",
            sub_div,
            f" ENTRY TIME    : {entry_str}",
            f" EXIT TIME     : {exit_str}",
            f" TOTAL DURATION: {bill['duration_str']}",
            sub_div,
            f" Base Fee      : Rs. {bill['base_fee']:.2f}",
            f" Subsequent    : Rs. {bill['hourly_rate']:.2f}/hr",
            f" Billable Hrs  : {bill['billable_hours']} hr(s)",
            sub_div,
            f" Taxable Value : Rs. {taxable_amt:.2f}",
            f" CGST (9%)     : Rs. {cgst:.2f}",
            f" SGST (9%)     : Rs. {sgst:.2f}",
            sub_div,
            f" TOTAL PAID    : Rs. {bill['total_fee']:.2f} (INR)",
            f" PAYMENT MODE  : UPI / FASTag / CASH / CARD",
            f" PAYMENT STATUS: SUCCESSFUL / PAID",
            sub_div,
            "   THANK YOU FOR VISITING OUR FACILITY  ",
            "           HAVE A SAFE DRIVE!           ",
            divider
        ]
        return "\n".join(lines)

    def export_tickets_to_csv(self, filepath: str) -> Tuple[bool, str]:
        """Exports all tickets and billing logs to CSV in Indian Rupees (₹)."""
        try:
            tickets = self.db.fetch_tickets(vehicle_type_filter="ALL", status_filter="ALL")
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Ticket ID", "Vehicle Plate", "Category", "Bay / Slot",
                    "Driver Name", "Contact", "Entry Time", "Exit Time",
                    "Duration (Mins)", "Hourly Rate (INR Rs.)", "Total Fee (INR Rs.)", "Status"
                ])
                for t in tickets:
                    writer.writerow([
                        t.ticket_id,
                        t.vehicle_no,
                        t.vehicle_type.value,
                        t.slot_id,
                        t.owner_name,
                        t.phone,
                        t.entry_time.isoformat(),
                        t.exit_time.isoformat() if t.exit_time else "",
                        t.duration_minutes,
                        f"Rs. {t.hourly_rate:.2f}",
                        f"Rs. {t.total_fee:.2f}",
                        t.status
                    ])
            return True, f"Successfully exported {len(tickets)} records to {filepath}"
        except Exception as e:
            return False, f"Failed to export CSV: {str(e)}"
