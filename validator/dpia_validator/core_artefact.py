"""Project a native dpia-sentinel sidecar into the portfolio core artefact.

A PROJECTION, not a rewrite: the native sidecar is never modified. Mirrors
skills/toms-art32/validator/toms_validator/core_artefact.py in structure and
signature — `to_core_artefact(sidecar, *, skill_version) -> dict` — but the
field mapping is dpia-sentinel's own.

subject.type is "processing_activity" (skill-artefact-1.1.schema.json
subject.type enum) — a DPIA assesses one named processing activity, not an
organisation as a whole (SKILL.md's own "Required facts" open with
"processing description and purposes").

sources[]/handoffs[]/unknowns[] are driven by the LIVE sidecar content, never
hard-coded empty (the exact defect the standard calls out in ropa and
toms-art32, §7 "NOT YET IMPLEMENTED" / gap 8):

  - sources[]: `references/edpb-criteria.md` is always included — every
    sidecar carries a required `threshold` block, and the threshold verdict
    is always reasoned against the EDPB nine criteria (SKILL.md Routing).
    `references/scoring.md` is included only when `risk_register` is
    non-empty (scoring.md is only actually used once a risk register
    exists). A `references/jurisdictions/<slug>.md` entry is included for
    each code in `jurisdictions_checked` that has a mapped file AND a
    sources.lock.json entry — an unmapped or unlisted jurisdiction
    contributes nothing rather than a fabricated citation.
  - handoffs[]: one entry per mitigation with status "toms_art32_tracked"
    (SKILL.md "Article 32 handoff") — real only when the sidecar actually
    names a tracked ref.
  - unknowns[]: the sidecar's own `open_unknowns[]` passed through verbatim,
    PLUS one derived entry per mitigation with status "envisaged" — a named
    mitigation with no toms-art32 status attached is the one handoff/unknown
    case the adoption brief calls out explicitly: never a silent pass.
"""
from __future__ import annotations  # PEP 604 "|" unions below, on a requires-python >=3.9 file

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ARTEFACT_SCHEMA_VERSION = "1.1"
SKILL_NAME = "dpia-sentinel"

_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
_UNKNOWN_ACTIVITY_ID = "unknown-processing-activity"

_OUTCOME_BY_VALIDATION_STATUS = {
    "passed": "complete",
    "passed_with_warnings": "provisional",
    "failed": "blocked",
}

# threshold.jurisdictions_checked country code -> references/jurisdictions/<slug>.md,
# grounded in the files SKILL.md's Routing table actually lists.
_JURISDICTION_FILE = {
    "DE": "de-dsk", "FR": "fr-cnil", "IE": "ie-dpc", "BE": "be-apd",
    "NL": "nl-ap", "IT": "it-garante", "PL": "pl-uodo",
}

_DEFAULT_SOURCES_LOCK = Path(__file__).resolve().parents[2] / "sources.lock.json"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or _UNKNOWN_ACTIVITY_ID


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _generated_at(sidecar: dict) -> str:
    value = sidecar.get("generated_at")
    if isinstance(value, str) and _DATETIME_RE.match(value):
        return value
    return _now_iso()


def _subject(sidecar: dict) -> dict:
    activity = sidecar.get("processing_activity")
    if not isinstance(activity, dict):
        activity = {}
    slug = activity.get("activity_slug")
    label = activity.get("label")
    if slug:
        subject_id = slug
    elif label:
        subject_id = _slugify(label)
    else:
        subject_id = _UNKNOWN_ACTIVITY_ID
    return {
        "id": subject_id,
        "label": label or slug or "unknown processing activity",
        "type": "processing_activity",
    }


def _risk_counts(register) -> dict:
    counts: dict = {}
    for risk in register:
        if not isinstance(risk, dict):
            continue
        level = risk.get("adjusted_level", "unrated")
        counts[level] = counts.get(level, 0) + 1
    return counts


def _outcome_summary(sidecar: dict) -> str:
    threshold = sidecar.get("threshold")
    threshold = threshold if isinstance(threshold, dict) else {}
    parts = [f"dpia_required={threshold.get('dpia_required', 'unrated')}"]
    register = sidecar.get("risk_register")
    register = register if isinstance(register, list) else []
    counts = _risk_counts(register)
    if counts:
        parts.append("risks: " + ", ".join(
            f"{n} {level}" for level, n in sorted(counts.items())))
    verdict = sidecar.get("verdict")
    if isinstance(verdict, str):
        parts.append(f"verdict={verdict}")
    return "; ".join(parts)


def _gap(f: dict) -> dict:
    return {
        "id": f.get("entry_id") or f.get("rule_id") or "gap",
        "severity": f.get("severity") or "rejection",
        "message": f.get("message") or "(no message on this finding)",
    }


