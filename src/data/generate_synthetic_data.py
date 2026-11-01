"""
src/data/generate_synthetic_data.py
------------------------------------
Reproducible synthetic complaint generator for college campus intelligence.

Generates realistic complaints across all 11 configured categories:
  C01: Hostel and Accommodation
  C02: Electricity and Water
  C03: Internet and Network
  C04: Mess and Food
  C05: Academic and Examination
  C06: Classroom and Laboratory
  C07: Sanitation and Cleanliness
  C08: Campus Safety
  C09: Transportation
  C10: Administrative Services
  C11: Other / Unclassified

Design principles:
- Fully deterministic with random seed for complete reproducibility.
- Diverse sentence structures, vocabulary, lengths, and realistic noise/typos.
- Includes safety-critical incidents, cross-domain ambiguous complaints,
  and grouped multi-student incident reports.
- Sets explicit data_source='synthetic' on every record.
- NEVER claims to be real student data; used exclusively for pipeline
  development and preliminary experimentation.
"""

from __future__ import annotations

import argparse
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

logger = logging.getLogger(__name__)

# Campus locations
LOCATIONS = [
    "Hostel Block A - Floor 1",
    "Hostel Block A - Floor 3",
    "Hostel Block B - Floor 2",
    "Hostel Block B - Floor 4",
    "Hostel Block C (Girls) - Wing 1",
    "Hostel Block C (Girls) - Wing 2",
    "Hostel Block D (PG Hostel)",
    "Mess Hall 1 (North Dining)",
    "Mess Hall 2 (South Dining)",
    "Central Library - Ground Floor",
    "Central Library - Reading Hall 2",
    "Computer Center - Lab 102",
    "Computer Center - Lab 204",
    "Academic Block 1 - Room 101",
    "Academic Block 1 - Lecture Hall 3",
    "Academic Block 2 - Physics Lab",
    "Academic Block 2 - Chemistry Lab",
    "Mechanical Engineering Workshop",
    "Administrative Block - Registrar Office",
    "Administrative Block - Accounts Section",
    "Sports Complex - Indoor Badminton Court",
    "Campus Health Center",
    "Main Gate & Security Post",
    "Bus Stand & North Gate",
    "Student Activity Center (SAC)",
    "Cafeteria & Canteen",
]

# Common typographical substitutions for realistic noise
TYPO_MAP = {
    "water": ["wtr", "waterr", "watter"],
    "please": ["plz", "pls", "plez"],
    "because": ["coz", "bcaz", "bcoz"],
    "maintenance": ["maintainence", "maintanance"],
    "definitely": ["definately", "definatly"],
    "separate": ["seperate"],
    "receive": ["recieve"],
    "attendance": ["attendence", "attendense"],
    "professor": ["proffesor", "prof"],
    "laboratory": ["labrotary", "lab"],
    "working": ["wrking", "workin"],
    "electricity": ["electrcity", "electricty"],
    "bathroom": ["washroom", "bthroom"],
    "complaint": ["complnt", "complaint"],
    "immediately": ["immediatly", "urgent"],
}

