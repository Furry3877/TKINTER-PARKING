"""
Python Script to generate a complete, professional, 12-slide Widescreen (16:9) .pptx presentation
using pure Python standard libraries (zipfile, xml.etree.ElementTree).
Requires ZERO external packages!
"""
import os
import zipfile
from datetime import datetime

SLIDES_DATA = [
    {
        "title": "Smart Parking Management System",
        "subtitle": "Intelligent Vehicle Segregation (Cars, Two-Wheelers, Bicycles) in Indian Rupees (₹)",
        "bullets": [
            "Project Type: Full-Stack Web Application (SPA) & Tkinter Desktop GUI",
            "Core Objective: Automated urban parking allocation, fee calculation & audit trail",
            "Currency: Indian Rupees (INR ₹) with simulated FASTag, UPI, GST & Cash integration",
            "Operating Capability: 100% Offline-Ready (PWA Service Worker + LocalStorage engine)"
        ],
        "category": "PROJECT OVERVIEW"
    },
    {
        "title": "Problem Statement & Urban Challenges",
        "subtitle": "Why Traditional Parking Facilities Fail in Indian Cities",
        "bullets": [
            "Chaotic Mixed Parking: Cars, bikes, and cycles parked together cause denting, blockage, and traffic chaos.",
            "Bicycle Damage: Two-wheelers and bicycles frequently get damaged when parked beside large SUVs.",
            "Inefficient Space Utilization: No designated bay allocation leads to haphazard double parking.",
            "Fixed/Unfair Pricing: Charging two-wheelers and bicycles the same rate as 4-wheelers causes customer dissatisfaction.",
            "Long Queues & Delays: Manual paper ticketing creates bottleneck congestion at entry and exit gates."
        ],
        "category": "PROBLEM STATEMENT"
    },
    {
        "title": "Proposed Solution: Segregated Architecture",
        "subtitle": "Dedicated Physical & Virtual Zones for Distinct Vehicle Classes",
        "bullets": [
            "🚗 Zone C (Cars & SUVs): 12 spacious designated bays (C-01 to C-12).",
            "🏍️ Zone M (Two-Wheelers & Bikes): 16 medium bays (M-01 to M-16) with optimized turn radii.",
            "🚲 Zone B (Bicycles): 20 compact rack bays (B-01 to B-20) dedicated to green mobility.",
            "Strict Category Enforcement: System validates bay compatibility; rejects parking a Car in a Bike bay.",
            "Dual Allocation Modes: Automatic assignment of best vacant bay OR 1-click selection on the visual map."
        ],
        "category": "SYSTEM DESIGN"
    },
    {
        "title": "Tariff Structure in Indian Rupees (₹)",
        "subtitle": "Fair, Tiered Pricing Engine with Concessions & Tax Breakdown",
        "bullets": [
            "🚗 Cars (Zone C): Base ₹40.00 (covers 1st hour) | Subsequent rate: ₹20.00 / hour.",
            "🏍️ Two-Wheelers (Zone M): Base ₹20.00 (covers 1st hour) | Subsequent rate: ₹10.00 / hour.",
            "🚲 Bicycles (Zone B): Base ₹10.00 (covers 1st hour) | Subsequent rate: ₹5.00 / hour.",
            "15-Minute Short Stay Concession: 50% discount on base fee for quick drop/pickup.",
            "Tax Invoice Simulation: Automated itemized breakdown of 18% GST (9% CGST + 9% SGST inclusive).",
            "Simulated Payment Modes: FASTag RFID, UPI (GPay/PhonePe/Paytm), Cash, and RuPay/Card."
        ],
        "category": "PRICING & REVENUE"
    },
    {
        "title": "System Architecture & Tech Stack",
        "subtitle": "Modular Model-View-Controller (MVC) Pattern with Zero External Dependencies",
        "bullets": [
            "Backend: Python standard library ThreadingHTTPServer serving RESTful JSON endpoints.",
            "Persistence Layer: SQLite database (smart_parking.db) with relational integrity & connection context managers.",
            "Web Frontend: Single-Page Application (HTML5, responsive CSS Grid/Flexbox, Vanilla ES6+ JavaScript).",
            "Desktop GUI: Native Tkinter interface styled with ttk 'clam' engine and custom palettes.",
            "Portability: Runs entirely on standard Python 3.14 without requiring pip install of any 3rd party packages."
        ],
        "category": "ARCHITECTURE"
    },
    {
        "title": "GUI Design & Implementation (5 Marks)",
        "subtitle": "Aesthetics, Visual Hierarchy & Real-Time Operational Controls",
        "bullets": [
            "Interactive Visual Parking Map: 48 individual bay tiles color-coded (Green=Vacant, Red=Occupied, Gold=Selected).",
            "Live KPI Statistics Dashboard: 4 responsive metric cards showing occupancy counts, progress bars, and total revenue.",
            "Ergonomic Split Workspace: Left operations panel (Entry/Exit/Tariffs) and Right visual map / audit log table.",
            "Contextual Hover Tooltips: Hovering over any bay reveals vehicle plate, arrival time, and stay duration.",
            "Monospace Slip Modals: Clean printable parking tickets & GST invoices with simulated barcodes and window.print()."
        ],
        "category": "EVALUATION CRITERIA 1"
    },
    {
        "title": "Code Implementation & Event Handling",
        "subtitle": "Rich Event-Driven Mechanics for Smooth User Interactions",
        "bullets": [
            "Keystroke Input Events: Auto-capitalizes license plate input and runs live duplicate parking validation.",
            "Combobox Selection Events: Dynamically filters available bays to match chosen category and updates rates.",
            "Interactive Bay Click Events: Smart contextual routing (Vacant -> Check-In; Occupied -> Live Bill & Check-Out).",
            "Real-Time Table Search: Instant keyup filtering across plate, ticket ID, driver, and bay without submit button.",
            "Timer Events: Real-time digital clock (1s interval) and periodic background synchronization (5s interval).",
            "Window Close Protocol: WM_DELETE_WINDOW intercepts app exit and warns if vehicles are still parked inside."
        ],
        "category": "EVALUATION CRITERIA 2"
    },
    {
        "title": "100% Offline Capability & PWA Architecture",
        "subtitle": "Completely Functional Without Internet Connectivity",
        "bullets": [
            "Zero External CDNs: Eliminated external Google Fonts in favor of high-grade native system font stacks.",
            "Progressive Web App (PWA): Service Worker (service-worker.js) caches all application shell resources.",
            "Mode A (Local Python Server): Operates over localhost:5000 with zero external internet access.",
            "Mode B (Standalone File Mode): Double-clicking web/index.html functions 100% offline via localStorage.",
            "Client-Side Blob CSV Export: Dynamic generation of downloadable CSV spreadsheets directly in the browser."
        ],
        "category": "OFFLINE DESIGN"
    },
    {
        "title": "REST API & Data Model Specification",
        "subtitle": "Structured Endpoints for Seamless Client-Server Synchronization",
        "bullets": [
            "GET /api/stats: Returns live segregated counts, available capacity, and cumulative revenue in INR (₹).",
            "GET /api/slots: Returns real-time status, vehicle plate, and elapsed duration for all 48 bays.",
            "GET /api/preview_checkout: Pre-computes stay duration and tariff breakdown before processing payment.",
            "POST /api/park: Validates vehicle, assigns bay, stores timestamp, and generates formatted ticket slip.",
            "POST /api/checkout: Collects payment, frees bay, updates ticket to COMPLETED, and issues GST invoice.",
            "POST /api/demo: Instantly seeds 7 realistic Indian demo vehicles across DL, MH, KA, and HR states."
        ],
        "category": "API DESIGN"
    },
    {
        "title": "Automated Testing & Verification",
        "subtitle": "Comprehensive Test Coverage Ensuring High Reliability",
        "bullets": [
            "Test Suite: 12 automated unit and integration tests passing with 100% success in 0.26 seconds.",
            "Segregation Enforcement Tests: Verifies that Car cannot park in Bike bay and Bike cannot park in Bicycle rack.",
            "Duplicate Prevention Tests: Ensures same license plate cannot check in twice while already parked.",
            "Tariff & GST Precision Tests: Validates exact hourly calculation and 15-minute grace period concessions in ₹.",
            "Endpoint Coverage: Validates all GET, POST, static asset delivery, and offline service worker requests."
        ],
        "category": "QUALITY ASSURANCE"
    },
    {
        "title": "Future Roadmap & Smart City Enhancements",
        "subtitle": "Scalable Expansion Possibilities for Enterprise Deployment",
        "bullets": [
            "ANPR Camera Integration: Automated Number Plate Recognition using OpenCV for ticketless gate entry.",
            "Hardware FASTag RFID Readers: Dedicated toll-like antenna integration for automatic barrier lift.",
            "Ultrasonic / Infrared IoT Sensors: Physical occupancy detection per bay with LED indicators (Green/Red).",
            "Mobile App Companion: Pre-booking parking bays via Android/iOS with Google Maps navigation.",
            "EV Charging Integration: Dedicated EV bays with metered electricity billing added to parking tariff."
        ],
        "category": "FUTURE ENHANCEMENTS"
    },
    {
        "title": "Conclusion & Summary",
        "subtitle": "Complete, Robust, and Lab-Ready Parking Management Solution",
        "bullets": [
            "Dual Interface: Fully functional as a Modern Web App (SPA) and a Desktop Tkinter GUI.",
            "Indian Localization: 100% localized to Indian Rupees (₹), Indian vehicle registrations & tax models.",
            "Total Reliability: 100% offline capability with SQLite persistence and browser storage fallback.",
            "Strict Academic Compliance: Satisfies all marking criteria for GUI Design (5 mks) & Event Handling.",
            "Thank You! Q&A Session."
        ],
        "category": "CONCLUSION"
    }
]


