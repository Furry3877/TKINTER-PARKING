# 🅿️ Smart Parking Management System (India / INR Edition)
### Real-Time Vehicle Segregation System in Indian Rupees (₹)
**Available as both a Web Application (Single-Page App) & a Desktop GUI (Tkinter)**

---

## 📑 Table of Contents
1. [Overview & Highlights](#-overview--highlights)
2. [Indian Rupee (₹) Tariff Architecture](#-indian-rupee--tariff-architecture)
3. [REST API Documentation](#-rest-api-documentation)
4. [GUI & Web Implementation (5 Marks Breakdown)](#-gui--web-implementation-5-marks-breakdown)
5. [Code Implementation & Event Handling](#-code-implementation--event-handling)
6. [How to Run (Web & Desktop)](#-how-to-run-the-application)
7. [Automated Test Suite](#-automated-test-suite)

---

## 🌟 Overview & Highlights

A parking management application tailored for Indian urban infrastructure with vehicle segregation across three dedicated zones:
- 🚗 **Zone C: Cars & SUVs**: 12 designated bays (`C-01` to `C-12`)
- 🏍️ **Zone M: Two-Wheelers & Bikes**: 16 designated bays (`M-01` to `M-16`)
- 🚲 **Zone B: Bicycles**: 20 designated racks (`B-01` to `B-20`)

### ⚡ 100% Offline Architecture:
- **Zero External Dependencies / CDNs**: All Google font dependencies removed; runs on high-grade native system font stacks (`Segoe UI`, `-apple-system`, `Consolas`).
- **Service Worker (`service-worker.js`) & PWA Manifest**: Caches application shell assets for offline Progressive Web App execution.
- **Dual Offline Execution Modes**:
  1. **Local Server Mode (SQLite)**: Double-click `run_web.bat` or run `python web_server.py 5000` locally without any internet connection.
  2. **Standalone Browser File Mode (`file:///`)**: Double-click `web/index.html` directly in any browser without even running Python! The integrated client-side `OfflineParkingEngine` manages bays, tariffs, ticket slips, and CSV export via `localStorage` and `Blob` APIs.
- **Currency in Indian Rupees (₹)** throughout UI, calculations, slips, and audit logs.
- **Support for Indian Vehicle Registration Formats** (e.g. `DL-01-AB-1234`, `MH-12-DE-9981`, `KA-05-MJ-2024`, `HR-26-EX-3344`).
- **Payment Integration Simulation**: FASTag, UPI (GPay / PhonePe / Paytm / BHIM), Cash, and RuPay/Card.
- **Tax Invoice with GST Simulation**: Itemized CGST (9%) and SGST (9%) on receipts.

---

## 💰 Indian Rupee (₹) Tariff Architecture

Vehicles are strictly segregated into dedicated parking bays with category tariffs:

| Vehicle Category | Zone Name | Bays | Base Rate (1st Hour) | Hourly Rate (Subsequent) | 15-Min Concession |
|---|:---:|:---:|:---:|:---:|:---:|
| 🚗 **Cars & SUVs** | Zone C | 12 bays (`C-01` to `C-12`) | **₹40.00** | **₹20.00 / hr** | ₹20.00 |
| 🏍️ **Two-Wheelers** | Zone M | 16 bays (`M-01` to `M-16`) | **₹20.00** | **₹10.00 / hr** | ₹10.00 |
| 🚲 **Bicycles** | Zone B | 20 racks (`B-01` to `B-20`) | **₹10.00** | **₹5.00 / hr** | ₹5.00 |

### Billing Calculation Formula:
- **Short Stay (≤ 15 minutes)**: 50% concession on base rate.
- **Standard Stay (16 to 60 minutes)**: Base fee covers the entire first hour.
- **Extended Stay (> 60 minutes)**:
  $$\text{Total Fee (₹)} = \text{Base Fee} + \lceil\frac{\text{Minutes} - 60}{60}\rceil \times \text{Hourly Rate}$$

---

## 🌐 REST API Documentation

| Endpoint | Method | Response / Payload | Description |
|---|:---:|:---:|---|
| `/` | `GET` | HTML5 / CSS3 / JS | Delivers the Single-Page Application dashboard |
| `/api/stats` | `GET` | JSON | Live occupancy counts per zone, percentages, and total revenue in ₹ |
| `/api/slots` | `GET` | JSON | Status, vehicle number, and stay duration for all 48 bays |
| `/api/tickets` | `GET` | JSON | Searchable list of active and completed parking sessions |
| `/api/preview_checkout` | `GET` | JSON | Pre-computes parking fee, duration, and GST before collecting payment |
| `/api/park` | `POST` | JSON | Validates plate, checks in vehicle, allocates bay, generates ticket slip |
| `/api/checkout` | `POST` | JSON | Processes payment, releases bay, and generates printable tax invoice |
| `/api/demo` | `POST` | JSON | Seeds 7 realistic Indian demo vehicles across zones |
| `/api/export_csv` | `GET` | CSV File | Downloads audit logs formatted in Indian Rupees (₹) |

---

## 🎨 GUI & Web Implementation (5 Marks Breakdown)

| Component | Web Application (SPA) | Desktop Application (Tkinter) | Design Value |
|---|---|---|---|
| **Header Bar** | Sticky deep slate `#0F172A` banner with live digital clock, system title, and action buttons | Slate `#0F172A` frame with live digital clock (`Consolas`) and action toolbar | Professional enterprise look |
| **KPI Metric Cards** | 4 responsive cards showing live occupancy for **Zone C**, **Zone M**, **Zone B**, and **Total Revenue (₹)** | 4 themed cards with colored accent strips and dynamic text | Real-time situational awareness |
| **Interactive Lot Grid** | 48 visual bays with color coding: 🟢 Green (Vacant), 🔴 Red (Occupied), 🟡 Gold (Selected) | 48 styled frames with slot ID, vehicle icon, and status badge | Instant visual status replacement for text tables |
| **Hover Tooltips** | Hover shows vehicle plate, arrival time, and quick click actions | Custom `ToolTip` popup showing vehicle info and arrival time | Ergonomic contextual feedback |
| **Split Workstation** | Tabbed left operations (Check-In, Check-Out, Tariffs) & right visual map/table | Tabbed left panel (Check-In, Check-Out, Tariffs) & right visual map/table | High operational efficiency |
| **Printable Slips** | Modal with formatted monospace slip, simulated barcode, Copy and `window.print()` | Modal `SlipDialog` with monospace slip, Copy to clipboard, and Save to file | Completes real-world parking workflow |

---

## ⚡ Code Implementation & Event Handling

| Event | Target | Handler | Action Performed |
|---|---|---|---|
| `input` / `<KeyRelease>` | License Plate Input | Plate listener | Auto-capitalizes input and runs instant validation to check if plate is already parked. |
| `change` / `<<ComboboxSelected>>` | Category Dropdown | Category listener | Filters available bays to match the selected zone and updates tariff preview. |
| `click` / `<Button-1>` | Parking Bay Tile | `handleSlotClick()` | **Smart Routing**: If bay is vacant, switches to Check-In with bay pre-selected. If occupied, switches to Check-Out and displays the live bill. |
| `mouseenter` / `<Enter>` | Parking Bay Tile | Hover handler | Displays floating tooltip with bay status, parked vehicle plate, and check-in timestamp. |
| `input` / `<KeyRelease>` | Search Box | Table filter listener | Instant keystroke search filtering across plate, ticket, driver, and bay without submit button. |
| `click` / `<<TreeviewSelect>>` | Table Row | Table select handler | Pre-loads active vehicle into Check-Out and highlights its bay on the visual map. |
| `setInterval` / `after(1000)` | Clock Timer | Clock tick handler | Updates live digital clock and refreshes stay durations every second. |
| `setInterval(5000)` | Auto-Poll Timer | Background sync | Synchronizes active bays and revenue across all open browser tabs. |

---

## 🚀 How to Run the Application

### 🌐 Option 1: Web Application (Single-Page App)
Simply double-click:
```
run_web.bat
```
*(Starts the server and automatically opens `http://localhost:5000` in your web browser)*

Or run manually:
```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" web_server.py 5000
```
Then visit: **`http://localhost:5000`**

---

### 🖥️ Option 2: Desktop GUI Application (Tkinter)
Simply double-click:
```
run.bat
```
Or run manually:
```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" main.py
```

---

## 🧪 Automated Test Suite

All 11 unit and integration tests validate segregation enforcement, auto-allocation, duplicate entry checks, fee calculations in Indian Rupees (₹), and REST API endpoints.

To run tests:
```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" -m unittest discover -p "test_*.py"
```

Expected output:
```
...........
----------------------------------------------------------------------
Ran 11 tests in 0.256s

OK
```
