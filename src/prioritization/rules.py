"""
src/prioritization/rules.py
----------------------------
Rules-based complaint priority assessment and SLA engine for Module C.

Approved Priority Formula:
  P_base = (0.35 * severity) + (0.25 * safety_risk) + (0.20 * affected_population) + (0.10 * waiting_time) + (0.10 * recurrence)

Where each factor is normalized to [0, 100]:
  - severity: language severity cues (0-100)
  - safety_risk: detection of hazardous risks (fire, electrical, structural, physical harm) (0-100)
  - affected_population: estimated scale of impact (0-100). Default is 25 (individual/room), not 0.
  - waiting_time: min(100, (elapsed_hours / 72.0) * 100). Future timestamps clamped to 0.
  - recurrence: min(100, (recurrence_count / 5.0) * 100).

Approved Priority Bands:
  - CRITICAL: Safety override (verified critical safety hazard) OR P_base >= 85 with safety risk. Always requires immediate human review.
  - HIGH: P_base >= 75
  - MEDIUM: 45 <= P_base < 75
  - LOW: P_base < 45

Ethical & Auditing Mandates:
  - A keyword match flags potential risk for urgent human assessment; it is NOT definitive proof of emergency.
  - Clear distinction between numerical score, safety override, suggested priority, and final staff priority.
  - Full audit trail for authorized staff overrides.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PriorityLevel(str, Enum):
    """Categorical urgency bands for complaint resolution."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"  # Legacy alias preserved


# Safety keywords representing acute hazards
SAFETY_KEYWORDS: list[str] = [
    "fire", "injury", "injured", "assault", "collapse",
    "flood", "gas leak", "medical emergency", "unconscious",
    "bleeding", "attack", "threat", "harassment", "emergency",
    "ambulance", "police", "evacuation", "dangerous", "unsafe",
    "electric shock", "electrocuted", "smoke", "burning",
    "live wire", "structural damage", "short circuit",
    "ragging", "ragged", "sharp glass", "open drainage", "manhole",
    "food poisoning", "algae", "outsiders", "trespass", "speeding",
    "catcalling", "stalking", "fell off", "shattered", "high-voltage",
    "high voltage", "hazardous", "fumes", "acid", "loitering",
    "suspicious person", "dog bite", "bit a", "bitten", "cockroach",
    "trapped", "fell down", "oil leak", "oil leaking",
]

_SAFETY_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(kw) for kw in SAFETY_KEYWORDS) + r')\b',
    flags=re.IGNORECASE,
)


@dataclass
class StaffOverride:
    """Audit record when an authorized staff member overrides system priority."""
    staff_id: str
    original_priority: PriorityLevel
    override_priority: PriorityLevel
    reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "staff_id": self.staff_id,
            "original_priority": self.original_priority.value,
            "override_priority": self.override_priority.value,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PriorityResult:
    """Comprehensive output of the priority assessment engine."""
    score: float                              # 0.0 - 100.0 composite base score
    suggested_priority: PriorityLevel         # Model/rule recommended band
    final_priority: PriorityLevel             # Active band (can be overridden by staff)
    safety_flag: bool                         # True if safety keywords detected
    safety_override: bool                     # True if policy safety override escalated to CRITICAL
    needs_human_review: bool                  # True if human review is required
    triggered_safety_keywords: list[str] = field(default_factory=list)
    signals: dict[str, float] = field(default_factory=dict)
    explanation: str = ""
    staff_override: StaffOverride | None = None

    @property
    def priority_level(self) -> PriorityLevel:
        """Backward-compatible accessor for existing callers."""
        return self.final_priority

    def apply_override(
        self,
        staff_id: str,
        new_priority: PriorityLevel,
        reason: str,
    ) -> None:
        """Record an authorized human staff priority adjustment with audit trail."""
        if not reason or not reason.strip():
            raise ValueError("A clear reason must be provided for all staff priority overrides.")

        override_record = StaffOverride(
            staff_id=staff_id,
            original_priority=self.final_priority,
            override_priority=new_priority,
            reason=reason.strip(),
        )
        self.staff_override = override_record
        self.final_priority = new_priority
        logger.info(
            "Staff override applied by %s: %s -> %s (Reason: %s)",
            staff_id, override_record.original_priority.value, new_priority.value, reason
        )

    def __repr__(self) -> str:
        override_note = " [STAFF OVERRIDDEN]" if self.staff_override else ""
        safety_note = " [SAFETY OVERRIDE]" if self.safety_override else ""
        return (
            f"PriorityResult(priority={self.final_priority.value}, "
            f"score={self.score:.1f}{safety_note}{override_note})"
        )


