"""
tests/test_priority_rules.py
------------------------------
Unit and integration tests for the rules-based priority assessment engine (Module C).

Verifies:
  - Canonical formula: P_base = 0.35*sev + 0.25*safe + 0.20*aff + 0.10*wait + 0.10*recur (0-100 scale)
  - Priority bands: CRITICAL (safety override), HIGH (>=75), MEDIUM (45-74.9), LOW (<45)
  - Waiting time calculation (elapsed / 72 * 100) and future timestamp clamping
  - Missing affected population non-zero neutral handling (default = 25)
  - Safety hazard detection and escalation with mandatory human review
  - Staff override logging and audit trail
  - Robust handling of edge cases (empty strings, special chars, invalid counts)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.prioritization.rules import (
    APPROVED_THRESHOLDS,
    APPROVED_WEIGHTS,
    PriorityLevel,
    PriorityResult,
    StaffOverride,
    assess_priority,
    score_affected_estimate,
    score_recurrence,
    score_safety_keywords,
    score_severity_language,
    score_waiting_time,
)


# ---------------------------------------------------------------------------
# Safety keyword detection tests
# ---------------------------------------------------------------------------

class TestSafetyKeywordDetection:
    def test_detects_fire(self):
        flag, keywords = score_safety_keywords("There is a fire in the hostel kitchen.")
        assert flag is True
        assert "fire" in keywords

    def test_detects_injury(self):
        flag, keywords = score_safety_keywords("A student was injured near the gate.")
        assert flag is True
        assert "injured" in keywords

    def test_no_safety_keywords(self):
        flag, keywords = score_safety_keywords("The mess food is very bad today.")
        assert flag is False
        assert keywords == []

    def test_case_insensitive(self):
        flag, keywords = score_safety_keywords("FIRE in Block A right now!")
        assert flag is True
        assert "fire" in keywords

    def test_empty_string(self):
        flag, keywords = score_safety_keywords("")
        assert flag is False
        assert keywords == []

    def test_non_string_input(self):
        flag, keywords = score_safety_keywords(None)  # type: ignore
        assert flag is False
        assert keywords == []


# ---------------------------------------------------------------------------
# Signal Scorers Tests (0 - 100 scale)
# ---------------------------------------------------------------------------

class TestSignalScorers:
    def test_severity_language_scoring(self):
        assert score_severity_language("") == 0.0
        # 1 cue -> 33.3
        s1 = score_severity_language("The tap is broken.")
        assert round(s1, 1) == 33.3
        # 3 cues -> 100.0
        s3 = score_severity_language("No water since yesterday, completely broken and intolerable!")
        assert s3 == 100.0

    def test_missing_affected_population_is_non_zero_neutral(self):
        """MANDATE: Missing or unspecified affected population must NOT default to 0."""
        score_missing = score_affected_estimate("Single chair in my room is squeaky.")
        assert score_missing == 25.0  # Neutral individual/room baseline
        assert score_missing > 0.0

        # Specific wide-impact language scales up
        assert score_affected_estimate("Many students in our wing are facing this.") == 50.0
        assert score_affected_estimate("The entire hostel has no water.") == 75.0
        assert score_affected_estimate("University wide internet blackout across entire campus.") == 100.0

    def test_waiting_time_calculation_and_future_timestamp(self):
        fixed_now = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)

        # 0 hours elapsed -> 0.0
        t0 = fixed_now
        assert score_waiting_time(t0, current_time=fixed_now) == 0.0

        # 36 hours elapsed (half of 72h SLA) -> 50.0
        t36 = fixed_now - timedelta(hours=36)
        assert round(score_waiting_time(t36, current_time=fixed_now), 1) == 50.0

        # 72 hours elapsed (100% of SLA) -> 100.0
        t72 = fixed_now - timedelta(hours=72)
        assert score_waiting_time(t72, current_time=fixed_now) == 100.0

        # 100 hours elapsed -> capped at 100.0
        t100 = fixed_now - timedelta(hours=100)
        assert score_waiting_time(t100, current_time=fixed_now) == 100.0

        # Future timestamp -> clamped to 0.0
        t_future = fixed_now + timedelta(hours=5)
        assert score_waiting_time(t_future, current_time=fixed_now) == 0.0

        # Missing timestamp -> neutral 25.0
        assert score_waiting_time(None) == 25.0

    def test_recurrence_scoring(self):
        assert score_recurrence(0) == 0.0
        assert score_recurrence(1) == 20.0
        assert score_recurrence(5) == 100.0
        assert score_recurrence(10) == 100.0  # capped
        assert score_recurrence(-3) == 0.0    # negative clamped


# ---------------------------------------------------------------------------
# Priority Assessment Engine Tests
# ---------------------------------------------------------------------------

class TestAssessPriority:
    def test_safety_complaint_escalates_to_critical_and_review(self):
        """CRITICAL: Safety keywords trigger safety override and immediate review."""
        result = assess_priority("There is an electrical short circuit and smoke in lab 3.")
        assert result.suggested_priority == PriorityLevel.CRITICAL
        assert result.final_priority == PriorityLevel.CRITICAL
        assert result.safety_flag is True
        assert result.safety_override is True
        assert result.needs_human_review is True
        assert "smoke" in result.triggered_safety_keywords or "short circuit" in result.triggered_safety_keywords

    def test_mild_sounding_safety_complaint_still_overrides(self):
        """Even a mild safety complaint must trigger critical human review."""
        result = assess_priority("I noticed a slight gas leak smell in corridor.")
        assert result.suggested_priority == PriorityLevel.CRITICAL
        assert result.safety_override is True
        assert result.needs_human_review is True

    def test_score_range_0_to_100(self):
        result = assess_priority("The WiFi has been down in the library.")
        assert 0.0 <= result.score <= 100.0

    def test_priority_bands_low_medium_high(self):
        # 1. Low urgency complaint (minor cosmetic issue, 0 recurrence, recent)
        low_res = assess_priority(
            "Poster on bulletin board is slightly peeling off.",
            created_at=datetime.now(timezone.utc),
            recurrence_count=0,
        )
        assert low_res.score < 45.0
        assert low_res.suggested_priority == PriorityLevel.LOW
        assert low_res.safety_override is False

        # 2. Medium urgency complaint (multi-day wide disruption, multiple recurrences)
        med_res = assess_priority(
            "Whole floor has had completely no water since yesterday and broken taps are dirty.",
            created_at=datetime.now(timezone.utc) - timedelta(hours=36),
            recurrence_count=2,
        )
        assert 45.0 <= med_res.score < 75.0
        assert med_res.suggested_priority == PriorityLevel.MEDIUM

        # 3. High urgency complaint (saturating all non-safety factors to maximum)
        high_res = assess_priority(
            "Entire campus has had completely no water for days and broken supply not working at all. Everyone is affected.",
            created_at=datetime.now(timezone.utc) - timedelta(hours=72),
            recurrence_count=5,
        )
        assert high_res.score >= 75.0
        assert high_res.suggested_priority == PriorityLevel.HIGH

    def test_high_recurrence_increases_score(self):
        base = assess_priority("WiFi not working.", recurrence_count=0)
        high_recur = assess_priority("WiFi not working.", recurrence_count=5)
        assert high_recur.score > base.score

    def test_older_complaint_increases_score(self):
        fixed_now = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
        recent_res = assess_priority("Tap leaking.", created_at=fixed_now - timedelta(hours=2), current_time=fixed_now)
        old_res = assess_priority("Tap leaking.", created_at=fixed_now - timedelta(hours=70), current_time=fixed_now)
        assert old_res.score > recent_res.score

    def test_verified_safety_hazard_override_without_keywords(self):
        """External verification flag can escalate to critical even if text lacks keywords."""
        result = assess_priority("Water pipe maintenance required.", verified_safety_hazard=True)
        assert result.suggested_priority == PriorityLevel.CRITICAL
        assert result.safety_override is True
        assert result.needs_human_review is True


# ---------------------------------------------------------------------------
# Staff Override & Auditability Tests
# ---------------------------------------------------------------------------

class TestStaffOverrideAndAuditing:
    def test_staff_override_updates_final_priority_with_audit_trail(self):
        result = assess_priority("Flickering tube light in hallway.")
        assert result.suggested_priority == PriorityLevel.LOW
        assert result.final_priority == PriorityLevel.LOW
        assert result.staff_override is None

        # Staff elevates to HIGH due to upcoming VIP visit
        result.apply_override(
            staff_id="EMP-1042",
            new_priority=PriorityLevel.HIGH,
            reason="Upcoming NAAC accreditation inspection on this floor tomorrow morning."
        )

        assert result.suggested_priority == PriorityLevel.LOW  # Original retained
        assert result.final_priority == PriorityLevel.HIGH     # Active updated
        assert result.staff_override is not None
        assert result.staff_override.staff_id == "EMP-1042"
        assert result.staff_override.original_priority == PriorityLevel.LOW
        assert result.staff_override.override_priority == PriorityLevel.HIGH
        assert "accreditation" in result.staff_override.reason

    def test_staff_override_requires_non_empty_reason(self):
        result = assess_priority("Flickering tube light in hallway.")
        with pytest.raises(ValueError, match="reason must be provided"):
            result.apply_override(staff_id="EMP-1042", new_priority=PriorityLevel.HIGH, reason="")


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestPriorityEdgeCases:
    def test_empty_complaint_text(self):
        result = assess_priority("")
        assert isinstance(result, PriorityResult)
        assert 0.0 <= result.score <= 100.0

    def test_very_long_text(self):
        long_text = "The water supply is broken and tap is not working. " * 300
        result = assess_priority(long_text)
        assert isinstance(result, PriorityResult)
        assert 0.0 <= result.score <= 100.0

    def test_special_characters(self):
        text = "Water!!! @#$%^&*() isn't working??? Please!!! HELP!!!"
        result = assess_priority(text)
        assert isinstance(result, PriorityResult)
        assert 0.0 <= result.score <= 100.0
