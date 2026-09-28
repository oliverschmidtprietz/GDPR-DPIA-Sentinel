# DPIA Sentinel — Changelog

## [v1.14] — 2026-09-24

Portfolio standard adoption (structural tier): validator, sources.lock.json, core
artefact adapter, conformance.json. No change to DPIA methodology or intake.

- **New `references/dpia-sidecar-schema.json`** — the native machine-readable
  sidecar shape (threshold verdict, risk register, mitigations), defined from
  scratch per `docs/standards/PORTFOLIO-STANDARD.md` — this skill had no
  structured output before this release.
- **New `validator/`** — a deterministic structural validator
  (`dpia_validator/`) with 6 rules: `SCHEMA-1` (schema conformance),
  `COMPLETE-1` (a blocking open unknown stops the run), `CONSEQ-1` and
  `THRESH-1` (consequential threshold contradictions — `dpia_required` vs. the
  WP248 two-criteria rule and the Art. 35(3) absolute-trigger rule),
  `MIT-1` (a mitigation claimed as `toms_art32_tracked` must carry a real ref
  — dpia-sentinel never certifies Art. 32 status itself), and `SRC-1`
  (`sources.lock.json` coverage and freshness), plus the `RUNNER-0`
  empty-registry fail-closed guard. `--emit-core-artefact` projects the live
  validation result into the portfolio core artefact
  (`skill-artefact-1.1.schema.json`): `sources[]`, `handoffs[]` and
  `unknowns[]` are all driven by the sidecar's actual content, never a
  hard-coded empty list — a mitigation named with no toms-art32 status
  attached surfaces as an `unknowns[]` entry rather than a silent pass.
- **New `sources.lock.json`** — every `references/**/*.md` file declared,
  with `last_verified` set to that file's own last-modified date (from git
  history); no date invented.
- **New `conformance.json`** — declares `tier: structural`,
  `standard_version: "1.4"`. `scripts/check_conformance.py` reports
  `CONFORMANT dpia-sentinel`.
- **`SKILL.md`** — new "Machine-readable output" section pointing at the
  sidecar + validator.

**Status:** unreviewed — tooling/adoption change; substantive DPIA
methodology, scoring, and jurisdiction analysis unchanged.

---

## [v1.13] — 2026-09-15

Front-door check + enforced intake, fanned out from the GM-008 intake/front-door wave (design spec `docs/superpowers/specs/2026-08-29-gm008-intake-frontdoor-design.md`, decisions D-GM008-01..03), following the pattern proven in `tia` v1.5 and `dpa-art28`'s enforced-intake wording. Light fan-out, author-scoped 2026-08-29 — no journey test.

- **New `## Session Setup` section**, inserted between Routing and Assessment Flow:
  - **Front-door check** — a request carrying GDPR obligations beyond a DPIA (no single deliverable, spans several duties, or asks "are we compliant" / "what do we need to do") routes through `super-gdpr` first when installed; if not installed, the adjacent obligations (Art. 28 contract, transfer assessment, Art. 30 register entry, etc.) are named and the skill proceeds with a bounded DPIA-only answer. A crisp DPIA-only request stays direct-to-skill.
  - **Required facts — ask, never assume.** An ALWAYS-gather fact set for the DPIA threshold and scope (processing description and purposes; data subjects and scale; data categories incl. the special-category screen; new-technology/systematic-monitoring/evaluation-scoring/automated-decision flags; recipients and processors; transfers; retention; existing DPIA or SA blacklist/whitelist match). Rich context upfront is extracted and confirmed back to the user, never silently skipped; a missing fact is asked before the threshold verdict; an unanswerable fact is recorded as an explicit open unknown and reasoned about conditionally.
  - **Special-category free-text screen** — the author-ruled three-part question for free-text/unstructured inputs (which channels; is there an actual control, not just a policy; has special-category content been observed) folded into the data-categories fact, with the rule that an uncontrolled data-subject/staff-facing free-text channel is treated as potentially special-category for the Art. 35(3)(b) / WP248 criterion 4 assessment.
  - **Provenance rule** — a fact is "user-confirmed" only if the user literally stated it; assistant-inferred facts are labelled *inferred*.
- **`## Assessment Flow`** — removed the "if they provide rich context upfront, skip intake questions" escape hatch (the line journey run 1 fell through). The Required facts are now never skipped; rich context only changes ask-sequentially into extract-and-confirm.
- **`evals/evals.json` and `references/`** — reviewed for text encoding the old skip-intake behaviour. No eval assertion rewarded skipping questions (all 8 prompts already supply rich context and are graded on substantive GDPR correctness, not on omitting a confirmation step), so no eval changes were required.

**Status:** unreviewed — behavioural/intake change; substantive DPIA methodology, scoring, and jurisdiction analysis unchanged.

---

## [v1.12] — 2026-08-21

Portfolio-audit fix release (source: `docs/projects/gdpr-skills-marathon/AUDIT-2026-08-19.md`). No change to DPIA methodology, scoring, or jurisdiction analysis.

