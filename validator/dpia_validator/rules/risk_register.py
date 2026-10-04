"""RISK-1 / SCORE-1 / MIT-2 — risk-register internal consistency rules.

All findings-based; a rule never raises (a bad shape at the field this rule
reads is reported by SCHEMA-1, so every getter below degrades safely on
untrusted/malformed input rather than crashing — same discipline as
completeness.py).

These catch a sidecar that is individually schema-valid per field but
internally contradicts either the scoring methodology
(references/scoring.md) or the DPIA verdict's own meaning. None of them
require a new sidecar field — they cross-check fields the schema already
has (threshold.blacklist_match is handled in completeness.py; this module
covers risk_register[], mitigations[], and verdict).
"""
from ..findings import Finding
from ..registry import rule

SPEC_MATRIX = "references/scoring.md#risk-level-matrix"
SPEC_MODULATION = "references/scoring.md#modulating-factors"
SPEC_VERDICT = "references/scoring.md#dpia-verdict"
SPEC_HANDOFF = "SKILL.md#article-32-handoff"

# references/scoring.md "Risk Level Matrix" — Score Range -> Level, and the
# DPIA Verdict table's two outcomes compatible with an unmitigated Very High
# residual risk (Art. 36 consultation, or abandoning the processing).
_TIER_ORDER = ["Low", "Medium", "High", "Very High"]
_NON_APPROVING_VERDICTS = {"CONSULT_SA", "REJECTED"}


def _dict(value):
    return value if isinstance(value, dict) else {}


def _list(value):
    return value if isinstance(value, list) else []


def _tier_from_score(score):
    """references/scoring.md Risk Level Matrix: 1-3 Low, 4-6 Medium,
    7-12 High, 13-25 Very High."""
    if score <= 3:
        return "Low"
    if score <= 6:
        return "Medium"
    if score <= 12:
        return "High"
    return "Very High"


@rule(id="RISK-1", severity="rejection", category="risk",
      description="A residual risk_register entry at adjusted_level 'Very "
                  "High' with no mitigation naming it in risk_refs must not "
                  "be left under an APPROVED verdict (or no verdict at all) "
                  "— references/scoring.md's Very High row requires Art. 36 "
                  "consultation once residual risk remains at that level "
                  "with nothing left to reduce it.",
      spec_anchor=SPEC_VERDICT)
def unmitigated_very_high_residual_requires_consult_sa(sidecar, ctx):
    register = _list(sidecar.get("risk_register"))
    mitigations = _list(sidecar.get("mitigations"))
    linked_refs = set()
    for mit in mitigations:
        if not isinstance(mit, dict):
            continue
        for ref in _list(mit.get("risk_refs")):
            if isinstance(ref, str):
                linked_refs.add(ref)

    verdict = sidecar.get("verdict")
    out = []
    for risk in register:
        if not isinstance(risk, dict):
            continue
        if risk.get("adjusted_level") != "Very High":
            continue
        if risk.get("phase") == "inherent":
            # Inherent-phase entries are scored before mitigation is applied
            # at all (SKILL.md "Score inherent risk first, then re-score as
            # residual") — an unmitigated inherent Very High is the expected
            # starting point, not a contradiction. A missing `phase` is
            # treated as in-scope (fail closed) rather than assumed inherent.
            continue
        rid = risk.get("id")
        if rid is not None and rid in linked_refs:
            continue  # has at least one linked mitigation
        if verdict not in _NON_APPROVING_VERDICTS:
            out.append(Finding(
                rule_id="RISK-1", category="risk", severity="rejection",
                message=(f"risk_register entry {rid!r} is adjusted_level "
                          "'Very High' (not phase 'inherent') with no "
                          "mitigation whose risk_refs names it, but verdict "
                          f"is {verdict!r}. references/scoring.md's Very High "
                          "row ('Art. 36 prior consultation ... likely "
                          "required if residual risk remains at this level') "
                          "only accepts CONSULT_SA or REJECTED here — never "
                          "APPROVED/CONDITIONALLY_APPROVED, and never a "
                          "verdict left unset."),
                spec_anchor=SPEC_VERDICT, entry_type="risk", entry_id=rid,
                field="verdict",
            ))
    return out