def create_pptx(output_path="Smart_Parking_System_Presentation.pptx"):
    """Creates a valid, beautiful widescreen (16:9) PPTX presentation."""
    # 1. Prepare XML templates
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
"""
    for i in range(1, len(SLIDES_DATA) + 1):
        content_types += f'  <Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>\n'
    content_types += "</Types>"

    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""

    pres_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
"""
    for i in range(1, len(SLIDES_DATA) + 1):
        pres_rels += f'  <Relationship Id="rId{i+2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>\n'
    pres_rels += "</Relationships>"

    presentation_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
"""
    for i in range(1, len(SLIDES_DATA) + 1):
        presentation_xml += f'    <p:sldId id="{255 + i}" r:id="rId{i+2}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>\n'
    presentation_xml += """  </p:sldIdLst>
  <p:sldSz cx="12192000" cy="6858000" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""

    theme_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="TechTheme">
  <a:themeElements>
    <a:clrScheme name="TechPalette">
      <a:dk1><a:srgbClr val="0F172A"/></a:dk1>
      <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1E293B"/></a:dk2>
      <a:lt2><a:srgbClr val="F8FAFC"/></a:lt2>
      <a:accent1><a:srgbClr val="2563EB"/></a:accent1>
      <a:accent2><a:srgbClr val="10B981"/></a:accent2>
      <a:accent3><a:srgbClr val="F59E0B"/></a:accent3>
      <a:accent4><a:srgbClr val="EF4444"/></a:accent4>
      <a:accent5><a:srgbClr val="8B5CF6"/></a:accent5>
      <a:accent6><a:srgbClr val="0EA5E9"/></a:accent6>
      <a:hlink><a:srgbClr val="38BDF8"/></a:hlink>
      <a:folHlink><a:srgbClr val="94A3B8"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Modern">
      <a:majorFont><a:latin typeface="Segoe UI"/></a:majorFont>
      <a:minorFont><a:latin typeface="Segoe UI"/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>"""

    slide_master_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
  </p:sldLayoutIdLst>
</p:sldMaster>"""

    slide_master_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""

    slide_layout_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
