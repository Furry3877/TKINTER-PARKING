"""
Smart Parking Management System - GUI & Event Handling Layer (Indian Rupee / INR Edition)
Provides a modern Tkinter user interface with vehicle segregation (Cars, Bikes, Bicycles),
interactive visual parking lot map, live billing in INR (₹), and event handling.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from models import VehicleType, ParkingSlot, ParkingTicket
from database import DatabaseManager
from parking_system import ParkingSystemController


# ----------------------------------------------------------------------
# Modern Color Palette
# ----------------------------------------------------------------------
COLORS = {
    "bg_main": "#F8FAFC",         # Slate 50
    "bg_card": "#FFFFFF",         # Pure White
    "bg_dark": "#0F172A",         # Slate 900
    "primary": "#2563EB",         # Royal Blue
    "primary_hover": "#1D4ED8",
    "success": "#10B981",         # Emerald Green (Vacant)
    "danger": "#EF4444",          # Crimson Red (Occupied)
    "warning": "#F59E0B",         # Amber/Gold (Selected)
    "car_zone": "#3B82F6",        # Car Zone Blue
    "bike_zone": "#F59E0B",       # Bike Zone Amber
    "bicycle_zone": "#10B981",    # Bicycle Zone Green
    "text_main": "#1E293B",       # Slate 800
    "text_muted": "#64748B",      # Slate 500
    "border": "#E2E8F0",          # Slate 200
    "border_highlight": "#3B82F6",
}


# ----------------------------------------------------------------------
# Floating ToolTip Component
# ----------------------------------------------------------------------
class ToolTip:
    """Provides hover popup information over parking bays and controls."""
    def __init__(self, widget: tk.Widget, text_callback):
        self.widget = widget
        self.text_callback = text_callback
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        text = self.text_callback() if callable(self.text_callback) else self.text_callback
        if not text:
            return
        
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)

        frame = tk.Frame(tw, bg="#1E293B", bd=1, relief="solid")
        frame.pack()
        lbl = tk.Label(
            frame,
            text=text,
            justify="left",
            bg="#1E293B",
            fg="#F8FAFC",
            font=("Segoe UI", 9),
            padx=8,
            pady=5
        )
        lbl.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# ----------------------------------------------------------------------
# Modal Dialog for Printable Receipts & Tickets (INR ₹)
# ----------------------------------------------------------------------
class SlipDialog(tk.Toplevel):
    def __init__(self, parent, title: str, content: str):
        super().__init__(parent)
        self.title(title)
        self.geometry("460x560")
        self.minsize(400, 480)
        self.configure(bg=COLORS["bg_main"])
        self.transient(parent)
        self.grab_set()

        self._build_ui(title, content)

    def _build_ui(self, title: str, content: str):
        header = tk.Frame(self, bg=COLORS["bg_dark"], height=50)
        header.pack(fill="x", side="top")
        tk.Label(
            header,
            text=title,
            font=("Segoe UI", 12, "bold"),
            fg="white",
            bg=COLORS["bg_dark"]
        ).pack(side="left", padx=16, pady=12)

        txt_frame = tk.Frame(self, bg=COLORS["bg_main"], padx=15, pady=10)
        txt_frame.pack(fill="both", expand=True)

        self.text_area = tk.Text(
            txt_frame,
            font=("Courier New", 10),
            bg="#FFFFFF",
            fg="#0F172A",
            relief="solid",
            bd=1,
            padx=12,
            pady=12
        )
        self.text_area.insert("1.0", content)
        self.text_area.configure(state="disabled")
        self.text_area.pack(fill="both", expand=True)

        btn_frame = tk.Frame(self, bg=COLORS["bg_main"], pady=10)
        btn_frame.pack(fill="x", side="bottom")

        tk.Button(
            btn_frame,
            text="📋 Copy Slip",
            font=("Segoe UI", 9),
            bg="#E2E8F0",
            relief="flat",
            padx=10,
            pady=5,
            command=self._copy_clipboard
        ).pack(side="left", padx=15)

        tk.Button(
            btn_frame,
            text="💾 Save Text",
            font=("Segoe UI", 9),
            bg="#E2E8F0",
            relief="flat",
            padx=10,
            pady=5,
            command=lambda: self._save_to_file(content)
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Close",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["primary"],
            fg="white",
            relief="flat",
            padx=16,
            pady=5,
            command=self.destroy
        ).pack(side="right", padx=15)

    def _copy_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.text_area.get("1.0", "end-1c"))
        messagebox.showinfo("Copied", "Slip copied to clipboard!", parent=self)

    def _save_to_file(self, content: str):
        filepath = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Parking Slip"
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Slip saved to {filepath}", parent=self)


# ----------------------------------------------------------------------
# Main Application Window (Desktop GUI)
# ----------------------------------------------------------------------
class SmartParkingApp(tk.Tk):
    def __init__(self, controller: ParkingSystemController):
        super().__init__()
        self.ctrl = controller
        self.selected_slot_id: Optional[str] = None
        self.slot_widgets: Dict[str, Dict[str, Any]] = {}

        self.title("Smart Parking Management System (India) - INR (₹)")
        self.geometry("1280x820")
        self.minsize(1100, 700)
        self.configure(bg=COLORS["bg_main"])

        self._init_ttk_styles()

        self._build_header()
        self._build_kpi_dashboard()
        self._build_main_content()
        self._build_status_bar()

        self._bind_global_events()

        self.refresh_all_views()
        self._tick_clock()

    def _init_ttk_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background="#FFFFFF",
            foreground=COLORS["text_main"],
            fieldbackground="#FFFFFF",
            font=("Segoe UI", 9),
            rowheight=26
        )
        style.configure(
            "Treeview.Heading",
            background="#F1F5F9",
            foreground=COLORS["text_main"],
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )
        style.map("Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", "#1E3A8A")])

        style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=[16, 8],
            background="#E2E8F0",
            foreground="#475569"
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#FFFFFF")],
            foreground=[("selected", COLORS["primary"])]
        )

    def _build_header(self):
        header_frame = tk.Frame(self, bg=COLORS["bg_dark"], height=65)
        header_frame.pack(fill="x", side="top")

        brand_frame = tk.Frame(header_frame, bg=COLORS["bg_dark"])
        brand_frame.pack(side="left", padx=20, pady=10)

        title_lbl = tk.Label(
            brand_frame,
            text="🅿️ SMART PARKING SYSTEM (INDIA)",
            font=("Segoe UI", 14, "bold"),
            fg="#FFFFFF",
            bg=COLORS["bg_dark"]
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            brand_frame,
            text="Intelligent Segregation: Cars 🚗 | Two-Wheelers 🏍️ | Bicycles 🚲  •  INR (₹)",
            font=("Segoe UI", 9),
            fg="#94A3B8",
            bg=COLORS["bg_dark"]
        )
        sub_lbl.pack(anchor="w")

        actions_frame = tk.Frame(header_frame, bg=COLORS["bg_dark"])
        actions_frame.pack(side="right", padx=20, pady=10)

        self.clock_lbl = tk.Label(
            actions_frame,
            text="--:--:--",
            font=("Consolas", 11, "bold"),
            fg="#38BDF8",
            bg="#1E293B",
            padx=12,
            pady=4,
            relief="solid",
            bd=1
        )
        self.clock_lbl.pack(side="right", padx=(10, 0))

        tk.Button(
            actions_frame,
            text="⚡ Load Demo Data",
            font=("Segoe UI", 9, "bold"),
            bg="#D97706",
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._handle_load_demo_data
        ).pack(side="right", padx=5)

        tk.Button(
            actions_frame,
            text="📊 Export CSV (₹)",
            font=("Segoe UI", 9),
            bg="#334155",
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._handle_export_csv
        ).pack(side="right", padx=5)

        tk.Button(
            actions_frame,
            text="🔄 Refresh",
            font=("Segoe UI", 9),
            bg="#334155",
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.refresh_all_views
        ).pack(side="right", padx=5)

    def _build_kpi_dashboard(self):
        kpi_frame = tk.Frame(self, bg=COLORS["bg_main"], pady=10, padx=15)
        kpi_frame.pack(fill="x", side="top")

        self.kpi_cards: Dict[str, Dict[str, Any]] = {}

        card_defs = [
            ("Car", "🚗 Zone C: Cars", COLORS["car_zone"], "Rate: ₹40 base + ₹20/hr"),
            ("Bike", "🏍️ Zone M: Two-Wheelers", COLORS["bike_zone"], "Rate: ₹20 base + ₹10/hr"),
            ("Bicycle", "🚲 Zone B: Bicycles", COLORS["bicycle_zone"], "Rate: ₹10 base + ₹5/hr"),
            ("Overview", "📈 Total Revenue (INR)", "#8B5CF6", "UPI / FASTag Ready"),
        ]

        for idx, (key, title, color, subtext) in enumerate(card_defs):
            kpi_frame.grid_columnconfigure(idx, weight=1, uniform="kpi")

            card = tk.Frame(kpi_frame, bg=COLORS["bg_card"], bd=1, relief="solid")
            card.grid(row=0, column=idx, padx=6, sticky="nsew")

            accent_bar = tk.Frame(card, bg=color, height=4)
            accent_bar.pack(fill="x", side="top")

            inner = tk.Frame(card, bg=COLORS["bg_card"], padx=12, pady=8)
            inner.pack(fill="both", expand=True)

            t_lbl = tk.Label(inner, text=title, font=("Segoe UI", 10, "bold"), fg=COLORS["text_main"], bg=COLORS["bg_card"])
            t_lbl.pack(anchor="w")

            main_val_lbl = tk.Label(
                inner,
                text="0 / 0 Occupied",
                font=("Segoe UI", 14, "bold"),
                fg=color,
                bg=COLORS["bg_card"]
            )
            main_val_lbl.pack(anchor="w", pady=(2, 0))

            detail_lbl = tk.Label(
                inner,
                text=subtext,
                font=("Segoe UI", 8),
                fg=COLORS["text_muted"],
                bg=COLORS["bg_card"]
            )
            detail_lbl.pack(anchor="w")

            self.kpi_cards[key] = {
                "main_label": main_val_lbl,
                "detail_label": detail_lbl,
                "subtext": subtext
            }

    def _build_main_content(self):
        container = tk.Frame(self, bg=COLORS["bg_main"], padx=15, pady=5)
        container.pack(fill="both", expand=True)

        self.left_panel = tk.Frame(container, bg=COLORS["bg_card"], width=390, bd=1, relief="solid")
        self.left_panel.pack(side="left", fill="y", padx=(0, 10))
        self.left_panel.pack_propagate(False)

        self._build_operations_notebook(self.left_panel)

        self.right_panel = tk.Frame(container, bg=COLORS["bg_card"], bd=1, relief="solid")
        self.right_panel.pack(side="right", fill="both", expand=True)

        self._build_visual_and_logs_notebook(self.right_panel)

    def _build_operations_notebook(self, parent: tk.Frame):
        self.op_notebook = ttk.Notebook(parent)
        self.op_notebook.pack(fill="both", expand=True, padx=2, pady=2)

        checkin_tab = tk.Frame(self.op_notebook, bg=COLORS["bg_card"], padx=12, pady=12)
        self.op_notebook.add(checkin_tab, text="📥 Check-In (Entry)")
        self._build_checkin_form(checkin_tab)

        checkout_tab = tk.Frame(self.op_notebook, bg=COLORS["bg_card"], padx=12, pady=12)
        self.op_notebook.add(checkout_tab, text="📤 Check-Out (Exit)")
        self._build_checkout_form(checkout_tab)

        tariff_tab = tk.Frame(self.op_notebook, bg=COLORS["bg_card"], padx=12, pady=12)
        self.op_notebook.add(tariff_tab, text="💲 Tariffs (₹)")
        self._build_tariff_tab(tariff_tab)

    def _build_checkin_form(self, parent: tk.Frame):
        tk.Label(
            parent,
            text="Vehicle Entry & Bay Allocation",
            font=("Segoe UI", 11, "bold"),
            fg=COLORS["text_main"],
            bg=COLORS["bg_card"]
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(parent, text="Vehicle Registration Number *", font=("Segoe UI", 9, "bold"), fg=COLORS["text_main"], bg=COLORS["bg_card"]).pack(anchor="w")
        self.entry_veh_no = tk.Entry(parent, font=("Segoe UI", 11, "bold"), bg="#F8FAFC", relief="solid", bd=1)
        self.entry_veh_no.pack(fill="x", pady=(2, 2))
        self.entry_veh_no.bind("<KeyRelease>", self._on_vehicle_no_keyrelease)

        self.lbl_veh_status = tk.Label(parent, text="Enter plate (e.g. DL-01-AB-1234 or MH-12-DE-9981)", font=("Segoe UI", 8), fg=COLORS["text_muted"], bg=COLORS["bg_card"])
        self.lbl_veh_status.pack(anchor="w", pady=(0, 8))

        tk.Label(parent, text="Vehicle Category (Segregated Zone) *", font=("Segoe UI", 9, "bold"), fg=COLORS["text_main"], bg=COLORS["bg_card"]).pack(anchor="w")
        self.var_vehicle_type = tk.StringVar(value=VehicleType.CAR.value)
        self.combo_vehicle_type = ttk.Combobox(
            parent,
            textvariable=self.var_vehicle_type,
            values=[VehicleType.CAR.value, VehicleType.BIKE.value, VehicleType.BICYCLE.value],
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.combo_vehicle_type.pack(fill="x", pady=(2, 6))
        self.combo_vehicle_type.bind("<<ComboboxSelected>>", self._on_vehicle_type_changed)

        tk.Label(parent, text="Designated Parking Bay *", font=("Segoe UI", 9, "bold"), fg=COLORS["text_main"], bg=COLORS["bg_card"]).pack(anchor="w")
        self.var_selected_slot = tk.StringVar(value="AUTO: Next Available")
        self.combo_slots = ttk.Combobox(
            parent,
            textvariable=self.var_selected_slot,
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.combo_slots.pack(fill="x", pady=(2, 6))

        tk.Label(parent, text="Driver Name (Optional)", font=("Segoe UI", 8), fg=COLORS["text_muted"], bg=COLORS["bg_card"]).pack(anchor="w")
        self.entry_driver_name = tk.Entry(parent, font=("Segoe UI", 9), bg="#F8FAFC", relief="solid", bd=1)
        self.entry_driver_name.pack(fill="x", pady=(1, 4))

        tk.Label(parent, text="Mobile Number (Optional)", font=("Segoe UI", 8), fg=COLORS["text_muted"], bg=COLORS["bg_card"]).pack(anchor="w")
        self.entry_phone = tk.Entry(parent, font=("Segoe UI", 9), bg="#F8FAFC", relief="solid", bd=1)
        self.entry_phone.pack(fill="x", pady=(1, 8))

        sim_frame = tk.LabelFrame(parent, text="⏱️ Duration Simulation (For Testing)", font=("Segoe UI", 8, "bold"), fg=COLORS["text_muted"], bg=COLORS["bg_card"], padx=8, pady=4)
        sim_frame.pack(fill="x", pady=(0, 8))

        self.var_sim_hours = tk.IntVar(value=0)
        for text, val in [("Now", 0), ("1h ago", 1), ("2h ago", 2), ("4h ago", 4)]:
            tk.Radiobutton(
                sim_frame,
                text=text,
                value=val,
                variable=self.var_sim_hours,
                bg=COLORS["bg_card"],
                font=("Segoe UI", 8)
            ).pack(side="left", expand=True)

        btn_box = tk.Frame(parent, bg=COLORS["bg_card"])
        btn_box.pack(fill="x", pady=(4, 8))

        self.btn_park = tk.Button(
            btn_box,
            text="📥 Park Vehicle & Print Ticket (₹)",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["primary"],
            fg="white",
            relief="flat",
            pady=7,
            cursor="hand2",
            command=self._handle_park_vehicle
        )
        self.btn_park.pack(fill="x", pady=(0, 4))

        tk.Button(
            btn_box,
            text="Clear Form",
            font=("Segoe UI", 8),
            bg="#E2E8F0",
            relief="flat",
            command=self._clear_checkin_form
        ).pack(fill="x")

        tk.Label(parent, text="Last Issued Ticket Slip", font=("Segoe UI", 8, "bold"), fg=COLORS["text_muted"], bg=COLORS["bg_card"]).pack(anchor="w", pady=(4, 1))
        self.txt_ticket_preview = tk.Text(
            parent,
            font=("Courier New", 8),
            bg="#F1F5F9",
            fg="#0F172A",
            height=7,
            relief="solid",
            bd=1
        )
        self.txt_ticket_preview.pack(fill="both", expand=True)
        self.txt_ticket_preview.insert("1.0", "--- No tickets printed yet ---\nPark a vehicle to generate ticket slip.")
        self.txt_ticket_preview.configure(state="disabled")

        self.btn_view_full_ticket = tk.Button(
            parent,
            text="🔍 View Printable Ticket Slip (INR)",
            font=("Segoe UI", 8, "bold"),
            bg="#F1F5F9",
            relief="solid",
            bd=1,
            state="disabled",
            command=self._view_current_ticket_slip
        )
        self.btn_view_full_ticket.pack(fill="x", pady=(4, 0))

        self.last_generated_ticket: Optional[ParkingTicket] = None

    def _build_checkout_form(self, parent: tk.Frame):
        tk.Label(
            parent,
            text="Vehicle Check-Out & Billing (₹)",
            font=("Segoe UI", 11, "bold"),
            fg=COLORS["text_main"],
            bg=COLORS["bg_card"]
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(parent, text="Select Parked Vehicle / Bay *", font=("Segoe UI", 9, "bold"), fg=COLORS["text_main"], bg=COLORS["bg_card"]).pack(anchor="w")
        self.var_checkout_id = tk.StringVar()
        self.combo_checkout_active = ttk.Combobox(
            parent,
            textvariable=self.var_checkout_id,
            font=("Segoe UI", 10),
            state="readonly"
        )
        self.combo_checkout_active.pack(fill="x", pady=(2, 4))
        self.combo_checkout_active.bind("<<ComboboxSelected>>", self._on_checkout_selection_changed)

        tk.Label(parent, text="Or Enter Vehicle Plate / Ticket ID / Bay:", font=("Segoe UI", 8), fg=COLORS["text_muted"], bg=COLORS["bg_card"]).pack(anchor="w")
        self.entry_checkout_manual = tk.Entry(parent, font=("Segoe UI", 10, "bold"), bg="#F8FAFC", relief="solid", bd=1)
        self.entry_checkout_manual.pack(fill="x", pady=(1, 6))
        self.entry_checkout_manual.bind("<KeyRelease>", self._on_checkout_manual_keyrelease)

        self.bill_preview_frame = tk.LabelFrame(
            parent,
            text="💳 Tariff & Tax Summary",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["text_main"],
            bg=COLORS["bg_card"],
            padx=10,
            pady=8
        )
        self.bill_preview_frame.pack(fill="both", expand=True, pady=6)

        self.lbl_bill_veh = tk.Label(self.bill_preview_frame, text="Vehicle: --", font=("Segoe UI", 9, "bold"), bg=COLORS["bg_card"], anchor="w")
        self.lbl_bill_veh.pack(fill="x")

        self.lbl_bill_slot = tk.Label(self.bill_preview_frame, text="Bay: --", font=("Segoe UI", 9), bg=COLORS["bg_card"], anchor="w")
        self.lbl_bill_slot.pack(fill="x")

        self.lbl_bill_time = tk.Label(self.bill_preview_frame, text="Duration: --", font=("Segoe UI", 9), bg=COLORS["bg_card"], anchor="w")
        self.lbl_bill_time.pack(fill="x")

        self.lbl_bill_rate = tk.Label(self.bill_preview_frame, text="Tariff: --", font=("Segoe UI", 8), fg=COLORS["text_muted"], bg=COLORS["bg_card"], anchor="w")
        self.lbl_bill_rate.pack(fill="x")

        self.lbl_bill_total = tk.Label(
            self.bill_preview_frame,
            text="Total Due: ₹0.00",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS["danger"],
            bg=COLORS["bg_card"],
            pady=4
        )
        self.lbl_bill_total.pack(fill="x")

        self.btn_process_checkout = tk.Button(
            parent,
            text="💳 Free Bay (UPI / FASTag / Cash)",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["success"],
            fg="white",
            relief="flat",
            pady=8,
            cursor="hand2",
            state="disabled",
            command=self._handle_process_checkout
        )
        self.btn_process_checkout.pack(fill="x", pady=(6, 4))

        self.btn_view_receipt = tk.Button(
            parent,
            text="🧾 View Tax Invoice / Receipt",
            font=("Segoe UI", 8, "bold"),
            bg="#F1F5F9",
            relief="solid",
            bd=1,
            state="disabled",
            command=self._view_current_receipt_slip
        )
        self.btn_view_receipt.pack(fill="x", pady=(2, 0))

        self.last_payment_receipt: Optional[Dict[str, Any]] = None

    def _build_tariff_tab(self, parent: tk.Frame):
        tk.Label(
            parent,
            text="Vehicle Segregation Tariff Structure (INR ₹)",
            font=("Segoe UI", 11, "bold"),
            fg=COLORS["text_main"],
            bg=COLORS["bg_card"]
        ).pack(anchor="w", pady=(0, 10))

        rules = [
            ("🚗 Cars (Zone C)", "₹40.00 base (1st hr)", "₹20.00 / hour after", "₹20.00", COLORS["car_zone"]),
            ("🏍️ Two-Wheelers (Zone M)", "₹20.00 base (1st hr)", "₹10.00 / hour after", "₹10.00", COLORS["bike_zone"]),
            ("🚲 Bicycles (Zone B)", "₹10.00 base (1st hr)", "₹5.00 / hour after", "₹5.00", COLORS["bicycle_zone"]),
        ]

        for name, base, hourly, min_fee, col in rules:
            card = tk.LabelFrame(parent, text=name, font=("Segoe UI", 9, "bold"), fg=col, bg=COLORS["bg_card"], padx=10, pady=8)
            card.pack(fill="x", pady=5)
            tk.Label(card, text=f"• First Hour Base Fee : {base}", font=("Segoe UI", 8), bg=COLORS["bg_card"]).pack(anchor="w")
            tk.Label(card, text=f"• Subsequent Rate     : {hourly}", font=("Segoe UI", 8), bg=COLORS["bg_card"]).pack(anchor="w")
            tk.Label(card, text=f"• Grace Period (≤15m) : {min_fee} concession", font=("Segoe UI", 8), bg=COLORS["bg_card"]).pack(anchor="w")

        tk.Label(
            parent,
            text="* Payment accepted via FASTag, UPI, QR, Cash, and Card.",
            font=("Segoe UI", 8, "italic"),
            fg=COLORS["text_muted"],
            bg=COLORS["bg_card"]
        ).pack(anchor="w", pady=(15, 0))

    def _build_visual_and_logs_notebook(self, parent: tk.Frame):
        self.main_notebook = ttk.Notebook(parent)
        self.main_notebook.pack(fill="both", expand=True, padx=2, pady=2)

        visual_tab = tk.Frame(self.main_notebook, bg=COLORS["bg_main"])
        self.main_notebook.add(visual_tab, text="🗺️ Interactive Parking Lot Map")
        self._build_visual_map_view(visual_tab)

        logs_tab = tk.Frame(self.main_notebook, bg=COLORS["bg_card"])
        self.main_notebook.add(logs_tab, text="📋 Parking Records & Audit Logs (₹)")
        self._build_logs_table_view(logs_tab)

    def _build_visual_map_view(self, parent: tk.Frame):
        top_bar = tk.Frame(parent, bg=COLORS["bg_card"], pady=6, padx=12, bd=1, relief="solid")
        top_bar.pack(fill="x", side="top", padx=8, pady=(8, 4))

        tk.Label(
            top_bar,
            text="💡 Tip: Click any VACANT bay to check-in | Click any OCCUPIED bay to check-out",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["primary"],
            bg=COLORS["bg_card"]
        ).pack(side="left")

        legend_frame = tk.Frame(top_bar, bg=COLORS["bg_card"])
        legend_frame.pack(side="right")

        for text, color in [("Available (Vacant)", COLORS["success"]), ("Occupied", COLORS["danger"]), ("Selected", COLORS["warning"])]:
            badge = tk.Label(legend_frame, text="  ", bg=color, relief="solid", bd=1)
            badge.pack(side="left", padx=(10, 4))
            tk.Label(legend_frame, text=text, font=("Segoe UI", 8), bg=COLORS["bg_card"]).pack(side="left")

        canvas_container = tk.Frame(parent, bg=COLORS["bg_main"])
        canvas_container.pack(fill="both", expand=True, padx=8, pady=4)

        canvas = tk.Canvas(canvas_container, bg=COLORS["bg_main"], highlightthickness=0)
        v_scroll = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)

        v_scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.zones_frame = tk.Frame(canvas, bg=COLORS["bg_main"])
        canvas_win = canvas.create_window((0, 0), window=self.zones_frame, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_win, width=event.width)
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", _on_canvas_configure)
        self.zones_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.zone_frames = {}
        self._create_zone_section("Zone C: Cars & SUVs (12 Bays &bull; ₹40 base + ₹20/hr)", VehicleType.CAR, COLORS["car_zone"], 6)
        self._create_zone_section("Zone M: Two-Wheelers & Bikes (16 Bays &bull; ₹20 base + ₹10/hr)", VehicleType.BIKE, COLORS["bike_zone"], 8)
        self._create_zone_section("Zone B: Bicycles (20 Racks &bull; ₹10 base + ₹5/hr)", VehicleType.BICYCLE, COLORS["bicycle_zone"], 10)

    def _create_zone_section(self, title: str, vehicle_type: VehicleType, accent_color: str, cols: int):
        section = tk.LabelFrame(
            self.zones_frame,
            text=f"  {vehicle_type.icon}  {title}  ",
            font=("Segoe UI", 10, "bold"),
            fg=accent_color,
            bg=COLORS["bg_card"],
            padx=10,
            pady=8,
            bd=1,
            relief="solid"
        )
        section.pack(fill="x", expand=True, padx=4, pady=6)
        self.zone_frames[vehicle_type] = (section, cols)

    def _build_logs_table_view(self, parent: tk.Frame):
        toolbar = tk.Frame(parent, bg=COLORS["bg_card"], padx=10, pady=8)
        toolbar.pack(fill="x", side="top")

        tk.Label(toolbar, text="🔍 Search:", font=("Segoe UI", 9, "bold"), bg=COLORS["bg_card"]).pack(side="left", padx=(0, 4))
        self.var_search = tk.StringVar()
        self.entry_search = tk.Entry(toolbar, textvariable=self.var_search, font=("Segoe UI", 9), width=20, bg="#F8FAFC", relief="solid", bd=1)
        self.entry_search.pack(side="left", padx=(0, 15))
        self.entry_search.bind("<KeyRelease>", lambda e: self.filter_logs_table())

        tk.Label(toolbar, text="Category:", font=("Segoe UI", 9), bg=COLORS["bg_card"]).pack(side="left", padx=(0, 4))
        self.var_filter_type = tk.StringVar(value="ALL")
        self.combo_filter_type = ttk.Combobox(
            toolbar,
            textvariable=self.var_filter_type,
            values=["ALL", VehicleType.CAR.value, VehicleType.BIKE.value, VehicleType.BICYCLE.value],
            state="readonly",
            width=10
        )
        self.combo_filter_type.pack(side="left", padx=(0, 15))
        self.combo_filter_type.bind("<<ComboboxSelected>>", lambda e: self.filter_logs_table())

        tk.Label(toolbar, text="Status:", font=("Segoe UI", 9), bg=COLORS["bg_card"]).pack(side="left", padx=(0, 4))
        self.var_filter_status = tk.StringVar(value="ALL")
        self.combo_filter_status = ttk.Combobox(
            toolbar,
            textvariable=self.var_filter_status,
            values=["ALL", "ACTIVE", "COMPLETED"],
            state="readonly",
            width=10
        )
        self.combo_filter_status.pack(side="left", padx=(0, 15))
        self.combo_filter_status.bind("<<ComboboxSelected>>", lambda e: self.filter_logs_table())

        tk.Button(
            toolbar,
            text="Reset Filters",
            font=("Segoe UI", 8),
            bg="#E2E8F0",
            relief="flat",
            command=self._reset_filters
        ).pack(side="left")

        table_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("ticket_id", "vehicle_no", "category", "slot", "driver", "entry_time", "exit_time", "duration", "fee", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("ticket_id", text="Ticket ID")
        self.tree.heading("vehicle_no", text="Vehicle Plate")
        self.tree.heading("category", text="Category")
        self.tree.heading("slot", text="Bay")
        self.tree.heading("driver", text="Driver")
        self.tree.heading("entry_time", text="Entry Time")
        self.tree.heading("exit_time", text="Exit Time")
        self.tree.heading("duration", text="Duration")
        self.tree.heading("fee", text="Fee (₹)")
        self.tree.heading("status", text="Status")

        self.tree.column("ticket_id", width=100, anchor="center")
        self.tree.column("vehicle_no", width=110, anchor="center")
        self.tree.column("category", width=80, anchor="center")
        self.tree.column("slot", width=60, anchor="center")
        self.tree.column("driver", width=110, anchor="w")
        self.tree.column("entry_time", width=120, anchor="center")
        self.tree.column("exit_time", width=120, anchor="center")
        self.tree.column("duration", width=70, anchor="center")
        self.tree.column("fee", width=80, anchor="e")
        self.tree.column("status", width=85, anchor="center")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.tag_configure("ACTIVE", foreground="#DC2626")
        self.tree.tag_configure("COMPLETED", foreground="#059669")

        self.tree.bind("<<TreeviewSelect>>", self._on_treeview_row_selected)

    def _build_status_bar(self):
        status_bar = tk.Frame(self, bg="#0F172A", height=28)
        status_bar.pack(fill="x", side="bottom")

        self.lbl_status_msg = tk.Label(
            status_bar,
            text="🟢 System Ready | Database Connected (smart_parking.db)",
            font=("Segoe UI", 9),
            fg="#94A3B8",
            bg="#0F172A",
            padx=15
        )
        self.lbl_status_msg.pack(side="left")

        self.lbl_status_counts = tk.Label(
            status_bar,
            text="Active Parked: 0 | Total Revenue: ₹0.00",
            font=("Segoe UI", 9, "bold"),
            fg="#38BDF8",
            bg="#0F172A",
            padx=15
        )
        self.lbl_status_counts.pack(side="right")

    def _bind_global_events(self):
        self.bind("<Control-p>", lambda e: self._focus_checkin())
        self.bind("<Control-o>", lambda e: self._focus_checkout())
        self.bind("<Control-f>", lambda e: self.entry_search.focus_set())
        self.bind("<Control-d>", lambda e: self._handle_load_demo_data())
        self.bind("<F5>", lambda e: self.refresh_all_views())
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _focus_checkin(self):
        self.op_notebook.select(0)
        self.entry_veh_no.focus_set()

    def _focus_checkout(self):
        self.op_notebook.select(1)
        self.entry_checkout_manual.focus_set()

    def _on_window_close(self):
        stats = self.ctrl.db.get_summary_statistics()
        if stats["active_count"] > 0:
            ans = messagebox.askyesno(
                "Exit Smart Parking System",
                f"There are currently {stats['active_count']} vehicle(s) parked inside the facility.\n"
                "All records will be preserved in the database.\n\nDo you want to exit now?"
            )
            if not ans:
                return
        self.destroy()

    def _tick_clock(self):
        now_str = datetime.now().strftime("%d-%b-%Y  %I:%M:%S %p")
        self.clock_lbl.config(text=now_str)
        self.after(1000, self._tick_clock)

    def _on_vehicle_no_keyrelease(self, event):
        current_text = self.entry_veh_no.get()
        upper_text = current_text.upper()
        if current_text != upper_text:
            pos = self.entry_veh_no.index(tk.INSERT)
            self.entry_veh_no.delete(0, tk.END)
            self.entry_veh_no.insert(0, upper_text)
            self.entry_veh_no.icursor(pos)

        clean = upper_text.strip()
        if not clean:
            self.lbl_veh_status.config(text="Enter plate (e.g. DL-01-AB-1234 or MH-12-DE-9981)", fg=COLORS["text_muted"])
            return

        ticket = self.ctrl.db.get_active_ticket_by_vehicle(clean)
        if ticket:
            self.lbl_veh_status.config(
                text=f"⚠️ Already parked in Bay {ticket.slot_id}!",
                fg=COLORS["danger"]
            )
        else:
            self.lbl_veh_status.config(
                text=f"✓ Vehicle {clean} eligible for check-in",
                fg=COLORS["success"]
            )

    def _on_vehicle_type_changed(self, event=None):
        vtype = VehicleType(self.var_vehicle_type.get())
        slots = self.ctrl.db.get_all_slots(vtype)
        available = [s.slot_id for s in slots if not s.is_occupied]

        slot_choices = ["AUTO: Next Available"] + available
        self.combo_slots["values"] = slot_choices
        self.combo_slots.set("AUTO: Next Available")
        self._highlight_selected_slot(None)

    def _on_checkout_selection_changed(self, event=None):
        selection = self.var_checkout_id.get()
        if not selection:
            return
        veh_no = selection.split(" | ")[0].strip()
        self.entry_checkout_manual.delete(0, tk.END)
        self.entry_checkout_manual.insert(0, veh_no)
        self._preview_checkout_bill(veh_no)

    def _on_checkout_manual_keyrelease(self, event=None):
        val = self.entry_checkout_manual.get().strip().upper()
        if val:
            self._preview_checkout_bill(val)
        else:
            self._clear_bill_preview()

    def _preview_checkout_bill(self, identifier: str):
        ticket = self.ctrl.db.get_active_ticket_by_vehicle(identifier)
        if not ticket:
            ticket = self.ctrl.db.get_ticket_by_id(identifier)
        if not ticket:
            ticket = self.ctrl.db.get_active_ticket_by_slot(identifier)

        if not ticket or ticket.status != "ACTIVE":
            self._clear_bill_preview()
            self.lbl_bill_veh.config(text=f"No active vehicle found for '{identifier}'", fg=COLORS["danger"])
            self.btn_process_checkout.config(state="disabled")
            return

        bill = self.ctrl.calculate_bill(ticket)
        self.lbl_bill_veh.config(text=f"Vehicle: {bill['vehicle_no']} ({bill['vehicle_type']})", fg=COLORS["text_main"])
        self.lbl_bill_slot.config(text=f"Bay: {bill['slot_id']} | Entry: {bill['entry_time'].strftime('%I:%M %p')}")
        self.lbl_bill_time.config(text=f"Duration: {bill['duration_str']} ({bill['billable_hours']} billable hrs)")
        self.lbl_bill_rate.config(text=f"Rate: Base ₹{bill['base_fee']:.2f} + ₹{bill['hourly_rate']:.2f}/hr")
        self.lbl_bill_total.config(text=f"Total Due: ₹{bill['total_fee']:.2f}")
        self.btn_process_checkout.config(state="normal")
        self._highlight_selected_slot(bill["slot_id"])

    def _clear_bill_preview(self):
        self.lbl_bill_veh.config(text="Vehicle: --", fg=COLORS["text_main"])
        self.lbl_bill_slot.config(text="Bay: --")
        self.lbl_bill_time.config(text="Duration: --")
        self.lbl_bill_rate.config(text="Tariff: --")
        self.lbl_bill_total.config(text="Total Due: ₹0.00")
        self.btn_process_checkout.config(state="disabled")

    def _on_slot_clicked(self, slot_id: str):
        slot = self.ctrl.db.get_slot_by_id(slot_id)
        if not slot:
            return

        self._highlight_selected_slot(slot_id)

        if not slot.is_occupied:
            self.op_notebook.select(0)
            self.var_vehicle_type.set(slot.vehicle_type.value)
            self._on_vehicle_type_changed()
            self.var_selected_slot.set(slot_id)
            self.entry_veh_no.focus_set()
            self.lbl_status_msg.config(text=f"Selected vacant bay {slot_id} ({slot.vehicle_type.value}) for check-in.")
        else:
            self.op_notebook.select(1)
            self.entry_checkout_manual.delete(0, tk.END)
            self.entry_checkout_manual.insert(0, slot_id)
            self._preview_checkout_bill(slot_id)
            self.lbl_status_msg.config(text=f"Selected occupied bay {slot_id} ({slot.current_vehicle_no}) for checkout.")

    def _highlight_selected_slot(self, slot_id: Optional[str]):
        if self.selected_slot_id and self.selected_slot_id in self.slot_widgets:
            old_slot = self.ctrl.db.get_slot_by_id(self.selected_slot_id)
            if old_slot:
                normal_bg = COLORS["danger"] if old_slot.is_occupied else COLORS["success"]
                widget = self.slot_widgets[self.selected_slot_id]["frame"]
                widget.config(bg=normal_bg, bd=1)

        self.selected_slot_id = slot_id
        if slot_id and slot_id in self.slot_widgets:
            widget = self.slot_widgets[slot_id]["frame"]
            widget.config(bg=COLORS["warning"], bd=3)

    def _on_treeview_row_selected(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        values = item["values"]
        if not values:
            return
        
        veh_no = values[1]
        slot_id = values[3]
        status = values[9]

        if status == "ACTIVE":
            self.op_notebook.select(1)
            self.entry_checkout_manual.delete(0, tk.END)
            self.entry_checkout_manual.insert(0, veh_no)
            self._preview_checkout_bill(veh_no)
            self._highlight_selected_slot(slot_id)

    def _handle_park_vehicle(self):
        veh_no = self.entry_veh_no.get().strip().upper()
        vtype = VehicleType(self.var_vehicle_type.get())
        selected_slot = self.var_selected_slot.get()
        slot_id = None if selected_slot.startswith("AUTO") else selected_slot

        driver_name = self.entry_driver_name.get().strip()
        phone = self.entry_phone.get().strip()

        sim_hrs = self.var_sim_hours.get()
        entry_time = datetime.now() - timedelta(hours=sim_hrs) if sim_hrs > 0 else datetime.now()

        success, msg, ticket = self.ctrl.park_vehicle(
            vehicle_no=veh_no,
            vehicle_type=vtype,
            slot_id=slot_id,
            owner_name=driver_name,
            phone=phone,
            simulated_entry_time=entry_time
        )

        if not success:
            messagebox.showwarning("Check-In Error", msg, parent=self)
            return

        self.last_generated_ticket = ticket
        self._update_ticket_preview(ticket)
        self.btn_view_full_ticket.config(state="normal")
        self._clear_checkin_form(keep_ticket=True)
        self.refresh_all_views()
        self.lbl_status_msg.config(text=f"✓ Vehicle {ticket.vehicle_no} parked successfully in Bay {ticket.slot_id}!")
        messagebox.showinfo("Ticket Issued", f"Vehicle parked in Bay {ticket.slot_id}!\nTicket ID: {ticket.ticket_id}\nRate: ₹{ticket.hourly_rate:.2f}/hr", parent=self)

    def _update_ticket_preview(self, ticket: ParkingTicket):
        self.txt_ticket_preview.configure(state="normal")
        self.txt_ticket_preview.delete("1.0", tk.END)
        self.txt_ticket_preview.insert("1.0", self.ctrl.generate_ticket_text(ticket))
        self.txt_ticket_preview.configure(state="disabled")

    def _view_current_ticket_slip(self):
        if self.last_generated_ticket:
            SlipDialog(
                self,
                f"Parking Ticket Slip - {self.last_generated_ticket.ticket_id}",
                self.ctrl.generate_ticket_text(self.last_generated_ticket)
            )

    def _clear_checkin_form(self, keep_ticket: bool = False):
        self.entry_veh_no.delete(0, tk.END)
        self.lbl_veh_status.config(text="Enter plate (e.g. DL-01-AB-1234 or MH-12-DE-9981)", fg=COLORS["text_muted"])
        self.entry_driver_name.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)
        self.var_sim_hours.set(0)
        self._on_vehicle_type_changed()
        if not keep_ticket:
            self.txt_ticket_preview.configure(state="normal")
            self.txt_ticket_preview.delete("1.0", tk.END)
            self.txt_ticket_preview.insert("1.0", "--- No tickets printed yet ---")
            self.txt_ticket_preview.configure(state="disabled")
            self.btn_view_full_ticket.config(state="disabled")
            self.last_generated_ticket = None

    def _handle_process_checkout(self):
        ident = self.entry_checkout_manual.get().strip().upper()
        if not ident:
            messagebox.showwarning("Check-Out", "Please provide a Vehicle Plate, Ticket ID, or Bay.", parent=self)
            return

        success, msg, bill = self.ctrl.checkout_vehicle(ident)
        if not success or not bill:
            messagebox.showerror("Check-Out Failed", msg, parent=self)
            return

        self.last_payment_receipt = bill
        self.btn_view_receipt.config(state="normal")
        self._clear_bill_preview()
        self.entry_checkout_manual.delete(0, tk.END)
        self.refresh_all_views()
        self.lbl_status_msg.config(text=f"✓ Vehicle {bill['vehicle_no']} checked out! Collected: ₹{bill['total_fee']:.2f}")

        receipt_text = self.ctrl.generate_receipt_text(bill)
        SlipDialog(self, f"Tax Invoice Receipt - {bill['ticket_id']}", receipt_text)

    def _view_current_receipt_slip(self):
        if self.last_payment_receipt:
            receipt_text = self.ctrl.generate_receipt_text(self.last_payment_receipt)
            SlipDialog(self, f"Payment Receipt - {self.last_payment_receipt['ticket_id']}", receipt_text)

    def refresh_all_views(self):
        self._refresh_kpis()
        self._render_visual_parking_map()
        self.filter_logs_table()
        self._refresh_active_checkout_combos()
        self._on_vehicle_type_changed()

    def _refresh_kpis(self):
        stats = self.ctrl.db.get_summary_statistics()

        for vtype in [VehicleType.CAR.value, VehicleType.BIKE.value, VehicleType.BICYCLE.value]:
            info = stats[vtype]
            tot = info["total"]
            occ = info["occupied"]
            avail = info["available"]
            pct = int((occ / tot * 100)) if tot > 0 else 0

            card = self.kpi_cards[vtype]
            card["main_label"].config(text=f"{occ} / {tot} Occupied")
            card["detail_label"].config(text=f"{avail} Available ({pct}% Occupancy)")

        ov_card = self.kpi_cards["Overview"]
        ov_card["main_label"].config(text=f"₹{stats['total_revenue']:.2f}")
        ov_card["detail_label"].config(
            text=f"Active: {stats['active_count']} | Completed: {stats['completed_count']}"
        )

        self.lbl_status_counts.config(
            text=f"Active Parked: {stats['active_count']} | Total Revenue: ₹{stats['total_revenue']:.2f}"
        )

    def _render_visual_parking_map(self):
        for slot_id, data in list(self.slot_widgets.items()):
            data["frame"].destroy()
        self.slot_widgets.clear()

        for vtype, (section_frame, cols) in self.zone_frames.items():
            slots = self.ctrl.db.get_all_slots(vtype)
            for c in range(cols):
                section_frame.grid_columnconfigure(c, weight=1, uniform="slot_col")

            for idx, slot in enumerate(slots):
                row = idx // cols
                col = idx % cols

                is_occ = slot.is_occupied
                bg_color = COLORS["danger"] if is_occ else COLORS["success"]

                slot_frame = tk.Frame(
                    section_frame,
                    bg=bg_color,
                    bd=1,
                    relief="solid",
                    cursor="hand2"
                )
                slot_frame.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

                inner = tk.Frame(slot_frame, bg="#FFFFFF", padx=4, pady=4)
                inner.pack(fill="both", expand=True, padx=2, pady=2)

                lbl_id = tk.Label(
                    inner,
                    text=f"{slot.slot_id}",
                    font=("Segoe UI", 9, "bold"),
                    fg=COLORS["text_main"],
                    bg="#FFFFFF"
                )
                lbl_id.pack(anchor="center")

                status_text = slot.current_vehicle_no if is_occ else "VACANT"
                lbl_status = tk.Label(
                    inner,
                    text=f"{vtype.icon}\n{status_text}",
                    font=("Segoe UI", 8),
                    fg=COLORS["danger"] if is_occ else COLORS["success"],
                    bg="#FFFFFF",
                    justify="center"
                )
                lbl_status.pack(anchor="center")

                self.slot_widgets[slot.slot_id] = {
                    "frame": slot_frame,
                    "inner": inner,
                    "slot": slot
                }

                click_handler = lambda e, sid=slot.slot_id: self._on_slot_clicked(sid)
                for w in (slot_frame, inner, lbl_id, lbl_status):
                    w.bind("<Button-1>", click_handler)

                def make_tip(s=slot):
                    if s.is_occupied:
                        since_str = s.occupied_since.strftime("%I:%M %p") if s.occupied_since else "N/A"
                        return (
                            f"Bay: {s.slot_id} ({s.vehicle_type.value})\n"
                            f"Status: OCCUPIED\n"
                            f"Vehicle: {s.current_vehicle_no}\n"
                            f"Parked at: {since_str}\n"
                            f"👉 Click to Check-Out"
                        )
                    else:
                        return (
                            f"Bay: {s.slot_id} ({s.vehicle_type.value})\n"
                            f"Status: AVAILABLE\n"
                            f"Zone: {s.vehicle_type.zone_name}\n"
                            f"👉 Click to Check-In"
                        )

                ToolTip(slot_frame, make_tip)
                ToolTip(inner, make_tip)
                ToolTip(lbl_status, make_tip)

    def _refresh_active_checkout_combos(self):
        active_tickets = self.ctrl.db.fetch_tickets(status_filter="ACTIVE")
        choices = [f"{t.vehicle_no} | Bay {t.slot_id} ({t.vehicle_type.value})" for t in active_tickets]
        self.combo_checkout_active["values"] = choices
        if choices and not self.var_checkout_id.get():
            self.combo_checkout_active.set("Select from active vehicles...")

    def filter_logs_table(self):
        vtype = self.var_filter_type.get()
        status = self.var_filter_status.get()
        query = self.var_search.get()

        tickets = self.ctrl.db.fetch_tickets(
            vehicle_type_filter=vtype,
            status_filter=status,
            search_query=query
        )

        for row in self.tree.get_children():
            self.tree.delete(row)

        for t in tickets:
            entry_str = t.entry_time.strftime("%d-%b %I:%M %p")
            exit_str = t.exit_time.strftime("%d-%b %I:%M %p") if t.exit_time else "--:--"
            dur_str = f"{t.duration_minutes // 60}h {t.duration_minutes % 60}m" if t.status == "COMPLETED" else "Parked"
            fee_str = f"₹{t.total_fee:.2f}" if t.status == "COMPLETED" else "--"

            self.tree.insert(
                "",
                "end",
                values=(
                    t.ticket_id,
                    t.vehicle_no,
                    f"{t.vehicle_type.icon} {t.vehicle_type.value}",
                    t.slot_id,
                    t.owner_name or "--",
                    entry_str,
                    exit_str,
                    dur_str,
                    fee_str,
                    t.status
                ),
                tags=(t.status,)
            )

    def _reset_filters(self):
        self.var_search.set("")
        self.var_filter_type.set("ALL")
        self.var_filter_status.set("ALL")
        self.filter_logs_table()

    def _handle_load_demo_data(self):
        ans = messagebox.askyesno(
            "Load Indian Demo Vehicles",
            "This will populate the parking bays with 7 staggered sample Indian vehicles (Cars, Bikes, Bicycles) "
            "with realistic parked durations for quick fee testing.\n\nContinue?",
            parent=self
        )
        if ans:
            self.ctrl.db.reset_and_seed_demo_data()
            self.refresh_all_views()
            self.lbl_status_msg.config(text="✓ Sample Indian vehicles loaded successfully! Ready for checkout testing.")
            messagebox.showinfo("Demo Data Loaded", "7 sample vehicles loaded across Car, Bike, and Bicycle bays!", parent=self)

    def _handle_export_csv(self):
        filepath = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Parking Audit Records (INR)"
        )
        if filepath:
            success, msg = self.ctrl.export_tickets_to_csv(filepath)
            if success:
                messagebox.showinfo("Export Successful", msg, parent=self)
            else:
                messagebox.showerror("Export Failed", msg, parent=self)
