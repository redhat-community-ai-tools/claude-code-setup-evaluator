from __future__ import annotations

from pathlib import Path

import yaml

from the_evaluator.config.presets import PRESETS
from the_evaluator.config.types import ResolvedConfig


def load_config(
    scan_path: str | None = None,
    preset_override: str | None = None,
    config_file: str | None = None,
) -> ResolvedConfig:
    """Load and resolve evaluation config.

    Resolution order:
    1. Start with recommended preset (default)
    2. If .evaluator.yaml exists, apply extends + rules
    3. If --preset CLI flag is passed, it overrides extends
    """
    raw_extends = "recommended"
    raw_rules: dict[str, str | list] = {}
    raw_ignore: list[str] = []

    if config_file:
        cfg_path = Path(config_file)
    elif scan_path:
        cfg_path = Path(scan_path) / ".evaluator.yaml"
    else:
        cfg_path = None

    if cfg_path and cfg_path.exists():
        with open(cfg_path) as f:
            raw = yaml.safe_load(f) or {}
        raw_extends = raw.get("extends", "recommended")
        raw_rules = raw.get("rules", {})
        raw_ignore = raw.get("ignore", [])

    if preset_override:
        raw_extends = preset_override

    if raw_extends not in PRESETS:
        raw_extends = "recommended"

    base_rules = dict(PRESETS[raw_extends])
    base_rules.update(raw_rules)

    return ResolvedConfig(
        rules=base_rules,
        ignore=raw_ignore,
        preset_name=raw_extends,
    )