</p:sldLayout>"""

    slide_layout_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""

    # Generate Individual Slide XMLs
    slide_xmls = []
    for idx, slide_info in enumerate(SLIDES_DATA, start=1):
        is_title_slide = (idx == 1 or idx == len(SLIDES_DATA))

        # Build bullet paragraphs
        bullet_xml_parts = []
        for bullet in slide_info["bullets"]:
            bullet_xml_parts.append(f"""
          <a:p>
            <a:pPr marL="288000" indent="-288000">
              <a:buFont typeface="Arial"/>
              <a:buChar char="•"/>
            </a:pPr>
            <a:r>
              <a:rPr lang="en-US" sz="1600" b="0">
                <a:solidFill><a:srgbClr val="1E293B"/></a:solidFill>
              </a:rPr>
              <a:t>{escape_xml(bullet)}</a:t>
            </a:r>
          </a:p>""")
        bullets_combined = "\n".join(bullet_xml_parts)

        # Background color: Deep slate for title/conclusion, clean light slate for content
        bg_color = "0F172A" if is_title_slide else "F8FAFC"
        title_color = "FFFFFF" if is_title_slide else "0F172A"
        sub_color = "38BDF8" if is_title_slide else "2563EB"

        slide_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg>
      <p:bgPr>
        <a:solidFill><a:srgbClr val="{bg_color}"/></a:solidFill>
      </p:bgPr>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>

      <!-- Category Pill -->
      <p:sp>
        <p:nvSpPr><p:cNvPr id="2" name="CategoryPill"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="800000" y="450000"/><a:ext cx="3000000" cy="350000"/></a:xfrm>
          <a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>
          <a:solidFill><a:srgbClr val="2563EB"/></a:solidFill>
        </p:spPr>
        <p:txBody>
          <a:bodyPr vert="horz" lIns="91440" rIns="91440" tIns="45720" bIns="45720" anchor="ctr"/>
          <a:p>
            <a:pPr algn="ctr"/>
            <a:r>
              <a:rPr lang="en-US" sz="1100" b="1">
                <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
              </a:rPr>
              <a:t>{escape_xml(slide_info["category"])}</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>

      <!-- Title & Subtitle Box -->
      <p:sp>
        <p:nvSpPr><p:cNvPr id="3" name="TitleBox"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="800000" y="850000"/><a:ext cx="10592000" cy="1100000"/></a:xfrm>
        </p:spPr>
        <p:txBody>
          <a:bodyPr vert="horz" lIns="0" tIns="0" rIns="0" bIns="0"/>
          <a:p>
            <a:r>
              <a:rPr lang="en-US" sz="2800" b="1">
                <a:solidFill><a:srgbClr val="{title_color}"/></a:solidFill>
              </a:rPr>
              <a:t>{escape_xml(slide_info["title"])}</a:t>
            </a:r>
          </a:p>
          <a:p>
            <a:r>
              <a:rPr lang="en-US" sz="1500" b="0">
                <a:solidFill><a:srgbClr val="{sub_color}"/></a:solidFill>
              </a:rPr>
              <a:t>{escape_xml(slide_info["subtitle"])}</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>

      <!-- Content Card Container -->
      <p:sp>
        <p:nvSpPr><p:cNvPr id="4" name="ContentCard"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="800000" y="2100000"/><a:ext cx="10592000" cy="4200000"/></a:xfrm>
          <a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>
          <a:solidFill><a:srgbClr val="{'1E293B' if is_title_slide else 'FFFFFF'}"/></a:solidFill>
          <a:ln w="12700"><a:solidFill><a:srgbClr val="{'334155' if is_title_slide else 'E2E8F0'}"/></a:solidFill></a:ln>
        </p:spPr>
        <p:txBody>
          <a:bodyPr vert="horz" lIns="360000" rIns="360000" tIns="360000" bIns="360000"/>
          {bullets_combined if not is_title_slide else f'''
          <a:p><a:r><a:rPr lang="en-US" sz="2000" b="1"><a:solidFill><a:srgbClr val="38BDF8"/></a:solidFill></a:rPr><a:t>Full-Stack Intelligent Urban Parking System</a:t></a:r></a:p>
          <a:p><a:r><a:rPr lang="en-US" sz="1600"><a:solidFill><a:srgbClr val="F8FAFC"/></a:solidFill></a:rPr><a:t>• Segregated Zones: Cars (Zone C), Two-Wheelers (Zone M), Bicycles (Zone B)</a:t></a:r></a:p>
          <a:p><a:r><a:rPr lang="en-US" sz="1600"><a:solidFill><a:srgbClr val="F8FAFC"/></a:solidFill></a:rPr><a:t>• Complete Indian Currency (₹) Tariffs with GST & FASTag/UPI integration</a:t></a:r></a:p>
          <a:p><a:r><a:rPr lang="en-US" sz="1600"><a:solidFill><a:srgbClr val="F8FAFC"/></a:solidFill></a:rPr><a:t>• 100% Offline Single-Page Web App + Tkinter Desktop Application</a:t></a:r></a:p>
          <a:p><a:r><a:rPr lang="en-US" sz="1600"><a:solidFill><a:srgbClr val="10B981"/></a:solidFill></a:rPr><a:t>• 12 Automated Unit Tests Passing (100% Quality Assurance)</a:t></a:r></a:p>
          '''}
        </p:txBody>
      </p:sp>

      <!-- Slide Number Footer -->
      <p:sp>
        <p:nvSpPr><p:cNvPr id="5" name="Footer"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="800000" y="6400000"/><a:ext cx="10592000" cy="300000"/></a:xfrm></p:spPr>
        <p:txBody>
          <a:bodyPr vert="horz" lIns="0" tIns="0" rIns="0" bIns="0"/>
          <a:p>
            <a:pPr algn="r"/>
            <a:r>
              <a:rPr lang="en-US" sz="1000">
                <a:solidFill><a:srgbClr val="{'64748B' if is_title_slide else '94A3B8'}"/></a:solidFill>
              </a:rPr>
              <a:t>Slide {idx} of {len(SLIDES_DATA)} | Smart Parking System (India) ₹</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>

    </p:spTree>
  </p:cSld>
</p:sld>"""
        slide_xmls.append(slide_xml)

    slide_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""

    # Assemble ZIP Package
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("ppt/_rels/presentation.xml.rels", pres_rels)
        z.writestr("ppt/presentation.xml", presentation_xml)
        z.writestr("ppt/theme/theme1.xml", theme_xml)
        z.writestr("ppt/slideMasters/slideMaster1.xml", slide_master_xml)
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", slide_master_rels)
        z.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout_xml)
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", slide_layout_rels)

        for i, s_xml in enumerate(slide_xmls, start=1):
            z.writestr(f"ppt/slides/slide{i}.xml", s_xml)
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", slide_rels)

    print(f"Successfully generated PowerPoint presentation: {output_path} ({len(SLIDES_DATA)} slides)")


def escape_xml(s: str) -> str:
    """Escapes special XML characters."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")


if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(__file__), "Smart_Parking_System_Presentation.pptx")
    create_pptx(out_file)