# Rich category-specific semantic templates & seeds
# Each category has varied core problem statements, impacts, and student perspectives.
CATEGORY_COMPLAINTS: dict[str, list[dict[str, Any]]] = {
    "C01": [
        # Hostel and Accommodation
        {"text": "Ceiling fan in room {room} makes a loud screeching noise and wobbles dangerously whenever switched to high speed.", "severity": "medium"},
        {"text": "Bed frame provided in room {room} has two broken wooden slats. Unable to sleep properly for the past three nights.", "severity": "medium"},
        {"text": "Severe water leakage from the upper floor ceiling into room {room}. It is dripping directly onto the study desk and books.", "severity": "high"},
        {"text": "Hostel warden is not allowing entry after 9:30 PM even with valid department project permission slips.", "severity": "low"},
        {"text": "The window mesh in room {room} is torn, allowing swarms of mosquitoes inside every evening.", "severity": "low"},
        {"text": "Balcony door latch in room {room} is broken and keeps banging in the wind. Cannot lock it from inside.", "severity": "medium"},
        {"text": "Cupboard lock was jammed when I moved into room {room}. Caretaker has not visited despite 2 verbal reminders.", "severity": "low"},
        {"text": "The common room television and air conditioning have been non-functional for three weeks.", "severity": "low"},
        {"text": "Plaster from the corridor ceiling near room {room} fell down yesterday evening. Luckily no one was walking underneath.", "severity": "high", "safety": True},
        {"text": "Hostel lift stopped working with four students trapped inside between 2nd and 3rd floors for 25 minutes.", "severity": "critical", "safety": True},
        {"text": "Room allocation issue: assigned a triple-sharing room despite paying full fee for double-occupancy room.", "severity": "medium"},
        {"text": "Hot water geyser in hostel bathroom floor {floor} is tripping the main circuit breaker whenever turned on.", "severity": "high"},
        {"text": "Mattress provided during hostel check-in is damp and infested with bedbugs. Need replacement urgently.", "severity": "medium"},
        {"text": "Hostel study room lights are flickering constantly, making it impossible to prepare for mid-semester exams.", "severity": "low"},
        {"text": "Door handle of hostel room {room} fell off completely. Anyone can push the door open even when closed.", "severity": "medium"},
    ],
    "C02": [
        # Electricity and Water
        {"text": "Complete power outage in {location} since 3:00 PM today. Backup inverter has also drained out.", "severity": "high"},
        {"text": "No running water supply in washrooms of {location} for over 18 hours. Daily hygiene severely affected.", "severity": "high"},
        {"text": "Water coming out of the taps in {location} is yellowish and muddy with foul rust odor.", "severity": "high"},
        {"text": "Exposed electrical wires hanging outside the switchboard in {location}. High risk of electric shock.", "severity": "critical", "safety": True},
        {"text": "Drinking water cooler on floor {floor} is leaking continuously, flooding the corridor hallway.", "severity": "medium"},
        {"text": "Frequent voltage fluctuations in {location} are damaging laptop chargers and electrical equipment.", "severity": "medium"},
        {"text": "Electric sparks observed from the main distribution panel near {location} accompanied by burning smell.", "severity": "critical", "safety": True},
        {"text": "RO water purifier filter in {location} has not been serviced for 6 months. Water tastes salty and metallic.", "severity": "medium"},
        {"text": "Water pressure on the top floor of {location} is practically zero. Only a trickle of water comes out.", "severity": "low"},
        {"text": "Main water pipe burst outside {location}, leading to thousands of liters of clean water wastage.", "severity": "high"},
        {"text": "Corridor tube lights outside room {room} are burnt out for 10 days. The walkway is completely pitch dark at night.", "severity": "medium"},
        {"text": "Switchboard in room {room} produced smoke when iron was plugged in. Sockets are scorched black.", "severity": "critical", "safety": True},
        {"text": "Overhead water tank in {location} is overflowing continuously for past 4 hours. Water overflowing onto stairs.", "severity": "medium"},
        {"text": "Geyser heating coil has burnt out in 3rd floor washroom of {location}. Only freezing cold water available.", "severity": "medium"},
        {"text": "Power cuts occur every day at exactly 8 PM during study hours without any prior notice from maintenance.", "severity": "medium"},
    ],
    "C03": [
        # Internet and Network
        {"text": "Wi-Fi router on {location} shows connected but with no internet access. DNS resolution fails repeatedly.", "severity": "medium"},
        {"text": "Campus Wi-Fi authentication portal (captive login) keeps timing out and dropping connection every 10 minutes.", "severity": "medium"},
        {"text": "Internet speed in {location} has dropped below 100 kbps, unable to download research papers or access portals.", "severity": "low"},
        {"text": "LAN port at desk in room {room} is dead. Cable tested and working fine elsewhere.", "severity": "low"},
        {"text": "College portal and intranet LMS are unreachable from student Wi-Fi network before assignment deadline.", "severity": "high"},
        {"text": "Wi-Fi access point in {location} has been completely switched off or dead since Saturday morning.", "severity": "medium"},
        {"text": "High packet loss and latency exceeding 800ms make it impossible to attend scheduled online placement interviews.", "severity": "high"},
        {"text": "Firewall is blocking essential academic domains including GitHub, IEEE Xplore, and Coursera on campus Wi-Fi.", "severity": "medium"},
        {"text": "Wi-Fi password reset request submitted through IT ticket #4819 has not been processed for over 5 working days.", "severity": "low"},
        {"text": "Hostel wing {floor} has zero Wi-Fi signal coverage. Signal does not penetrate through concrete walls.", "severity": "medium"},
        {"text": "Proxy server configuration for library e-resources fails with 502 Bad Gateway error.", "severity": "medium"},
        {"text": "Eduroam roaming network is not broadcasting SSID in {location}.", "severity": "low"},
        {"text": "Severe Wi-Fi bandwidth throttling during evening hours between 7 PM and 11 PM across all hostel blocks.", "severity": "medium"},
        {"text": "Ethernet switch in computer laboratory is rebooting every 15 minutes, interrupting practical programming tests.", "severity": "high"},
        {"text": "Network cable in research scholar lab was severed during garden trench digging work outside.", "severity": "medium"},
    ],
    "C04": [
        # Mess and Food
        {"text": "Found a dead cockroach inside the dal served during dinner at {location}. Severe hygiene violation.", "severity": "critical", "safety": True},
        {"text": "Food served at lunch today had a sour smell and stale taste. Several students complain of stomach upset.", "severity": "critical", "safety": True},
        {"text": "Rice served in the mess was half-cooked and chapatis were burnt black and rock hard.", "severity": "medium"},
        {"text": "Mess staff are handling cooked food, rotis, and salad with bare unwashed hands without hairnets or gloves.", "severity": "medium"},
        {"text": "Drinking water dispenser in mess hall has slimy green algae deposit around the dispensing nozzle.", "severity": "high", "safety": True},
        {"text": "Mess menu displayed on notice board is not followed. Special diet and paneer promised was missing.", "severity": "low"},
        {"text": "Food ran out completely 45 minutes before the scheduled dinner closing time, leaving over 50 students hungry.", "severity": "high"},
        {"text": "Plates and spoons provided at dinner had greasy oil film and visible dried gravy stains from previous meal.", "severity": "medium"},
        {"text": "Milk served at breakfast is heavily diluted with tap water and curd is excessively sour.", "severity": "low"},
        {"text": "Canteen vendor is overcharging above printed MRP for packaged biscuits and dairy products.", "severity": "low"},
        {"text": "Over 12 hostel residents fell violently ill with food poisoning after eating paneer curry at {location}.", "severity": "critical", "safety": True},
        {"text": "Mess contractor uses cheap sub-standard cooking oil causing throat irritation and acidity among students.", "severity": "medium"},
        {"text": "Fly infestation in the dining area of {location}. Swarms of flies landing directly on open food containers.", "severity": "medium"},
        {"text": "Mess rebate for 10 days of approved medical leave has not been credited in mess bill statement.", "severity": "low"},
        {"text": "Vegetarian and non-vegetarian food counters are using the same serving ladle and cooking pans.", "severity": "medium"},
    ],
    "C05": [
        # Academic and Examination
        {"text": "Clash in mid-term examination timetable: Two core branch subjects scheduled at exactly 10:00 AM on Monday.", "severity": "high"},
        {"text": "Course instructor has not shown graded answer sheets of Quiz 2 despite semester exams starting next week.", "severity": "medium"},
        {"text": "Attendance percentage on student ERP portal shows 68% whereas physical register attendance is 86%.", "severity": "high"},
        {"text": "End-semester exam hall ticket has incorrect elective subject printed, risking disqualification.", "severity": "high"},
        {"text": "Syllabus for Machine Learning course has only been 40% covered with just 2 weeks left before finals.", "severity": "medium"},
        {"text": "Re-evaluation result of previous semester applied 4 months ago has still not been declared by exam cell.", "severity": "medium"},
        {"text": "Elective subject allocation portal crashed during bidding and popular subjects were filled unfairly.", "severity": "medium"},
        {"text": "Internal assessment marks for practical lab entered as 0/30 due to teacher data entry error.", "severity": "high"},
        {"text": "Classroom lecture audio is inaudible beyond the third row because the collar microphone is broken.", "severity": "low"},
        {"text": "No faculty assigned yet for course code CS504 after the previous instructor went on medical leave.", "severity": "high"},
        {"text": "Make-up exam application submitted with hospital discharge certificate was rejected without explanation.", "severity": "medium"},
        {"text": "Transcript request for foreign university application is pending with exam branch for over 35 days.", "severity": "medium"},
        {"text": "Class test was conducted without mandatory 3 days prior intimation on department notice board.", "severity": "low"},
        {"text": "Question paper for Data Structures exam contained questions from unnotified out-of-syllabus topics.", "severity": "medium"},
        {"text": "Degree provisional certificate contains spelling mistake in student name matching passport records.", "severity": "medium"},
    ],
    "C06": [
        # Classroom and Laboratory
        {"text": "Digital oscilloscope and function generators in {location} are faulty and displaying distorted signals.", "severity": "medium"},
        {"text": "Air conditioning unit in {location} is broken; room temperature exceeds 38C during 3-hour afternoon lab.", "severity": "medium"},
        {"text": "Ceiling projector in lecture room displays blurred green tint, making lecture slides illegible.", "severity": "low"},
        {"text": "Fume hood in chemistry laboratory is not drawing exhaust properly; hazardous acid fumes accumulating in lab.", "severity": "critical", "safety": True},
        {"text": "Ten out of thirty desktop computers in {location} have corrupt OS installations and cannot boot.", "severity": "medium"},
        {"text": "Broken wooden benches in lecture hall have sharp exposed nails that tear clothing and scratch students.", "severity": "medium"},
        {"text": "Chemical reagents needed for Organic Chemistry practical experiment 5 are completely out of stock.", "severity": "medium"},
        {"text": "Water leakage in ceiling directly above the high-voltage electrical machines test bench in {location}.", "severity": "critical", "safety": True},
        {"text": "Whiteboard in classroom {room} is deeply stained and scratched; marker writing cannot be erased.", "severity": "low"},
        {"text": "Emergency fire extinguisher in chemical laboratory expired 2 years ago and has zero gauge pressure.", "severity": "critical", "safety": True},
        {"text": "Microscopes in biology lab have cracked objective lenses and mold growth on optical prisms.", "severity": "medium"},
        {"text": "Public address sound system in main auditorium screeches loudly with continuous feedback noise.", "severity": "low"},
        {"text": "Hydraulic test rig in mechanical laboratory has hydraulic oil leaking onto the student workstation floor.", "severity": "high", "safety": True},
        {"text": "Lack of adequate power sockets in seminar hall for students trying to run software on laptops.", "severity": "low"},
        {"text": "Classroom windows cannot be opened due to jammed iron frames causing suffocation when crowded.", "severity": "low"},
    ],
    "C07": [
        # Sanitation and Cleanliness
        {"text": "Common washrooms on floor {floor} of {location} have blocked drains with foul sewage overflowing onto floor.", "severity": "high"},
        {"text": "Trash cans outside {location} have not been emptied for 4 days; garbage is piling up on footpath.", "severity": "medium"},
        {"text": "Severe pest infestation: multiple rats spotted in hostel corridor and washroom pipes of {location}.", "severity": "medium"},
        {"text": "Liquid soap dispensers in all washrooms of academic block have been empty for over two weeks.", "severity": "low"},
        {"text": "Corridors and staircases of {location} are littered with plastic wrappers, mud, and construction debris.", "severity": "low"},
        {"text": "Stagnant wastewater pooling behind hostel building has become a breeding ground for dengue mosquitoes.", "severity": "high", "safety": True},
        {"text": "Washroom mirror fell off the wall and shattered into sharp glass pieces on the floor; not cleaned up.", "severity": "high", "safety": True},
        {"text": "Foul stench coming from the open drainage manhole near {location}. Cover is broken and left open.", "severity": "critical", "safety": True},
        {"text": "Hostel room dustbins are not being cleared by housekeeping staff despite daily cleaning charges.", "severity": "low"},
        {"text": "Sanitary napkin vending and disposal incinerator machines in girls hostel washroom are non-functional.", "severity": "medium"},
        {"text": "Drinking water fountain basin is clogged with tea leaves and spit marks; unhygienic to drink from.", "severity": "medium"},
        {"text": "Pigeon droppings accumulating on window sills and AC outdoor units of {location} causing breathing issues.", "severity": "low"},
        {"text": "Deep fungal mold stains covering the shower stall tiles and ceiling in {location}.", "severity": "medium"},
        {"text": "Sanitation sweepers are dumping collected dry leaves and plastic waste and burning it near hostel windows.", "severity": "high", "safety": True},
        {"text": "Urinals in ground floor washroom are permanently overflowing with standing urine due to clogged trap.", "severity": "high"},
    ],
    "C08": [
        # Campus Safety
        {"text": "Streetlights along the pathway between library and girls hostel are completely unlit creating pitch darkness.", "severity": "critical", "safety": True},
        {"text": "Pack of aggressive stray dogs near {location} bit a first-year student walking back from lab last night.", "severity": "critical", "safety": True},
        {"text": "Unidentified outsiders entered hostel premises past midnight without being checked by security guards.", "severity": "critical", "safety": True},
        {"text": "Bicycle lock was cut and bicycle stolen from designated cycle stand outside {location}.", "severity": "medium"},
        {"text": "Fire exit doors on 3rd floor of {location} are padlocked from outside, violating campus fire safety regulations.", "severity": "critical", "safety": True},
        {"text": "Female students reported repeated verbal catcalling and harassment by men on motorbikes near {location}.", "severity": "critical", "safety": True},
        {"text": "CCTV security camera covering the bicycle parking and hostel back gate is visibly disconnected.", "severity": "medium"},
        {"text": "Speeding delivery vehicles and cars inside campus pedestrian zones near main gate putting students at risk.", "severity": "high", "safety": True},
        {"text": "Smell of burning rubber and chemical smoke emerging from basement electrical control room near {location}.", "severity": "critical", "safety": True},
        {"text": "Suspicious person loitering near ground floor hostel windows taking photographs with phone.", "severity": "critical", "safety": True},
        {"text": "Emergency panic button at campus security kiosk is broken and display shows hardware error.", "severity": "high", "safety": True},
        {"text": "Security guard on duty at night post near {location} was found sleeping soundly while main gate was wide open.", "severity": "high"},
        {"text": "Heavy iron railing on the staircase landing of {location} is rusted through and shaking loose under hand pressure.", "severity": "critical", "safety": True},
        {"text": "Ragging incident: senior students forced freshers to perform humiliating tasks outside hostel block after hours.", "severity": "critical", "safety": True},
        {"text": "Broken glass bottles scattered across the basketball court posing injury hazard to players.", "severity": "medium", "safety": True},
    ],
    "C09": [
        # Transportation
        {"text": "Campus shuttle bus route #3 arrived 45 minutes late, causing students to miss morning 8:30 AM quiz.", "severity": "medium"},
        {"text": "Shuttle bus driver driving recklessly at high speed and braking abruptly with students standing in aisle.", "severity": "high", "safety": True},
        {"text": "Overcrowding in evening campus bus to railway station; more than 80 passengers crammed into 40-seater bus.", "severity": "medium"},
        {"text": "Designated student two-wheeler parking lot is completely full by 9 AM due to staff cars parked illegally.", "severity": "low"},
        {"text": "Battery-operated campus e-rickshaw service has been suspended without notification or replacement schedule.", "severity": "low"},
        {"text": "Bus pass renewal counter at transport office operates only for 1 hour a day with massive chaotic queues.", "severity": "low"},
        {"text": "Campus bus #5 exhaust pipe emits thick black suffocating smoke directly into passenger window seats.", "severity": "medium"},
        {"text": "Footboard of college bus #2 is severely rusted and cracked, flexing alarmingly when boarding.", "severity": "high", "safety": True},
        {"text": "No bus service available on Saturday for students attending mandatory remedial classes and weekend labs.", "severity": "medium"},
        {"text": "Security guard at vehicle gate refuses helmet-wearing students entry unless they show physical paper pass.", "severity": "low"},
        {"text": "Bicycle puncture repair shop on campus has been closed for 2 weeks leaving no alternatives for flat tires.", "severity": "low"},
        {"text": "Speed breakers installed on main academic avenue are dangerously steep and unpainted, scraping bike undercarriages.", "severity": "medium", "safety": True},
        {"text": "Transport coordinator does not answer emergency helpline phone when bus breaks down on city highway.", "severity": "medium"},
        {"text": "Night shuttle van from metro station to campus gate discontinued without prior notice to hostelers.", "severity": "high"},
        {"text": "Student parked motorcycle received deep key scratches while parked in official campus lot with no guard.", "severity": "low"},
    ],
    "C10": [
        # Administrative Services
        {"text": "Scholarship disbursement for national merit portal pending with college nodal officer for 3 months.", "severity": "high"},
        {"text": "Accounts section refuses to accept online UPI/NEFT transaction receipt for semester fee clearance.", "severity": "medium"},
        {"text": "Administrative staff in academic section behaved rudely and shouted at student inquiring about bonafide letter.", "severity": "medium"},
        {"text": "Lost ID card replacement fee paid 3 weeks ago; identity card has still not been printed by student section.", "severity": "low"},
        {"text": "No-dues clearance portal for graduating batch has multiple bogus pending library dues of Rs. 0.", "severity": "medium"},
        {"text": "Bonafide certificate required for passport renewal appointment is delayed beyond the committed 48-hour SLA.", "severity": "medium"},
        {"text": "Hostel caution money refund after room vacation has not been processed into bank account after 6 months.", "severity": "high"},
        {"text": "Medical insurance card promised during admission has not been issued to any first-year students.", "severity": "medium"},
        {"text": "Fee receipt download button on student online portal gives server 500 error since fee deadline.", "severity": "medium"},
        {"text": "Administrative counter 4 closes 30 minutes before official working hours every day with no substitute staff.", "severity": "low"},
        {"text": "Grade card issued by administration has father's name spelled incorrectly despite correct proof submitted.", "severity": "low"},
        {"text": "Railway concession form counter operates only on Tuesdays between 2 PM and 3 PM resulting in missed trains.", "severity": "low"},
        {"text": "Application for college character certificate submitted on 5th of last month is untraceable in dispatch.", "severity": "medium"},
        {"text": "Dean of Student Affairs office has not scheduled a meeting for student council grievances in two months.", "severity": "low"},
        {"text": "Tuition fee structure document on college website lists outdated fee figures leading to bank loan disputes.", "severity": "medium"},
    ],
    "C11": [
        # Other / Unclassified & Ambiguous
        {"text": "General inquiry: What is the procedure for booking the open air amphitheater for club cultural rehearsal?", "severity": "low"},
        {"text": "Lost black leather wallet containing college ID and metro card near cafeteria lawn yesterday afternoon.", "severity": "low"},
        {"text": "Found a set of motorcycle keys on bench outside library. Deposited with security desk.", "severity": "low"},
        {"text": "The stray cat in the courtyard seems severely injured and unable to walk. Needs veterinary assistance.", "severity": "medium"},
        {"text": "Very poor management and lack of communication regarding the schedule of upcoming annual fest events.", "severity": "low"},
        {"text": "Ambiguous complaint: Everything in our department is chaotic and nobody takes responsibility for anything.", "severity": "low"},
        {"text": "Request for installing more green recycling bins across the lawn area to encourage environmental sustainability.", "severity": "low"},
        {"text": "Campus bookstore does not keep required engineering textbooks or scientific calculator batteries.", "severity": "low"},
        {"text": "Construction noise from new building site starts at 5:30 AM disrupting morning sleep and meditation.", "severity": "low"},
        {"text": "Bank ATM installed inside campus near shopping complex has been out of cash for past ten days.", "severity": "low"},
        {"text": "Gym equipment weights are missing and cable pulley on chest press machine has snapped.", "severity": "medium"},
        {"text": "Unpleasant burning smell in air around 11 PM every night coming from neighboring village boundary.", "severity": "medium"},
        {"text": "Postal courier delivery packages are left unattended outside security cabin without signature or tracking log.", "severity": "low"},
        {"text": "Posters for student society elections are being pasted over department bulletin boards and defacing walls.", "severity": "low"},
        {"text": "The campus clock tower bell chime is out of sync by 14 minutes and rings at odd times.", "severity": "low"},
    ],
}

