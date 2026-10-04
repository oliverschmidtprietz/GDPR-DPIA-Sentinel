# dpia-sentinel Validator (v0.1.0)

Deterministic Python program that validates a native dpia-sentinel sidecar
against `references/dpia-sidecar-schema.json` and the rule set below. Mirrors
the architecture of `skills/toms-art32/validator/` (frozen `Finding`
dataclass, `@rule` decorator + `RULES` registry, a runner that iterates
every registered rule and never lets a rule crash the run).

## Quick start

```bash
# Validate a sidecar (internal mode, human-readable output)
uv run skills/dpia-sentinel/validator/validate.py path/to/dpia-sidecar.json

# JSON output (findings-report 2.0 envelope)
uv run skills/dpia-sentinel/validator/validate.py path/to/dpia-sidecar.json --format json

# Also write the portfolio core-artefact projection
uv run skills/dpia-sentinel/validator/validate.py path/to/dpia-sidecar.json --emit-core-artefact /tmp/core.json

# Run the test suite
uv run --with pytest --with jsonschema python -m pytest skills/dpia-sentinel/tests -q
```

## Rule IDs implemented

| ID | Severity | Category | Checks |
|---|---|---|---|
| SCHEMA-1 | rejection | schema | Sidecar conforms to `dpia-sidecar-schema.json` (Draft 2020-12) |
| COMPLETE-1 | rejection | completeness | A blocking `open_unknowns[]` entry stops the run — a required fact you don't have is a question, never an assumption (SKILL.md "Required facts") |
| CONSEQ-1 | rejection | threshold | `threshold.dpia_required == "no"` contradicts `threshold.criteria_met_count >= 2` (WP248 rev.01's two-criteria rule creates a strong presumption a DPIA IS required) |
| THRESH-1 | rejection | threshold | `threshold.mandatory_trigger == true` requires `dpia_required == "yes"` — an Art. 35(3) mandatory trigger is absolute (SKILL.md Legal Precision Point 1) |
| THRESH-2 | rejection | threshold | `threshold.blacklist_match == true` requires `dpia_required == "yes"` — a national Art. 35(4) blacklist match is also absolute (SKILL.md Legal Precision Point 5) |
| MIT-1 | rejection | handoff | A mitigation with `status == "toms_art32_tracked"` must carry a `toms_art32_ref` — dpia-sentinel never certifies Art. 32 appropriateness, implementation, or effectiveness itself |
| MIT-2 | rejection | handoff | A mitigation's `risk_refs[]` must resolve to an existing `risk_register[].id` — a dangling reference claims to mitigate a risk this DPIA never registered |
| RISK-1 | rejection | risk | A `risk_register[]` entry at `adjusted_level == "Very High"` (not `phase == "inherent"`) with no mitigation naming it in `risk_refs` requires `verdict` to be `CONSULT_SA` or `REJECTED` — never `APPROVED`/`CONDITIONALLY_APPROVED`, and never omitted (references/scoring.md DPIA Verdict + Art. 36) |
| SCORE-1 | rejection | risk | A `risk_register[]` entry's `score` (if given) must equal `likelihood * severity`, and `adjusted_level` may diverge from the raw L×S tier by at most one tier (references/scoring.md Risk Level Matrix + Modulating Factors' documented ±1-tier bound) |
| SRC-1 | warning | freshness | Every on-disk `references/**/*.md` file is declared in `sources.lock.json`, and every declared entry's `last_verified` is within the last 12 months |
| RUNNER-0 | rejection | runner | Guard, not a data rule: `validate()` with an **empty rule registry** fails closed instead of returning a green result — import `dpia_validator.rules` before calling `validate()` |
| CLI-0 | rejection | runner | CLI-only guard (lives in `validate.py` + `runner.load_error_result`, not in `RULES`): the sidecar file couldn't be read or parsed at all (missing, unreadable, invalid UTF-8, invalid JSON) — fails closed with one finding instead of a traceback |

Rule modules: `schema_conformance.py` (SCHEMA-1), `completeness.py`
(COMPLETE-1, CONSEQ-1, THRESH-1, THRESH-2, MIT-1), `risk_register.py`
(RISK-1, SCORE-1, MIT-2), `sources.py` (SRC-1); RUNNER-0 lives in
`runner.py` itself, CLI-0 in `validate.py`/`runner.load_error_result`.

## Findings are the only output — rules never raise

Every rule module takes `(sidecar, ctx)` and **returns** a list of `Finding`
objects; a data defect is reported as a `rejection`/`warning`/`info` finding,
never a raised exception. `validate()` aggregates every rule's findings into
a `Result` whose `status` is `"failed"` if any `rejection` finding is
present, `"passed_with_warnings"` if only `warning`/`info` findings are
present, else `"passed"`.

## Fixtures convention

- `fixtures/must_pass/minimal-clean.json` — a synthetic, schema-valid
  sidecar that satisfies every currently-implemented rule. No real
  organisation or personal data — every name and ref is fictional.
- `fixtures/must_fail/<RULE-ID>__<short-description>.json` — a fixture that
  deliberately violates exactly the named rule.
