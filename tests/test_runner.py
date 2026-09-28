"""Runner-level guards + one test per rule.

Mirrors skills/toms-art32/validator/toms_validator/test_runner.py's shape.
"""
import json
from pathlib import Path

import jsonschema
import pytest

import sys
VALIDATOR = Path(__file__).resolve().parents[1] / "validator"
sys.path.insert(0, str(VALIDATOR))

from dpia_validator.findings import Finding  # noqa: E402
from dpia_validator.runner import validate, Context, Result, to_findings_json  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SKILL_ROOT / "references" / "dpia-sidecar-schema.json"
FIX = VALIDATOR / "fixtures"


def _ctx():
    return Context(mode="internal", schema_path=SCHEMA,
                   references_dir=SKILL_ROOT / "references")


def _load(name: str) -> dict:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def test_empty_rule_registry_fails_closed(monkeypatch):
    monkeypatch.setattr("dpia_validator.runner.RULES", {})
    sidecar = _load("must_pass/minimal-clean.json")
    result = validate(sidecar, _ctx())
    assert result.status == "failed"
    assert any(f.rule_id == "RUNNER-0" and f.severity == "rejection"
               for f in result.findings), [f.to_dict() for f in result.findings]


def test_populated_registry_still_passes_clean_fixture():
    import dpia_validator.rules  # noqa: F401 — populates the registry
    sidecar = _load("must_pass/minimal-clean.json")
    result = validate(sidecar, _ctx())
    assert result.status in {"passed", "passed_with_warnings"}, \
        [f.to_dict() for f in result.findings]


def test_runner0_early_return_reports_the_real_mode_and_validated_at(monkeypatch):
    monkeypatch.setattr("dpia_validator.runner.RULES", {})
    sidecar = _load("must_pass/minimal-clean.json")
    ctx = Context(mode="submission", schema_path=SCHEMA,
                  references_dir=SKILL_ROOT / "references")
    result = validate(sidecar, ctx)
    assert result.status == "failed"
    assert result.mode == "submission"
    assert result.validated_at != ""


def test_populated_registry_run_carries_mode_and_validated_at():
    import dpia_validator.rules  # noqa: F401
    sidecar = _load("must_pass/minimal-clean.json")
    ctx = Context(mode="submission", schema_path=SCHEMA,
                  references_dir=SKILL_ROOT / "references")
    result = validate(sidecar, ctx)
    assert result.mode == "submission"
    assert result.validated_at != ""


def test_a_rule_that_raises_becomes_a_rejection_finding_never_crashes(monkeypatch):
    import dpia_validator.rules  # noqa: F401
    from dpia_validator.registry import RuleSpec

    def _boom(sidecar, ctx):
        raise ValueError("simulated rule crash")

    broken_registry = dict(__import__("dpia_validator.runner", fromlist=["RULES"]).RULES)
    broken_registry["BOOM-1"] = (
        RuleSpec(id="BOOM-1", severity="rejection", category="test",
                 description="test", spec_anchor="test"),
        _boom,
    )
    monkeypatch.setattr("dpia_validator.runner.RULES", broken_registry)
    sidecar = _load("must_pass/minimal-clean.json")
    result = validate(sidecar, _ctx())
    assert result.status == "failed"
    assert any(f.rule_id == "BOOM-1" and "simulated rule crash" in f.message
               for f in result.findings)


@pytest.mark.parametrize("fixture,rule_id", [
    ("must_fail/SCHEMA-1__invalid-dpia-required-enum.json", "SCHEMA-1"),
    ("must_fail/COMPLETE-1__blocking-unknown-present.json", "COMPLETE-1"),
    ("must_fail/CONSEQ-1__dpia-not-required-with-two-criteria.json", "CONSEQ-1"),
    ("must_fail/THRESH-1__mandatory-trigger-not-required.json", "THRESH-1"),
    ("must_fail/MIT-1__tracked-mitigation-missing-ref.json", "MIT-1"),
])
def test_each_must_fail_fixture_trips_its_own_rule_and_fails_closed(fixture, rule_id):
    import dpia_validator.rules  # noqa: F401
    sidecar = _load(fixture)
    result = validate(sidecar, _ctx())
    assert result.status == "failed"
    assert any(f.rule_id == rule_id and f.severity == "rejection"
               for f in result.findings), [f.to_dict() for f in result.findings]


def test_src1_reports_missing_manifest_via_sources_lock_override():
    import dpia_validator.rules  # noqa: F401
    sidecar = _load("must_pass/minimal-clean.json")
    ctx = Context(mode="internal", schema_path=SCHEMA,
                  references_dir=SKILL_ROOT / "references",
                  sources_lock_override={"schema_version": "1.0",
                                          "generated_at": "2026-09-24", "files": {}})
    result = validate(sidecar, ctx)
    assert result.status == "passed_with_warnings"
    src1 = [f for f in result.findings if f.rule_id == "SRC-1"]
    assert src1 and all(f.severity == "warning" for f in src1)
    # every on-disk references/**/*.md file is reported missing from the empty manifest
    assert any("edpb-criteria.md" in (f.entry_id or "") for f in src1)


def test_src1_flags_a_stale_manifest_entry():
    import dpia_validator.rules  # noqa: F401
    sidecar = _load("must_pass/minimal-clean.json")
    stale_files = {
        f"references/{p.relative_to(SKILL_ROOT / 'references').as_posix()}": {
            "source_type": "ai-drafted", "jurisdiction": "EU", "url": None,
            "last_verified": "2020-01-01", "confidence": "high",
            "owner": "oliverschmidtprietz",
        }
        for p in (SKILL_ROOT / "references").rglob("*.md")
    }
    ctx = Context(mode="internal", schema_path=SCHEMA,
                  references_dir=SKILL_ROOT / "references",
                  sources_lock_override={"schema_version": "1.0",
                                          "generated_at": "2026-09-24",
                                          "files": stale_files})
    result = validate(sidecar, ctx)
    assert result.status == "passed_with_warnings"
    assert any(f.rule_id == "SRC-1" and f.field == "last_verified"
               for f in result.findings)


# --- Portfolio findings-report 2.0 ------------------------------------------

_REPORT_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[3] / "docs" / "standards" / "schemas"
     / "findings-report-2.0.schema.json").read_text(encoding="utf-8")
)


def _sample_result() -> Result:
    return Result(
        status="passed_with_warnings",
        summary={"rejections": 0, "warnings": 1, "info": 0, "rules_evaluated": 6},
        findings=[Finding(
            rule_id="SRC-1", category="freshness", severity="warning", priority="high",
            message="references/sources.md exists on disk but has no entry in "
                     "sources.lock.json.",
            spec_anchor="sources.lock.json#freshness",
        )],
        mode="internal",
        artefact_path="assessment.json",
        validated_at="2026-09-24T09:12:00Z",
    )


def test_report_validates_against_the_portfolio_schema():
    jsonschema.validate(to_findings_json(_sample_result(), skill_version="1.14"),
                        _REPORT_SCHEMA)


def test_report_is_self_describing():
    report = to_findings_json(_sample_result(), skill_version="1.14")
    assert report["skill"] == "dpia-sentinel"
    assert report["skill_version"] == "1.14"
    assert report["report_schema_version"] == "2.0"


def test_summary_has_exactly_the_four_standard_keys():
    report = to_findings_json(_sample_result(), skill_version="1.14")
    assert set(report["summary"]) == {"rejections", "warnings", "info", "rules_evaluated"}