- **CF-01 — eval 4 graded the wrong AI Act pathway.** The clinical triage AI eval expected "Annex III (medical devices or health)"; AI Act Annex III has no medical-devices/health category. Clinical AI used for diagnosis/triage is high-risk via the Annex I product-safety pathway (Art. 6(1)) as a medical device under the MDR, not via Annex III. Corrected `expected_output` and assertion #7 in `evals/evals.json` (eval id 4) to require the Annex I/MDR pathway.
- **CF-02 — eval 7 asserted an overbroad FRIA obligation.** The private-staffing-agency eval expected a mandatory Art. 27 AI Act FRIA for an Annex III Nr. 4 (employment) deployer. Art. 27 limits the mandatory FRIA to public-law bodies, private providers of public services, and Annex III 5(b)/(c) deployers — a private staffing agency qualifies for none of these. Corrected `expected_output` and the assertions in `evals/evals.json` (eval id 7) to require the DPIA, state the FRIA is NOT mandatory here, and reward explaining why (rewarding a voluntary-FRIA mention without asserting it's required).
- **CF-13 — EDPB 2026 template called "official"/"recognized by all EU SAs" with no consultation caveat.** The template is still adopted for public consultation (per the skill's own Legal Precision Point 13), but the Output Formats instruction and several other surfaces stated recognition unconditionally. Added the same consultation caveat to `SKILL.md` Output Formats, `README.md`, `references/templates.md`, and `docs/portfolio/skill_pages/dpia-sentinel.py`.
- **CF-20 — CHANGELOG entries were out of order.** v1.10 was listed above v1.11, hiding the actual current release. Reordered this file to strict descending version order.
- **CF-22 — portfolio blurb understated jurisdiction coverage.** `docs/portfolio/generate.py`'s landing blurb listed only 4 of the skill's 7 covered jurisdictions (DE, FR, IE, BE) with no qualifier. Updated to list all 7 (DE, FR, IE, BE, NL, IT, PL) plus "and more."
- **CF-23 — undocumented third .docx in `references/`.** `edpb-2026-custom-template-v1.docx` is a real, distinct hybrid draft (EDPB layout + custom 12-section structure) added 2026-05-06 as an intentionally unfinished variant, not a leftover duplicate — its content differs meaningfully from both shipped templates. Not deleted. Documented as an unrouted, unsupported draft in `SKILL.md` Output Formats and `README.md`'s file structure listing, so it can't be mistaken for a supported output.

**Status:** reviewed (carried from v1.11) — audit-fix release; no change to threshold logic, scoring, jurisdiction files, or template population.

---

## [v1.11] — 2026-07-25

Routes Article 32 security-of-processing work to the `toms-art32` skill. Part of the coordinated **sibling-routing pass** (`ropa` v2.15, `dpia-sentinel` v1.11, `dpa-art28` v1.2, `breach-sentinel` v3.3, `tia` v1.3) that closes the toms-art32 portfolio-integration gate recorded as Finding 1 in `docs/projects/gdpr-skills-marathon/ROADMAP-2026-07-25.md`. Routing pointers only — no Article 32 methodology is duplicated into any sibling.

- **Routing table:** new row routing the Art. 32 security measures behind a mitigation to `toms-art32`.
- **Article 32 handoff block.** The DPIA records the measures *envisaged* under Art. 35(7)(d) and the residual risk after them; it does not own them. Appropriateness under Art. 32(1), ownership, implementation status, evidence and effectiveness testing are `toms-art32`'s.
- **Residual-risk discipline.** An Art. 32 measure at status `planned` is not a mitigation in force and must not be imported into the residual-risk calculation as though it were live.
- **Assessment Flow:** Art. 32 boundary note at the mitigations phase — name the measure and its intended risk effect here, grade the control there.

**Status:** reviewed (carried from v1.10) — routing/documentation only; no change to threshold logic, scoring, jurisdiction files or template population.

---

## [v1.10] — 2026-07-21

Digital Omnibus instrument-citation correction + EDPB pseudonymisation-guidelines status correction. Legal-accuracy patch; no change to DPIA methodology, scoring or templates.

- **`references/sources.md` — wrong instrument corrected.** The Digital Omnibus proposal was cited as *COM(2025) 833 final*. The Digital Omnibus package of 19 November 2025 is **COM(2025) 836** (Digital Omnibus on AI, 2025/0359(COD)), **COM(2025) 837** (Digital Omnibus Regulation — data, privacy and cybersecurity, 2025/0360(COD), carrying the GDPR amendments in **Article 3**) and **COM(2025) 838** (European Business Wallets). **No Commission proposal bears the number COM(2025) 833** — EUR-Lex has no `52025PC0833`. The watch-note now cites COM(2025) 837 final, procedure 2025/0360(COD), GDPR amendments at Article 3, with an instrument note and primary-source URL. The substance (Art. 35 not amended; Arts. 30 and 33 re-pivoted onto "high risk") is unchanged.
- **`SKILL.md` Legal Precision Point 10 — draft status restored.** EDPB *Guidelines 01/2025 on Pseudonymisation* were described as "adopted 17 January 2025", which reads as final adoption. They are a **draft**: adopted for public consultation on 16 January 2025, consultation open 17 January – 14 March 2025, **no final version adopted as at July 2026**, and the topic remains on the EDPB Work Programme 2026–2027. The point now says so explicitly and instructs that the guidelines be cited as a draft, never as settled guidance. Verified 2026-07-21 against the EDPB public-consultation register.
- Verified 2026-07-21 against EUR-Lex (CELEX 52025PC0837) and the European Parliament Legislative Train entry for the digital package; corroborated by `data-subject-rights/sources/verification-log.md` §4.1.

**Status:** reviewed (carried from v1.9).

---

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
