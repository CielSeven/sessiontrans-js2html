"""Apply text masks to redact sensitive information."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class MaskRule:
    pattern: str
    replacement: str


def load_masks(path: str | Path) -> list[MaskRule]:
    rules: list[MaskRule] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if " -> " not in line:
            continue
        pattern, replacement = line.split(" -> ", 1)
        rules.append(MaskRule(pattern=pattern.strip(), replacement=replacement.strip()))
    # Sort longest patterns first so more specific rules match before general ones
    rules.sort(key=lambda r: len(r.pattern), reverse=True)
    return rules


def apply_masks(text: str, rules: list[MaskRule]) -> str:
    for rule in rules:
        text = text.replace(rule.pattern, rule.replacement)
    return text
