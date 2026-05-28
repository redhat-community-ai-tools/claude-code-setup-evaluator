#!/usr/bin/env python3
"""Configuration models and utilities for ai-workspace."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


class FeaturesConfig(BaseModel):
    """Feature flags for workspace capabilities."""

    agent_docs: bool = Field(
        default=True,
        description="Enable agent-docs system. WARNING: Disabling removes agent-docs/ if empty",
    )
    skills: bool = Field(
        default=True,
        description="Enable skills system. WARNING: Disabling removes skills/ if empty",
    )
    commands: bool = Field(
        default=True,
        description="Enable commands system. WARNING: Disabling removes commands/ if empty",
    )


class RepositoriesConfig(BaseModel):
    """Repository status and sync configuration."""

    include_workspace_root: bool = Field(
        default=False,
        description="Include the workspace root repository in session status reporting",
    )


class DistributionConfig(BaseModel):
    """Distribution paths for skills and commands."""

    skills_paths: list[str] = Field(
        default=[],
        description="Target directories for skills symlinks. Must be explicitly configured.",
    )
    commands_paths: list[str] = Field(
        default=[],
        description="Target directories for commands. Must be explicitly configured.",
    )
    commands_overrides: dict[str, str] = Field(
        default={},
        description=(
            "Override the distribution method for specific command paths. "
            "Keys are paths from commands_paths, values are distribution methods. "
            "Valid methods: 'symlink' (default for all paths), 'strip_frontmatter'. "
            "Overrides for paths not yet in commands_paths are silently kept for future use."
        ),
    )


class ToolsConfig(BaseModel):
    """Tool discovery configuration."""

    show_unavailable: bool = Field(
        default=False,
        description="Show all tools with availability status (False = only available)",
    )


class AIWorkspaceConfig(BaseModel):
    """Root configuration model for ai-workspace.toml."""

    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    repositories: RepositoriesConfig = Field(default_factory=RepositoriesConfig)
    distribution: DistributionConfig = Field(default_factory=DistributionConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)


def load_config(config_path: Path) -> AIWorkspaceConfig:
    """Load and validate configuration from ai-workspace.toml."""
    if not config_path.exists():
        return AIWorkspaceConfig()

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    return AIWorkspaceConfig.model_validate(data)
