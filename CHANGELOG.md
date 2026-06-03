# DPIA Sentinel — Changelog

## [v1.9] — 2026-05-31

Regulatory-horizon note (no change to DPIA methodology).

- **Digital Omnibus (PROPOSED).** `references/sources.md` gains a watch-note: the Commission's Digital Omnibus (COM(2025) 833 final, 19 Nov 2025) does not amend Art. 35, but re-pivots GDPR record-keeping (Art. 30) and SA breach-notification (Art. 33) onto the "high risk" concept — raising the downstream stakes of a DPIA's Art. 35 high-risk determination. Flagged not-in-force. (The EDPB 2026 DPIA template was already integrated via the `edpb-2026-*` references.)

**Status:** reviewed (carried from v1.8).

---

## [v1.8] — 2026-05-14

First **reviewed** release. Eval pass via `/skill-creator` confirmed skill value against no-skill baseline.

- 8 realistic test cases run with-skill vs no-skill baseline (72 assertions total)
- Result: 71/72 (98.6%) with skill vs 70/72 (97.2%) without
- Diagnostic finding: skill earned its keep on the truly discriminative assertion (Art. 35(3) absolute triggers vs nine-criteria analysis) — the baseline collapsed into nine-criteria framing on facial-recognition CCTV, the skill correctly stated triggers are absolute
- The narrow numeric differential reflects assertion-bank ceiling effects against a strong GDPR-savvy baseline, not a skill weakness; iteration-2 will harden the assertion bank with discriminative items
- Eval-assertion bug noted (Case 3 Lead SA framing — Art. 56(1) follows controller's main establishment, not data-subject location) and queued for iteration-2 fix
- See `../../dpia-sentinel-workspace/iteration-1/` for full eval artifacts

## [v1.7] — 2026-04-21

- Add custom 12-section DPIA template .docx (`dpia-custom-template-v1.docx`) as populatable base document
- Add `dpia-custom-population.md` — population guide mapping all 21 tables + narrative placeholders to assessment data
- Custom format now uses same template population workflow as EDPB format (unpack → fill → repack) for consistent styling
- Both document generation paths (EDPB 2026 + custom) now produce visually consistent output across runs

## [v1.6] — 2026-04-14

- Add official EDPB template .docx (`edpb-2026-template-v1.docx`) as populatable base document
- Add `edpb-2026-population.md` — table-by-table population guide mapping all 35 tables + 13 placeholders to assessment data
- EDPB 2026 output now uses template population workflow (unpack → fill → repack) instead of from-scratch generation
- Update SKILL.md routing and templates.md for population-based EDPB document generation

## [v1.5] — 2026-04-09

- Add EDPB 2026 DPIA Template (v1.0, 10 March 2026) as new output format (Sections 0–6)
- Adopt inherent/residual risk terminology throughout (replacing pre-/post-mitigation)
- Add modulating factors to risk assessment (aggravating/mitigating contextual adjusters)
- Add two-track risk model: Track A (inherent-by-design) + Track B (operational)
- Add implementation status tiers for all measures (Planned / Partially Implemented / Implemented)
- Add four-outcome DPIA verdict (APPROVED / CONDITIONALLY APPROVED / CONSULT SA / REJECTED)
- Add asset inventory step to assessment flow (EDPB Section 1.3)
- Split necessity and proportionality into separate upstream assessment gates
- New reference: `edpb-2026-template.md` — field-by-field EDPB template specification
- New reference: `edpb-2026-explainer.md` — distilled EDPB methodology guidance
- Tag all risk catalog entries with Track A/B labels and modulating factor suggestions
- Add standard Track B operational scenarios to all processing-specific risk profiles
- Update risk register table format: added Track, Modulating Factors, and Status columns

## [v1.0] — 2026-02-10

- Initial release: threshold assessment, multi-jurisdictional blacklist analysis (7 EU jurisdictions), 5×5 risk scoring, EDPB AI opinion integration, 4 document templates, whitelists for FR/CZ/ES/AT