# Cross-domain ambiguous complaints to test multi-topic handling (routed to primary or C11)
AMBIGUOUS_COMPLAINTS = [
    {
        "text": "The mess drinking water caused stomach infection and the water cooler on floor 2 has the same foul smell.",
        "primary": "C04", "secondary": "C02",
    },
    {
        "text": "Electrical short circuit in computer science lab 3 caused smoke and ruined the server equipment during practical exam.",
        "primary": "C06", "secondary": "C02", "safety": True,
    },
    {
        "text": "Campus bus #4 broke down on dark highway at night with no streetlights and girls hostel students aboard.",
        "primary": "C09", "secondary": "C08", "safety": True,
    },
    {
        "text": "Exam hall temperature was 42C because air conditioner was broken and drinking water was completely empty.",
        "primary": "C06", "secondary": "C05",
    },
    {
        "text": "Hostel warden was rude and threatened to cancel our semester exam admit cards when we reported broken washrooms.",
        "primary": "C01", "secondary": "C10",
    },
    {
        "text": "Garbage dump near mess hall kitchen is attracting stray dogs that growl aggressively at students going for dinner.",
        "primary": "C07", "secondary": "C08", "safety": True,
    },
    {
        "text": "Wi-Fi in library reading room is down so cannot verify attendance percentage before exam eligibility deadline.",
        "primary": "C03", "secondary": "C05",
    },
    {
        "text": "Streetlight pole outside hostel broke and live wire is hanging into a pool of overflowing sewage water.",
        "primary": "C08", "secondary": "C02", "safety": True,
    },
]

