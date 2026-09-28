"""sources.lock.json shape + coverage + freshness (own-file discipline)."""
import datetime as dt
import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = SKILL_ROOT / "sources.lock.json"
REFERENCES = SKILL_ROOT / "references"


def _lock() -> dict:
    return json.loads(LOCK_PATH.read_text(encoding="utf-8"))


def test_lock_has_the_required_top_level_keys():
    lock = _lock()
    assert set(lock) >= {"schema_version", "generated_at", "files"}
    assert isinstance(lock["files"], dict)


def test_every_on_disk_reference_md_file_is_declared():
    lock = _lock()
    declared = set(lock["files"])
    on_disk = {f"references/{p.relative_to(REFERENCES).as_posix()}"
               for p in REFERENCES.rglob("*.md")}
    missing = on_disk - declared
    assert not missing, f"undeclared reference files: {sorted(missing)}"


def test_every_declared_entry_has_the_required_fields_and_a_real_owner():
    lock = _lock()
    for path, entry in lock["files"].items():
        for field in ("source_type", "jurisdiction", "last_verified", "confidence", "owner"):
            assert field in entry, f"{path} is missing '{field}'"
        assert entry["owner"] == "oliverschmidtprietz"


def test_no_declared_entry_is_stale_beyond_365_days():
    lock = _lock()
    today = dt.date.today()
    threshold = today - dt.timedelta(days=365)
    stale = {
        path: entry["last_verified"]
        for path, entry in lock["files"].items()
        if dt.date.fromisoformat(entry["last_verified"]) < threshold
    }
    assert not stale, f"stale sources.lock.json entries (>365 days): {stale}"


def test_no_declared_entry_last_verified_is_in_the_future():
    lock = _lock()
    today = dt.date.today()
    future = {path: entry["last_verified"] for path, entry in lock["files"].items()
              if dt.date.fromisoformat(entry["last_verified"]) > today}
    assert not future, f"sources.lock.json entries dated in the future: {future}"
