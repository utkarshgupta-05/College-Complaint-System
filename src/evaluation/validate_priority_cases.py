"""
src/evaluation/validate_priority_cases.py
-------------------------------------------
Validation of priority rules, overrides, safety triggers, and edge cases.
"""

from datetime import datetime, timezone, timedelta
import pandas as pd
from src.prioritization.rules import assess_priority, PriorityLevel


def run_priority_validation() -> pd.DataFrame:
    test_cases = [
        {
            "id": "TC-01",
            "scenario": "Acute physical safety hazard (Fire/Smoke)",
            "text": "Fire and smoke coming out of electrical meter room in Academic Block B. Immediate evacuation needed!",
            "created_at": datetime.now(timezone.utc),
            "recurrence": 0,
            "expected_band": "CRITICAL",
        },
        {
            "id": "TC-02",
            "scenario": "Harassment / Ragging emergency",
            "text": "Seniors are ragging first-year students in Hostel D common room. Urgent intervention required.",
            "created_at": datetime.now(timezone.utc),
            "recurrence": 0,
            "expected_band": "CRITICAL",
        },
        {
            "id": "TC-03",
            "scenario": "Structural collapse hazard",
            "text": "Plaster and concrete chunks fell off the ceiling in Classroom 302. Unsafe for classes.",
            "created_at": datetime.now(timezone.utc),
            "recurrence": 0,
            "expected_band": "CRITICAL",
        },
        {
            "id": "TC-04",
            "scenario": "Widespread utility failure (Building-wide outage)",
            "text": "There is completely no water in entire hostel block for the past two days. Disgusting and unbearable condition for all students.",
            "created_at": datetime.now(timezone.utc) - timedelta(hours=48),
            "recurrence": 0,
            "expected_band": "HIGH",
        },
        {
            "id": "TC-05",
            "scenario": "Minor individual cosmetic issue",
            "text": "The room fan makes a mild clicking noise when set to highest speed. Not urgent.",
            "created_at": datetime.now(timezone.utc),
            "recurrence": 0,
            "expected_band": "LOW",
        },
        {
            "id": "TC-06",
            "scenario": "Recurrence escalation (5 prior reports)",
            "text": "The room fan makes a mild clicking noise when set to highest speed.",
            "created_at": datetime.now(timezone.utc),
            "recurrence": 5,
            "expected_band": "LOW -> Escalated (+10 score points)",
        },
        {
            "id": "TC-07",
            "scenario": "Waiting time aging escalation (>72h)",
            "text": "Study table chair has a wobbly leg in room 204.",
            "created_at": datetime.now(timezone.utc) - timedelta(hours=80),
            "recurrence": 0,
            "expected_band": "LOW -> Escalated (+10 score points)",
        },
        {
            "id": "TC-08",
            "scenario": "Authorized staff priority adjustment",
            "text": "Slight flicker in library corridor lamp.",
            "created_at": datetime.now(timezone.utc),
            "recurrence": 0,
            "expected_band": "LOW -> HIGH (Staff Override)",
        },
    ]

    records = []
    for tc in test_cases:
        res = assess_priority(
            tc["text"],
            created_at=tc["created_at"],
            recurrence_count=tc["recurrence"],
        )
        staff_note = "None"
        if tc["id"] == "TC-08":
            res.apply_override(
                staff_id="STAFF-ADM-01",
                new_priority=PriorityLevel.HIGH,
                reason="VIP inspection tomorrow morning requires all corridor lights operational.",
            )
            staff_note = "Overridden to HIGH"

        records.append({
            "test_id": tc["id"],
            "scenario": tc["scenario"],
            "base_score": res.score,
            "suggested_band": res.suggested_priority.value,
            "final_band": res.final_priority.value,
            "safety_override": res.safety_override,
            "mandatory_review": res.needs_human_review,
            "keywords": ", ".join(res.triggered_safety_keywords) if res.triggered_safety_keywords else "None",
            "staff_action": staff_note,
        })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    df = run_priority_validation()
    print(df.to_string(index=False))

