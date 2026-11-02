"""
src/taxonomy.py
---------------
Canonical Complaint Taxonomy and Department Routing Reference.

Defines the finalized, authoritative 11-category classification scheme
for the AI-Powered College Complaint Intelligence System.
Serves as the single source of truth across dataset generation, preprocessing,
model inference, backend routing, frontend display, and documentation.
"""

from __future__ import annotations

from typing import Final

# Canonical 11-Category Taxonomy: Code -> Official Description
CANONICAL_TAXONOMY: Final[dict[str, str]] = {
    "C01": "Hostel and Accommodation",
    "C02": "Electricity and Water",
    "C03": "Internet and Network",
    "C04": "Mess and Food",
    "C05": "Academic and Examination",
    "C06": "Classroom and Laboratory",
    "C07": "Sanitation and Cleanliness",
    "C08": "Campus Safety",
    "C09": "Transportation",
    "C10": "Administrative Services",
    "C11": "Other / Unclassified",
}

# Category Code -> Primary Campus Administrative Department
CATEGORY_DEPARTMENTS: Final[dict[str, str]] = {
    "C01": "Hostel Administration & Chief Warden Office",
    "C02": "Estate Maintenance & Works Department (Electrical & Civil)",
    "C03": "Campus IT Services & Network Operations Center",
    "C04": "Dining Services & Mess Management Committee",
    "C05": "Office of Academic Affairs & Controller of Examinations",
    "C06": "Instructional Facilities & Laboratory Maintenance",
    "C07": "Campus Sanitation & Housekeeping Department",
    "C08": "Campus Security & Proctorial Board",
    "C09": "Transport Section & Campus Fleet Operations",
    "C10": "Central Administrative & Student Welfare Office",
    "C11": "Student Grievance Redressal Cell / Dean of Student Welfare",
}

# Detailed Scope Definition for Each Complaint Category
CATEGORY_DESCRIPTIONS: Final[dict[str, str]] = {
    "C01": "Residential hostel living conditions, room allocation, furniture, hostel amenities, and warden assistance.",
    "C02": "Power outages, electrical wiring, voltage fluctuations, drinking water supply, plumbing, geysers, and water coolers.",
    "C03": "Campus Wi-Fi connectivity, LAN ports, network outages, bandwidth throttling, and firewall/portal access issues.",
    "C04": "Mess food hygiene, meal quality, dining hall seating, drinking water in mess, dietary requirements, and catering complaints.",
    "C05": "Course registration, grading, lecture schedules, examination clashes, faculty absence, mark sheets, and academic records.",
    "C06": "Classroom projectors, laboratory computers, scientific apparatus, smart boards, laboratory benches, and lab consumables.",
    "C07": "Washroom hygiene, trash collection, corridor cleaning, sewage blockage, pest control, and campus sanitation.",
    "C08": "Security patrol, night lighting, unauthorized intruders, ragging, harassment, emergency response, and safety escorts.",
    "C09": "Campus shuttle timing, route frequency, bus conditions, bus stop shelters, pass issuance, and student transport delays.",
    "C10": "Fee payment receipts, scholarship disbursal, bonafide certificates, ID card issuance, library clearance, and registrar services.",
    "C11": "Cross-cutting grievances, ambiguous inquiries, unclassified campus issues, or complaints requiring specialized Dean review.",
}


def get_canonical_categories() -> list[str]:
    """Return sorted list of all 11 canonical category codes."""
    return sorted(CANONICAL_TAXONOMY.keys())


def get_category_name(code: str) -> str:
    """Resolve a category code to its canonical title."""
    return CANONICAL_TAXONOMY.get(code, CANONICAL_TAXONOMY["C11"])


def get_department_for_category(code: str) -> str:
    """Resolve a category code to its handling administrative department."""
    return CATEGORY_DEPARTMENTS.get(code, CATEGORY_DEPARTMENTS["C11"])


def validate_category_code(code: str) -> bool:
    """Check if a category code belongs to the canonical taxonomy."""
    return code in CANONICAL_TAXONOMY

