"""Finding dataclass — a single validator output entry.

Severity is the GATE ("does this stop the job?"), gate vocabulary
rejection|warning|info (portfolio findings-report 2.0). This axis is the
deterministic validator's own diagnostics about the SIDECAR FILE only — it is
never applied to a DPIA's own substantive risk register (Likelihood x
Severity, Low/Medium/High/Very High per references/scoring.md), which keeps
its own vocabulary untouched (D-WS3-03 split, carried from toms-art32).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass(frozen=True)
class Finding:
    rule_id: str
    category: str
    severity: str             # "rejection" | "warning" | "info"
    message: str
    spec_anchor: str
    priority: Optional[str] = None      # "high" | "medium" | "low"
    entry_type: Optional[str] = None
    entry_id: Optional[str] = None
    field: Optional[str] = None
    fix_hint: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}
