"""Tests for dpia_validator.core_artefact.to_core_artefact."""
import json
import sys
from pathlib import Path

import jsonschema
import pytest

VALIDATOR = Path(__file__).resolve().parents[1] / "validator"
sys.path.insert(0, str(VALIDATOR))

from dpia_validator.core_artefact import to_core_artefact, blocked_artefact  # noqa: E402

_ARTEFACT_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[3] / "docs" / "standards" / "schemas"
     / "skill-artefact-1.1.schema.json").read_text(encoding="utf-8")
)

_LOCK = {
    "schema_version": "1.0",
    "generated_at": "2026-09-24",
    "files": {
        "references/edpb-criteria.md": {
            "source_type": "ai-drafted", "jurisdiction": "EU", "url": None,
            "last_verified": "2026-03-09", "confidence": "high",
            "owner": "oliverschmidtprietz",
        },
        "references/scoring.md": {
            "source_type": "ai-drafted", "jurisdiction": "EU", "url": None,
            "last_verified": "2026-04-19", "confidence": "high",
            "owner": "oliverschmidtprietz",
        },
        "references/jurisdictions/de-dsk.md": {
            "source_type": "sa-guidance", "jurisdiction": "DE",
            "url": "https://www.datenschutzkonferenz-online.de/",
            "last_verified": "2026-03-09", "confidence": "high",
            "owner": "oliverschmidtprietz",
        },
    },
}


def _native() -> dict:
    return {
        "schema_version": "1.0",
        "generated_by": "dpia-sentinel skill v<X.Y>",
        "generated_at": "2026-09-24T09:00:00Z",
        "processing_activity": {
            "label": "Employee CCTV monitoring pilot",
            "activity_slug": "employee-cctv-monitoring-pilot",
        },
        "threshold": {
            "mandatory_trigger": False,
            "criteria_met_count": 1,
            "dpia_required": "borderline",
        },
        "jurisdictions_checked": ["DE"],
        "risk_register": [
            {"id": "risk-1", "track": "B", "description": "Unauthorised access.",
             "likelihood": 2, "severity": 3, "adjusted_level": "Medium"},
        ],
        "mitigations": [
            {"id": "mit-tracked", "description": "Access control.",
             "status": "toms_art32_tracked", "toms_art32_ref": "dep-123"},
            {"id": "mit-envisaged", "description": "Retention limit.",
             "status": "envisaged"},
        ],
        "open_unknowns": [
            {"id": "unk-1", "question": "What is the retention period?", "blocking": False},
        ],
        "verdict": "CONDITIONALLY_APPROVED",
        "validation": {"status": "passed", "findings": []},
    }


def test_projection_is_schema_valid():
    doc = to_core_artefact(_native(), skill_version="1.14", sources_lock=_LOCK)
    jsonschema.validate(doc, _ARTEFACT_SCHEMA, format_checker=jsonschema.FormatChecker())


def test_subject_is_processing_activity_typed():
    doc = to_core_artefact(_native(), skill_version="1.14", sources_lock=_LOCK)
    assert doc["subject"] == {
        "id": "employee-cctv-monitoring-pilot",
        "label": "Employee CCTV monitoring pilot",
        "type": "processing_activity",
    }


def test_subject_id_falls_back_to_slugified_label_when_slug_absent():
    native = _native()
    del native["processing_activity"]["activity_slug"]
    doc = to_core_artefact(native, skill_version="1.14", sources_lock=_LOCK)
    assert doc["subject"]["id"] == "employee-cctv-monitoring-pilot"


def test_subject_id_is_an_unmistakable_placeholder_when_activity_entirely_absent():
    native = _native()
    del native["processing_activity"]
    doc = to_core_artefact(native, skill_version="1.14", sources_lock=_LOCK)
    assert doc["subject"]["id"] == "unknown-processing-activity"


