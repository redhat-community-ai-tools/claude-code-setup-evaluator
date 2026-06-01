from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvaluatorConfig:
    extends: str = "recommended"
    rules: dict[str, str | list] = field(default_factory=dict)
    ignore: list[str] = field(default_factory=list)


@dataclass
class ResolvedConfig:
    rules: dict[str, str | list] = field(default_factory=dict)
    ignore: list[str] = field(default_factory=list)
    preset_name: str = "recommended"