# ---------------------------------------------------------------------------
# Signal Extractors (Outputs normalized to 0.0 - 100.0)
# ---------------------------------------------------------------------------

def score_safety_keywords(text: str) -> tuple[bool, list[str]]:
    """Detect safety-critical hazard terminology in complaint text."""
    if not isinstance(text, str) or not text.strip():
        return False, []
    matches = _SAFETY_PATTERN.findall(text)
    unique_matches = sorted(list(set(m.lower() for m in matches)))
    return len(unique_matches) > 0, unique_matches


def score_severity_language(text: str) -> float:
    """Estimate textual severity on 0-100 scale from language cues."""
    if not isinstance(text, str) or not text.strip():
        return 0.0

    HIGH_SEVERITY_TERMS = [
        "completely", "totally", "entire", "all", "everyone",
        "no water", "no electricity", "not working at all",
        "days", "weeks", "since yesterday", "since morning",
        "unbearable", "intolerable", "disgusting", "dangerous",
        "broken", "collapsed", "flooded", "overflowing", "severe",
        "urgent", "immediately", "hazard", "risk", "leaking",
        "leak", "outage", "disruption", "unusable", "malfunctioning",
        "contaminated", "dirty", "foul", "muddy", "spoiled",
    ]
    text_lower = text.lower()
    matches = sum(1 for term in HIGH_SEVERITY_TERMS if term in text_lower)
    # 3 or more matches saturates to 100.0
    return min(matches / 3.0, 1.0) * 100.0


def score_affected_estimate(text: str) -> float:
    """Estimate affected population impact on 0-100 scale.

    Mandate: Missing or unspecified affected population must NOT default to 0.
    Default baseline is 25.0 (individual/single-room issue).
    """
    if not isinstance(text, str) or not text.strip():
        return 25.0  # Neutral individual default

    CAMPUS_WIDE_TERMS = ["entire campus", "all hostels", "university wide", "every department"]
    BUILDING_WIDE_TERMS = ["whole block", "entire building", "whole floor", "entire hostel", "all students", "all rooms", "everyone"]
    MULTI_PERSON_TERMS = ["several students", "many students", "classmates", "our room", "all of us"]

    text_lower = text.lower()
    if any(term in text_lower for term in CAMPUS_WIDE_TERMS):
        return 100.0
    if any(term in text_lower for term in BUILDING_WIDE_TERMS):
        return 75.0
    if any(term in text_lower for term in MULTI_PERSON_TERMS):
        return 50.0

    return 25.0  # Default individual/room baseline


def score_waiting_time(
    created_at: datetime | None,
    current_time: datetime | None = None,
) -> float:
    """Calculate waiting time urgency on 0-100 scale.

    Formula: min(100.0, max(0.0, (elapsed_hours / 72.0) * 100.0))
    Future timestamps are clamped to 0.0. Missing timestamp defaults to 25.0.
    """
    if created_at is None:
        return 25.0  # Neutral assumption when submission time is unknown

    now = current_time or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    elapsed_seconds = (now - created_at).total_seconds()
    if elapsed_seconds <= 0:
        return 0.0  # Just submitted or future timestamp

    elapsed_hours = elapsed_seconds / 3600.0
    return min(100.0, max(0.0, (elapsed_hours / 72.0) * 100.0))


def score_recurrence(recurrence_count: int) -> float:
    """Score recurrence urgency on 0-100 scale.

    Formula: min(100.0, max(0.0, (count / 5.0) * 100.0))
    """
    if not isinstance(recurrence_count, (int, float)) or recurrence_count < 0:
        recurrence_count = 0
    return min(100.0, max(0.0, (float(recurrence_count) / 5.0) * 100.0))


# ---------------------------------------------------------------------------
# Approved Formula & Thresholds
# ---------------------------------------------------------------------------

APPROVED_WEIGHTS = {
    "severity": 0.35,
    "safety_risk": 0.25,
    "affected_population": 0.20,
    "waiting_time": 0.10,
    "recurrence": 0.10,
}