@rule(id="SCORE-1", severity="rejection", category="risk",
      description="A risk_register entry's score and adjusted_level must be "
                  "consistent with its own likelihood x severity: score "
                  "(when given) must equal L x S, and adjusted_level may "
                  "only diverge from the raw L x S tier by the documented "
                  "+/-1-tier modulating-factor bound (references/scoring.md "
                  "Risk Level Matrix + Modulating Factors).",
      spec_anchor=SPEC_MATRIX)
def likelihood_severity_score_level_consistency(sidecar, ctx):
    out = []
    for risk in _list(sidecar.get("risk_register")):
        if not isinstance(risk, dict):
            continue
        likelihood = risk.get("likelihood")
        severity = risk.get("severity")
        if not isinstance(likelihood, int) or not isinstance(severity, int) \
                or isinstance(likelihood, bool) or isinstance(severity, bool):
            continue  # SCHEMA-1 already reports the type/range violation
        raw_score = likelihood * severity
        rid = risk.get("id")

        score = risk.get("score")
        if isinstance(score, int) and not isinstance(score, bool) and score != raw_score:
            out.append(Finding(
                rule_id="SCORE-1", category="risk", severity="rejection",
                message=(f"risk_register entry {rid!r} has score={score} but "
                          f"likelihood({likelihood}) x severity({severity}) = "
                          f"{raw_score}. Risk Score = Likelihood x Severity "
                          "(references/scoring.md Risk Level Matrix)."),
                spec_anchor=SPEC_MATRIX, entry_type="risk", entry_id=rid,
                field="score",
            ))

        adjusted_level = risk.get("adjusted_level")
        if isinstance(adjusted_level, str) and adjusted_level in _TIER_ORDER:
            raw_tier = _tier_from_score(raw_score)
            raw_index = _TIER_ORDER.index(raw_tier)
            adjusted_index = _TIER_ORDER.index(adjusted_level)
            drift = abs(adjusted_index - raw_index)
            if drift > 1:
                out.append(Finding(
                    rule_id="SCORE-1", category="risk", severity="rejection",
                    message=(f"risk_register entry {rid!r} has adjusted_level "
                              f"{adjusted_level!r} but likelihood({likelihood}) "
                              f"x severity({severity}) = {raw_score} is raw "
                              f"tier {raw_tier!r} ({drift} tiers away). A "
                              "modulating factor may shift the level by at "
                              "most one tier (references/scoring.md "
                              "Modulating Factors: 'shift the final risk "
                              "level +/-1 tier from the raw L x S score'), "
                              "not more."),
                    spec_anchor=SPEC_MODULATION, entry_type="risk",
                    entry_id=rid, field="adjusted_level",
                ))
    return out


@rule(id="MIT-2", severity="rejection", category="handoff",
      description="A mitigation's risk_refs must resolve to an existing "
                  "risk_register entry id. Same severity as MIT-1 for the "
                  "same reason: an unverifiable claim in the sidecar, not a "
                  "cosmetic gap — a mitigation named against a risk this "
                  "DPIA never registered cannot be checked against Art. "
                  "35(7)(d).",
      spec_anchor=SPEC_HANDOFF)
def mitigation_risk_refs_resolve(sidecar, ctx):
    out = []
    risk_ids = {r.get("id") for r in _list(sidecar.get("risk_register"))
                if isinstance(r, dict) and isinstance(r.get("id"), str)}
    for mit in _list(sidecar.get("mitigations")):
        if not isinstance(mit, dict):
            continue
        for ref in _list(mit.get("risk_refs")):
            if not isinstance(ref, str):
                continue  # SCHEMA-1 already reports the type violation
            if ref not in risk_ids:
                out.append(Finding(
                    rule_id="MIT-2", category="handoff", severity="rejection",
                    message=(f"Mitigation {mit.get('id')!r} names risk_refs "
                              f"{ref!r}, which matches no id in "
                              "risk_register. A mitigation can only be "
                              "linked to a risk this DPIA actually "
                              "registered."),
                    spec_anchor=SPEC_HANDOFF, entry_type="mitigation",
                    entry_id=mit.get("id"), field="risk_refs",
                ))
    return out