def test_tracked_mitigation_with_ref_emits_a_handoff_to_toms_art32():
    doc = to_core_artefact(_native(), skill_version="1.14", sources_lock=_LOCK)
    assert doc["handoffs"] == [{
        "sibling_skill": "toms-art32",
        "reason": "Mitigation 'mit-tracked' is named in this DPIA under Art. "
                  "35(7)(d); appropriateness, implementation status, evidence and "
                  "effectiveness are toms-art32's (SKILL.md Article 32 handoff).",
        "payload_ref": "dep-123",
    }]


def test_envisaged_mitigation_with_no_toms_art32_status_emits_an_unknown_not_a_silent_pass():
    """The one handoff/unknown case the adoption brief calls out explicitly
    (SIX-SKILL-ADOPTION-BRIEF-2026-09-24.md #1 dpia-sentinel): a mitigation
    named with no toms-art32 status attached must surface as an unknown."""
    doc = to_core_artefact(_native(), skill_version="1.14", sources_lock=_LOCK)
    ids = {u["id"] for u in doc["unknowns"]}
    assert "mitigation-mit-envisaged-toms-art32-status" in ids


def test_native_open_unknowns_pass_through():
    doc = to_core_artefact(_native(), skill_version="1.14", sources_lock=_LOCK)
    ids = {u["id"] for u in doc["unknowns"]}
    assert "unk-1" in ids


def test_sources_are_driven_by_run_content_not_hard_coded():
    """sources[] must reflect what THIS run actually relied on: threshold is
    always present (edpb-criteria.md), a risk_register is present (scoring.md),
    and jurisdictions_checked=['DE'] pulls in the DE lock entry — dropping any
    of those three inputs must drop the corresponding source."""
    doc = to_core_artefact(_native(), skill_version="1.14", sources_lock=_LOCK)
    ids = {s["id"] for s in doc["sources"]}
    assert ids == {"references/edpb-criteria.md", "references/scoring.md",
                   "references/jurisdictions/de-dsk.md"}

    native = _native()
    del native["risk_register"]
    native["jurisdictions_checked"] = []
    doc2 = to_core_artefact(native, skill_version="1.14", sources_lock=_LOCK)
    ids2 = {s["id"] for s in doc2["sources"]}
    assert ids2 == {"references/edpb-criteria.md"}


def test_sources_never_hard_coded_to_a_constant_empty_list():
    doc = to_core_artefact(_native(), skill_version="1.14", sources_lock=_LOCK)
    assert doc["sources"] != []


def test_gaps_come_from_the_live_validation_result_not_the_embedded_block():
    native = _native()
    native["validation"] = {
        "status": "failed",
        "findings": [{"rule_id": "THRESH-1", "severity": "rejection",
                       "message": "boom", "category": "threshold",
                       "spec_anchor": "x", "entry_id": None}],
    }
    doc = to_core_artefact(native, skill_version="1.14", sources_lock=_LOCK)
    assert doc["outcome"]["status"] == "blocked"
    assert doc["gaps"] == [{"id": "THRESH-1", "severity": "rejection", "message": "boom"}]


def test_substantive_risk_levels_surface_in_the_outcome_summary_not_as_gaps():
    doc = to_core_artefact(_native(), skill_version="1.14", sources_lock=_LOCK)
    assert "Medium" in doc["outcome"]["summary"]
    gap_severities = {g["severity"] for g in doc["gaps"]}
    assert gap_severities.isdisjoint({"Low", "Medium", "High", "Very High"})


def test_native_artefact_is_not_mutated():
    native = _native()
    before = json.dumps(native, sort_keys=True)
    to_core_artefact(native, skill_version="1.14", sources_lock=_LOCK)
    assert json.dumps(native, sort_keys=True) == before


def test_blocked_artefact_fallback_is_schema_valid():
    doc = blocked_artefact(skill_version="1.14", reason="ValueError: boom")
    jsonschema.validate(doc, _ARTEFACT_SCHEMA, format_checker=jsonschema.FormatChecker())
    assert doc["outcome"]["status"] == "blocked"