APPROVED_THRESHOLDS = {
    "high": 75.0,
    "medium": 45.0,
}


def assess_priority(
    complaint_text: str,
    *,
    created_at: datetime | None = None,
    recurrence_count: int = 0,
    current_time: datetime | None = None,
    verified_safety_hazard: bool | None = None,
    weights: dict[str, float] | None = None,
) -> PriorityResult:
    """Assess complaint priority using the approved transparent rules engine.

    P_base = 0.35 * severity + 0.25 * safety_risk + 0.20 * affected_population + 0.10 * waiting_time + 0.10 * recurrence

    Args:
        complaint_text: Raw or preprocessed complaint text.
        created_at: Submission timestamp.
        recurrence_count: Historical recurrence count.
        current_time: Current timestamp (useful for deterministic tests).
        verified_safety_hazard: Explicit flag if confirmed hazard exists.
        weights: Optional dictionary overriding component weights.

    Returns:
        PriorityResult with base score, suggested priority, safety flags, and audit hooks.
    """
    w = weights or APPROVED_WEIGHTS

    # 1. Compute individual factor signals (0 - 100)
    has_safety_kw, safety_kw_list = score_safety_keywords(complaint_text)
    severity_val = score_severity_language(complaint_text)
    affected_val = score_affected_estimate(complaint_text)
    waiting_val = score_waiting_time(created_at, current_time=current_time)
    recurrence_val = score_recurrence(recurrence_count)

    # Safety risk score: keyword match contributes 60-100 depending on keyword count
    if has_safety_kw:
        safety_risk_val = min(100.0, 60.0 + len(safety_kw_list) * 20.0)
    else:
        safety_risk_val = 0.0

    signals = {
        "severity": severity_val,
        "safety_risk": safety_risk_val,
        "affected_population": affected_val,
        "waiting_time": waiting_val,
        "recurrence": recurrence_val,
    }

    # 2. Compute canonical weighted base score P_base
    p_base = (
        w["severity"] * severity_val
        + w["safety_risk"] * safety_risk_val
        + w["affected_population"] * affected_val
        + w["waiting_time"] * waiting_val
        + w["recurrence"] * recurrence_val
    )
    p_base = float(np.clip(p_base, 0.0, 100.0)) if "np" in globals() else float(min(100.0, max(0.0, p_base)))

    # 3. Policy Safety Override Check
    # If safety keywords are present OR verified_safety_hazard is True
    safety_override = bool(has_safety_kw or verified_safety_hazard)
    needs_review = bool(safety_override or p_base >= APPROVED_THRESHOLDS["high"])

    if safety_override:
        suggested_band = PriorityLevel.CRITICAL
        kw_note = f"keywords: {safety_kw_list}" if has_safety_kw else "verified safety hazard flag"
        explanation = (
            f"Safety override triggered by {kw_note}. "
            f"Escalated to CRITICAL with mandatory human staff review. "
            f"Calculated base score={p_base:.1f}."
        )
    elif p_base >= APPROVED_THRESHOLDS["high"]:
        suggested_band = PriorityLevel.HIGH
        explanation = (
            f"HIGH priority (score={p_base:.1f} >= 75.0). "
            f"Signals: severity={severity_val:.0f}, affected={affected_val:.0f}, "
            f"waiting={waiting_val:.0f}, recurrence={recurrence_val:.0f}."
        )
    elif p_base >= APPROVED_THRESHOLDS["medium"]:
        suggested_band = PriorityLevel.MEDIUM
        explanation = (
            f"MEDIUM priority (45.0 <= score={p_base:.1f} < 75.0). "
            f"Standard resolution SLA."
        )
    else:
        suggested_band = PriorityLevel.LOW
        explanation = (
            f"LOW priority (score={p_base:.1f} < 45.0). "
            f"Minor or cosmetic issue."
        )

    return PriorityResult(
        score=round(p_base, 2),
        suggested_priority=suggested_band,
        final_priority=suggested_band,
        safety_flag=has_safety_kw,
        safety_override=safety_override,
        needs_human_review=needs_review,
        triggered_safety_keywords=safety_kw_list,
        signals=signals,
        explanation=explanation,
        staff_override=None,
    )