# Modifiers to produce realistic variations in length and student tone
OPENERS = [
    "",
    "Kindly look into this issue: ",
    "Writing to urgently report that ",
    "This is the third time I am reporting this. ",
    "Respected Authorities, please note that ",
    "Frustrated to report that ",
    "Attention Maintenance Team: ",
    "Severe inconvenience being faced: ",
    "Wanted to bring to your immediate notice that ",
    "I am a resident student and ",
    "Urgent grievance: ",
    "Please resolve this as soon as possible. ",
]

CLOSERS = [
    "",
    " Please fix this on priority.",
    " Extremely disappointing state of affairs.",
    " Kindly take necessary action immediately.",
    " Expecting a prompt resolution from the concerned department.",
    " This is severely affecting our daily studies and health.",
    " Hope the administration takes this seriously this time.",
    " Thank you.",
    " Looking forward to a quick fix.",
    " Several students are affected by this problem.",
]


def apply_realistic_typos(text: str, rng: random.Random, typo_prob: float = 0.12) -> str:
    """Inject natural student spelling/typo variations probabilistically."""
    words = text.split()
    modified_words = []
    for word in words:
        clean = word.lower().strip(",.?!:;")
        if clean in TYPO_MAP and rng.random() < typo_prob:
            sub = rng.choice(TYPO_MAP[clean])
            # Preserve punctuation if any
            if word[-1] in ",.?!:;":
                sub += word[-1]
            modified_words.append(sub)
        else:
            modified_words.append(word)
    return " ".join(modified_words)


