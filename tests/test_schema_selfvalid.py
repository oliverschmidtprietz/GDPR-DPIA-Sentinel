import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA = Path(__file__).parents[1] / "references" / "dpia-sidecar-schema.json"


def test_schema_is_itself_valid_draft2020():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)  # raises if the schema is malformed


def test_schema_version_is_decoupled_from_skill_version():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    sv = schema["properties"]["schema_version"]
    assert sv["enum"] == ["1.0"]
    assert sv["default"] == "1.0"


def test_mitigation_status_never_claims_toms_art32_dimensions():
    """dpia-sentinel must never certify a mitigation's Art. 32 appropriateness,
    implementation, or effectiveness itself (SKILL.md Article 32 handoff) — the
    enum is closed to two values, neither of which is an implementation/
    effectiveness claim."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    status_enum = schema["properties"]["mitigations"]["items"]["properties"]["status"]["enum"]
    assert set(status_enum) == {"envisaged", "toms_art32_tracked"}
    forbidden = {"implemented", "effective", "verified", "evidenced", "tested"}
    assert forbidden.isdisjoint(status_enum)
