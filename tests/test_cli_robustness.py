"""CLI fail-closed tests — break-it test 2026-10-02.

A break-it probe pass (scratchpad/breakit/dpia-sentinel/A9..A11, mirrored by
dpa-art28's X1 finding) found the CLI's file-read/parse step raising raw
Python tracebacks on missing files, unreadable files, invalid UTF-8, invalid
JSON, and (with --emit-core-artefact) non-object top-level JSON. Every case
here must instead fail closed: no traceback, exit 1, status "failed", a
rejection finding, exactly like any other rule failure.
"""
import json
import subprocess
import sys
from pathlib import Path

import jsonschema

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
VALIDATE = SKILL_ROOT / "validator" / "validate.py"
ARTEFACT_SCHEMA = json.loads(
    (REPO_ROOT / "docs" / "standards" / "schemas"
     / "skill-artefact-1.1.schema.json").read_text(encoding="utf-8"))


def run_cli(*argv):
    return subprocess.run(
        [sys.executable, str(VALIDATE), *map(str, argv)],
        capture_output=True, text=True)


def _assert_fails_closed(proc):
    assert proc.returncode == 1
    assert "Traceback (most recent call last)" not in proc.stderr
    assert "status: failed" in proc.stdout
    assert "CLI-0" in proc.stdout


def test_missing_file_fails_closed(tmp_path):
    proc = run_cli(tmp_path / "does-not-exist.json")
    _assert_fails_closed(proc)
    assert "not found" in proc.stdout


def test_directory_instead_of_file_fails_closed(tmp_path):
    a_dir = tmp_path / "actually-a-directory.json"
    a_dir.mkdir()
    proc = run_cli(a_dir)
    _assert_fails_closed(proc)
    assert "directory" in proc.stdout


def test_invalid_utf8_fails_closed(tmp_path):
    bad = tmp_path / "not-utf8.json"
    bad.write_bytes(b"\xff\xfe\x00\x01not-utf8")
    proc = run_cli(bad)
    _assert_fails_closed(proc)
    assert "UTF-8" in proc.stdout


def test_invalid_json_fails_closed(tmp_path):
    bad = tmp_path / "invalid.json"
    bad.write_text("{ this is not json", encoding="utf-8")
    proc = run_cli(bad)
    _assert_fails_closed(proc)
    assert "JSON" in proc.stdout


def test_invalid_json_fails_closed_in_json_format_too(tmp_path):
    bad = tmp_path / "invalid.json"
    bad.write_text("{ this is not json", encoding="utf-8")
    proc = run_cli(bad, "--format", "json")
    assert proc.returncode == 1
    assert "Traceback (most recent call last)" not in proc.stderr
    envelope = json.loads(proc.stdout)
    assert envelope["status"] == "failed"
    assert envelope["findings"][0]["rule_id"] == "CLI-0"


def test_top_level_array_with_emit_core_artefact_fails_closed_not_typeerror(tmp_path):
    """The exact crash the probe found (mirrors dpa-art28's validate.py:62
    TypeError): {**sidecar, ...} raised when the top-level JSON value isn't a
    dict (a JSON array here; null is the same failure mode)."""
    arr = tmp_path / "array.json"
    arr.write_text("[1, 2, 3]", encoding="utf-8")
    out = tmp_path / "core.json"
    proc = run_cli(arr, "--emit-core-artefact", out)
    assert proc.returncode == 1
    assert "Traceback (most recent call last)" not in proc.stderr
    assert out.is_file()
    artefact = json.loads(out.read_text(encoding="utf-8"))
    jsonschema.validate(artefact, ARTEFACT_SCHEMA, format_checker=jsonschema.FormatChecker())
    assert artefact["outcome"]["status"] == "blocked"


def test_top_level_null_with_emit_core_artefact_fails_closed(tmp_path):
    null_file = tmp_path / "null.json"
    null_file.write_text("null", encoding="utf-8")
    out = tmp_path / "core.json"
    proc = run_cli(null_file, "--emit-core-artefact", out)
    assert proc.returncode == 1
    assert "Traceback (most recent call last)" not in proc.stderr
    artefact = json.loads(out.read_text(encoding="utf-8"))
    jsonschema.validate(artefact, ARTEFACT_SCHEMA, format_checker=jsonschema.FormatChecker())


def test_missing_file_with_emit_core_artefact_still_writes_a_blocked_artefact(tmp_path):
    out = tmp_path / "core.json"
    proc = run_cli(tmp_path / "does-not-exist.json", "--emit-core-artefact", out)
    assert proc.returncode == 1
    assert "Traceback (most recent call last)" not in proc.stderr
    assert out.is_file()
    artefact = json.loads(out.read_text(encoding="utf-8"))
    jsonschema.validate(artefact, ARTEFACT_SCHEMA, format_checker=jsonschema.FormatChecker())
    assert artefact["outcome"]["status"] == "blocked"
