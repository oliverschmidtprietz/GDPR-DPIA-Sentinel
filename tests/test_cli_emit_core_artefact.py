"""CLI tests for --emit-core-artefact.

Same contract as toms-art32's/ropa's flag: the emitted artefact is built
from the LIVE validation result, never the sidecar's embedded validation
block, and a blocked artefact is still written on a failing input.
"""
import json
import subprocess
import sys
from pathlib import Path

import jsonschema

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
VALIDATE = SKILL_ROOT / "validator" / "validate.py"
CLEAN_FIXTURE = SKILL_ROOT / "validator" / "fixtures" / "must_pass" / "minimal-clean.json"
FAILING_FIXTURE = (SKILL_ROOT / "validator" / "fixtures" / "must_fail"
                   / "THRESH-1__mandatory-trigger-not-required.json")
ARTEFACT_SCHEMA = json.loads(
    (REPO_ROOT / "docs" / "standards" / "schemas"
     / "skill-artefact-1.1.schema.json").read_text(encoding="utf-8"))


def run_cli(*argv):
    return subprocess.run(
        [sys.executable, str(VALIDATE), *map(str, argv)],
        capture_output=True, text=True)


def test_emit_writes_schema_valid_core_artefact_on_a_passing_run(tmp_path):
    out = tmp_path / "core.json"
    proc = run_cli(CLEAN_FIXTURE, "--emit-core-artefact", out, "--format", "json")
    assert proc.returncode == 0, proc.stderr
    artefact = json.loads(out.read_text(encoding="utf-8"))
    jsonschema.validate(artefact, ARTEFACT_SCHEMA, format_checker=jsonschema.FormatChecker())
    assert artefact["skill"] == "dpia-sentinel"
    envelope = json.loads(proc.stdout)
    assert envelope["report_schema_version"] == "2.0"


def test_emit_still_writes_a_blocked_artefact_on_a_failing_run(tmp_path):
    out = tmp_path / "core.json"
    proc = run_cli(FAILING_FIXTURE, "--emit-core-artefact", out)
    assert proc.returncode == 1
    assert out.is_file()
    artefact = json.loads(out.read_text(encoding="utf-8"))
    jsonschema.validate(artefact, ARTEFACT_SCHEMA, format_checker=jsonschema.FormatChecker())
    assert artefact["outcome"]["status"] == "blocked"


def test_emit_reflects_live_result_not_embedded_validation_block(tmp_path):
    sidecar = json.loads(CLEAN_FIXTURE.read_text(encoding="utf-8"))
    sidecar["validation"] = {"status": "failed", "findings": []}
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(sidecar), encoding="utf-8")
    out = tmp_path / "core.json"
    proc = run_cli(tampered, "--emit-core-artefact", out)
    assert proc.returncode == 0, proc.stderr
    artefact = json.loads(out.read_text(encoding="utf-8"))
    assert artefact["outcome"]["status"] == "complete"