def _load_sources_lock(sources_lock):
    if sources_lock is not None:
        return sources_lock if isinstance(sources_lock, dict) else {}
    if not _DEFAULT_SOURCES_LOCK.is_file():
        return {}
    try:
        return json.loads(_DEFAULT_SOURCES_LOCK.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _source_entry(files: dict, path: str) -> dict | None:
    entry = files.get(path)
    if not isinstance(entry, dict):
        return None
    last_verified = entry.get("last_verified")
    if not isinstance(last_verified, str):
        return None
    citation = entry.get("notes") or (
        f"{entry.get('source_type', 'source')} ({entry.get('jurisdiction', 'n/a')})")
    return {"id": path, "citation": citation, "last_verified": last_verified}


def _sources(sidecar: dict, sources_lock) -> list:
    lock = _load_sources_lock(sources_lock)
    files = lock.get("files") if isinstance(lock.get("files"), dict) else {}
    out = []
    threshold = sidecar.get("threshold")
    if isinstance(threshold, dict) and threshold:
        entry = _source_entry(files, "references/edpb-criteria.md")
        if entry:
            out.append(entry)
    register = sidecar.get("risk_register")
    if isinstance(register, list) and register:
        entry = _source_entry(files, "references/scoring.md")
        if entry:
            out.append(entry)
    jurisdictions = sidecar.get("jurisdictions_checked")
    if isinstance(jurisdictions, list):
        for code in jurisdictions:
            slug = _JURISDICTION_FILE.get(code)
            if not slug:
                continue
            entry = _source_entry(files, f"references/jurisdictions/{slug}.md")
            if entry:
                out.append(entry)
    return out


def _handoffs_and_unknowns(sidecar: dict) -> tuple:
    handoffs = []
    unknowns = []
    for mit in sidecar.get("mitigations") or []:
        if not isinstance(mit, dict):
            continue
        mid = mit.get("id", "unknown-mitigation")
        status = mit.get("status")
        if status == "toms_art32_tracked" and mit.get("toms_art32_ref"):
            handoffs.append({
                "sibling_skill": "toms-art32",
                "reason": f"Mitigation {mid!r} is named in this DPIA under Art. "
                          "35(7)(d); appropriateness, implementation status, "
                          "evidence and effectiveness are toms-art32's (SKILL.md "
                          "Article 32 handoff).",
                "payload_ref": mit["toms_art32_ref"],
            })
        elif status == "envisaged":
            unknowns.append({
                "id": f"mitigation-{mid}-toms-art32-status",
                "question": f"Mitigation {mid!r} is recorded as envisaged with no "
                            "toms-art32 status attached — is it implemented, and "
                            "if so is it verified? An envisaged measure must not be "
                            "imported into the residual-risk calculation as though "
                            "it were live.",
                "blocking": False,
            })
    for unk in sidecar.get("open_unknowns") or []:
        if isinstance(unk, dict) and "id" in unk and "question" in unk:
            unknowns.append({
                "id": unk["id"],
                "question": unk["question"],
                "blocking": bool(unk.get("blocking", False)),
            })
    return handoffs, unknowns


def to_core_artefact(sidecar: dict, *, skill_version: str, sources_lock=None) -> dict:
    validation = sidecar.get("validation")
    validation = validation if isinstance(validation, dict) else {}
    validation_findings = validation.get("findings")
    validation_findings = validation_findings if isinstance(validation_findings, list) else []

    handoffs, unknowns = _handoffs_and_unknowns(sidecar)

    return {
        "artefact_schema_version": ARTEFACT_SCHEMA_VERSION,
        "skill": SKILL_NAME,
        "skill_version": skill_version,
        "generated_at": _generated_at(sidecar),
        "subject": _subject(sidecar),
        "outcome": {
            "status": _OUTCOME_BY_VALIDATION_STATUS.get(
                validation.get("status", "passed"), "provisional"),
            "summary": _outcome_summary(sidecar),
        },
        "gaps": [_gap(f) for f in validation_findings if isinstance(f, dict)],
        "sources": _sources(sidecar, sources_lock),
        "handoffs": handoffs,
        "unknowns": unknowns,
    }


def blocked_artefact(*, skill_version: str, reason: str) -> dict:
    """Minimal, always schema-valid artefact for when `to_core_artefact` itself
    raises despite the guards above (defence in depth, mirrors
    dpia_validator.runner.validate()'s per-rule exception handler)."""
    return {
        "artefact_schema_version": ARTEFACT_SCHEMA_VERSION,
        "skill": SKILL_NAME,
        "skill_version": skill_version,
        "generated_at": _now_iso(),
        "subject": {"id": _UNKNOWN_ACTIVITY_ID, "label": "unknown processing activity",
                    "type": "processing_activity"},
        "outcome": {
            "status": "blocked",
            "summary": f"Core artefact adapter failed: {reason}",
        },
        "gaps": [{
            "id": "core-artefact-adapter-error",
            "severity": "rejection",
            "message": f"to_core_artefact raised: {reason}",
        }],
        "sources": [],
        "handoffs": [],
        "unknowns": [],
    }
