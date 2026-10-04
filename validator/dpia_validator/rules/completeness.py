"""COMPLETE-1 / CONSEQ-1 / THRESH-1 / MIT-1 — completeness and consequential-
consistency rules. All findings-based; a rule never raises (a bad shape at
the field this rule reads is reported by SCHEMA-1, so every getter below
degrades safely on untrusted/malformed input rather than crashing).

These are deliberately NOT cosmetic checks: each one catches a sidecar that
is individually schema-valid per field, but internally contradicts either
SKILL.md's own legal-precision rules or the Art. 32 handoff boundary.
"""
from ..findings import Finding
from ..registry import rule

SPEC_THRESHOLD = "SKILL.md#legal-precision-points"
SPEC_HANDOFF = "SKILL.md#article-32-handoff"


def _dict(value):
    return value if isinstance(value, dict) else {}


def _list(value):
    return value if isinstance(value, list) else []


@rule(id="COMPLETE-1", severity="rejection", category="completeness",
      description="A blocking open unknown must stop the run — a required fact "
                  "you don't have is a question, never an assumption (SKILL.md "
                  "'Required facts').",
      spec_anchor="SKILL.md#required-facts")
def blocking_unknown_present(sidecar, ctx):
    out = []
    for unk in _list(sidecar.get("open_unknowns")):
        if not isinstance(unk, dict):
            continue  # SCHEMA-1 already reports the type violation
        if unk.get("blocking") is True:
            out.append(Finding(
                rule_id="COMPLETE-1", category="completeness", severity="rejection",
                message=f"Blocking open unknown {unk.get('id')!r} is unresolved: "
                        f"{unk.get('question')!r}. A required fact is a question, "
                        "never an assumption, until it is answered or explicitly "
                        "downgraded to non-blocking.",
                spec_anchor="SKILL.md#required-facts",
                entry_type="open_unknown", entry_id=unk.get("id"),
            ))
    return out


@rule(id="CONSEQ-1", severity="rejection", category="threshold",
      description="dpia_required: no is inconsistent with 2+ EDPB criteria met "
                  "(WP248 rev.01 two-criteria rule creates a strong presumption).",
      spec_anchor=SPEC_THRESHOLD)
def two_criteria_contradiction(sidecar, ctx):
    threshold = _dict(sidecar.get("threshold"))
    count = threshold.get("criteria_met_count")
    required = threshold.get("dpia_required")
    if required == "no" and isinstance(count, (int, float)) and count >= 2:
        return [Finding(
            rule_id="CONSEQ-1", category="threshold", severity="rejection",
            message=f"threshold.dpia_required is 'no' but criteria_met_count={count} "
                    "(>=2). WP248 rev.01's two-criteria rule creates a strong "
                    "presumption a DPIA IS required; 'no' needs either a corrected "
                    "count or an exceptionally well-documented justification "
                    "recorded in threshold.rationale, not a bare 'no'.",
            spec_anchor=SPEC_THRESHOLD, field="threshold.dpia_required",
        )]
    return []


@rule(id="THRESH-1", severity="rejection", category="threshold",
      description="An Art. 35(3) mandatory trigger is absolute — dpia_required "
                  "must be 'yes' when mandatory_trigger is true (SKILL.md Legal "
                  "Precision Point 1: no balancing, no judgment call).",
      spec_anchor=SPEC_THRESHOLD)
def mandatory_trigger_absolute(sidecar, ctx):
    threshold = _dict(sidecar.get("threshold"))
    if threshold.get("mandatory_trigger") is True and threshold.get("dpia_required") != "yes":
        return [Finding(
            rule_id="THRESH-1", category="threshold", severity="rejection",
            message="threshold.mandatory_trigger is true but dpia_required is "
                    f"{threshold.get('dpia_required')!r}, not 'yes'. An Art. 35(3) "
                    "mandatory trigger is absolute — no balancing, no judgment call.",
            spec_anchor=SPEC_THRESHOLD, field="threshold.dpia_required",
        )]
    return []


@rule(id="THRESH-2", severity="rejection", category="threshold",
      description="A national Art. 35(4) blacklist match is also absolute — "
                  "dpia_required must be 'yes' when threshold.blacklist_match "
                  "is true (SKILL.md Legal Precision Point 5: a blacklist "
                  "match is a trigger in its own right, not merely additive "
                  "to the nine-criteria analysis).",
      spec_anchor=SPEC_THRESHOLD)
def blacklist_match_absolute(sidecar, ctx):
    threshold = _dict(sidecar.get("threshold"))
    if threshold.get("blacklist_match") is True and threshold.get("dpia_required") != "yes":
        return [Finding(
            rule_id="THRESH-2", category="threshold", severity="rejection",
            message="threshold.blacklist_match is true but dpia_required is "
                    f"{threshold.get('dpia_required')!r}, not 'yes'. A "
                    "national Art. 35(4) blacklist match requires a DPIA "
                    "regardless of how many EDPB criteria are separately met "
                    "or how the rationale frames it — no balancing, no "
                    "judgment call (SKILL.md Legal Precision Point 5).",
            spec_anchor=SPEC_THRESHOLD, field="threshold.dpia_required",
        )]
    return []


@rule(id="MIT-1", severity="rejection", category="handoff",
      description="A mitigation claimed as toms_art32_tracked must carry a "
                  "toms_art32_ref — dpia-sentinel never certifies Art. 32 "
                  "appropriateness, implementation or effectiveness itself.",
      spec_anchor=SPEC_HANDOFF)
def tracked_mitigation_requires_ref(sidecar, ctx):
    out = []
    for mit in _list(sidecar.get("mitigations")):
        if not isinstance(mit, dict):
            continue
        if mit.get("status") == "toms_art32_tracked" and not mit.get("toms_art32_ref"):
            out.append(Finding(
                rule_id="MIT-1", category="handoff", severity="rejection",
                message=f"Mitigation {mit.get('id')!r} is status "
                        "'toms_art32_tracked' but carries no toms_art32_ref. That "
                        "status claims a live toms-art32 tracking record — without "
                        "a ref it cannot be verified and exceeds what toms-art32 "
                        "would actually recognise. Use status 'envisaged' until the "
                        "handoff is real.",
                spec_anchor=SPEC_HANDOFF, entry_type="mitigation", entry_id=mit.get("id"),
                field="toms_art32_ref",
            ))
    return out