def generate_synthetic_dataset(
    target_count_per_category: int = 110,
    random_seed: int = 42,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """Generate a diverse, reproducible synthetic college complaints dataset.

    Args:
        target_count_per_category: Minimum examples per category (default: 110).
        random_seed: Random state for reproducibility (default: 42).
        output_path: If provided, saves CSV to this path.

    Returns:
        pd.DataFrame containing generated complaints with schema:
            complaint_id, complaint_text, category, category_name, location,
            created_at, status, priority_label, incident_group_id, data_source
    """
    rng = random.Random(random_seed)

    records: list[dict[str, Any]] = []
    seen_texts: set[str] = set()

    start_date = datetime(2026, 1, 10, 8, 0, 0)
    end_date = datetime(2026, 10, 25, 20, 0, 0)
    date_range_seconds = int((end_date - start_date).total_seconds())

    # Map category codes to names
    category_names = {
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

    # Incident counter for duplicate/related complaint clusters
    incident_counter = 1

    for cat_code, cat_name in category_names.items():
        base_pool = CATEGORY_COMPLAINTS.get(cat_code, [])
        count_for_cat = 0

        # Create 3-5 distinct incident groups per category with 2-3 reports each
        # (models real campus duplicate complaints where multiple students report the same event)
        num_incident_groups = rng.randint(3, 5)
        for _ in range(num_incident_groups):
            incident_id = f"INC-{cat_code}-{incident_counter:03d}"
            incident_counter += 1
            inc_base = rng.choice(base_pool)
            inc_loc = rng.choice(LOCATIONS)
            inc_base_time = start_date + timedelta(seconds=rng.randint(0, date_range_seconds))

            # 2 to 3 related reports of this incident
            cluster_size = rng.randint(2, 3)
            for member_idx in range(cluster_size):
                room_no = f"{rng.randint(1, 4)}{rng.randint(0, 3)}{rng.randint(1, 9)}"
                floor_no = f"{rng.choice(['ground', '1st', '2nd', '3rd', '4th'])}"

                # Format text with variations
                text_core = inc_base["text"].format(room=room_no, floor=floor_no, location=inc_loc)
                if member_idx == 0:
                    text = f"{rng.choice(OPENERS)}{text_core}{rng.choice(CLOSERS)}".strip()
                elif member_idx == 1:
                    text = f"Regarding {inc_loc}: {text_core.lower()} Still not resolved.{rng.choice(CLOSERS)}".strip()
                else:
                    text = f"{text_core} Many students in {inc_loc} are facing this.{rng.choice(CLOSERS)}".strip()

                text = apply_realistic_typos(text, rng)
                if text in seen_texts:
                    text += f" (report ref #{rng.randint(100, 999)})"
                seen_texts.add(text)

                # Small time delta between duplicate reports (e.g., within 2-48 hours)
                member_time = inc_base_time + timedelta(hours=rng.randint(1, 48))

                priority = "critical" if inc_base.get("safety") else rng.choice(["high", "medium"])
                status = rng.choice(["submitted", "in_progress", "resolved", "pending_review"])

                records.append({
                    "complaint_id": f"SYN-{len(records) + 1:05d}",
                    "complaint_text": text,
                    "category": cat_code,
                    "category_name": cat_name,
                    "location": inc_loc,
                    "created_at": member_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": status,
                    "priority_label": priority,
                    "incident_group_id": incident_id,
                    "data_source": "synthetic",
                })
                count_for_cat += 1

        # Now generate the remaining individual complaints for this category
        while count_for_cat < target_count_per_category:
            base_item = rng.choice(base_pool)
            room_no = f"{rng.randint(1, 4)}{rng.randint(0, 3)}{rng.randint(1, 9)}"
            floor_no = f"{rng.choice(['ground', '1st', '2nd', '3rd', '4th'])}"
            loc = rng.choice(LOCATIONS)

            text_core = base_item["text"].format(room=room_no, floor=floor_no, location=loc)

            # Generate varying lengths and compositions
            roll = rng.random()
            if roll < 0.20:
                # Very short complaint
                text = text_core
            elif roll < 0.70:
                # Standard complaint with opener or closer
                opener = rng.choice(OPENERS)
                closer = rng.choice(CLOSERS)
                text = f"{opener}{text_core}{closer}".strip()
            else:
                # Detailed long complaint with context
                detail = rng.choice([
                    f" This has been happening repeatedly since last {rng.choice(['Monday', 'Wednesday', 'Friday'])}.",
                    f" We informed the caretaker in person yesterday but no technician turned up.",
                    f" Mid-semester exams are ongoing and this disturbance is making it very difficult to concentrate.",
                    f" When approached, staff told us that spare parts have not been sanctioned yet.",
                    f" Several students residing in this wing have signed a joint complaint about this issue.",
                ])
                text = f"{rng.choice(OPENERS)}{text_core}{detail}{rng.choice(CLOSERS)}".strip()

            text = apply_realistic_typos(text, rng)

            # Ensure text uniqueness
            if text in seen_texts:
                suffix = f" Location details: {loc}, room {room_no}."
                text += suffix
                if text in seen_texts:
                    text += f" [Ticket ref #{rng.randint(1000, 9999)}]"

            seen_texts.add(text)

            complaint_time = start_date + timedelta(seconds=rng.randint(0, date_range_seconds))

            if base_item.get("safety"):
                priority = "critical"
            else:
                priority = base_item.get("severity", rng.choice(["medium", "low"]))

            status = rng.choice(["submitted", "in_progress", "resolved", "pending_review"])

            records.append({
                "complaint_id": f"SYN-{len(records) + 1:05d}",
                "complaint_text": text,
                "category": cat_code,
                "category_name": cat_name,
                "location": loc,
                "created_at": complaint_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": status,
                "priority_label": priority,
                "incident_group_id": "",  # Standalone complaint
                "data_source": "synthetic",
            })
            count_for_cat += 1

    # Add ambiguous cross-domain complaints into the mix
    for amb in AMBIGUOUS_COMPLAINTS:
        text = amb["text"]
        cat_code = amb["primary"]
        cat_name = category_names[cat_code]
        loc = rng.choice(LOCATIONS)
        c_time = start_date + timedelta(seconds=rng.randint(0, date_range_seconds))
        priority = "critical" if amb.get("safety") else "high"

        if text not in seen_texts:
            seen_texts.add(text)
            records.append({
                "complaint_id": f"SYN-{len(records) + 1:05d}",
                "complaint_text": text,
                "category": cat_code,
                "category_name": cat_name,
                "location": loc,
                "created_at": c_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "submitted",
                "priority_label": priority,
                "incident_group_id": "",
                "data_source": "synthetic",
            })

    # Shuffle the dataset reproducibly so categories are well mixed
    rng.shuffle(records)

    # Re-assign deterministic IDs
    for idx, r in enumerate(records, start=1):
        r["complaint_id"] = f"SYN-{idx:05d}"

    df = pd.DataFrame(records)
    logger.info(
        "Generated %d synthetic records across %d categories (seed=%d)",
        len(df), df["category"].nunique(), random_seed,
    )

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False, encoding="utf-8")
        logger.info("Saved synthetic dataset to %s", out)

    return df


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="Generate synthetic college complaint dataset.")
    parser.add_argument("--count-per-cat", type=int, default=115, help="Target count per category (min 100).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--output", type=str, default="data/raw/college_complaints_synthetic.csv", help="Output CSV path.")
    args = parser.parse_args()

    generate_synthetic_dataset(
        target_count_per_category=args.count_per_cat,
        random_seed=args.seed,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
