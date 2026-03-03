"""
skills_engine/skill.py
Skill dataclass — represents a loaded, parsed skill file.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SkillScript:
    """A companion script bundled with a skill (e.g. ADD.py, build.sh)."""

    name: str
    """Filename, e.g. 'ADD.py'."""

    path: Path
    """Absolute path to the script on disk."""

    language: str
    """'python' | 'bash' | 'other'"""

    content: str = ""
    """Raw file content (populated by the loader)."""

    @property
    def is_python(self) -> bool:
        return self.language == "python"

    @property
    def is_bash(self) -> bool:
        return self.language == "bash"


@dataclass
class Skill:
    """
    A fully loaded skill.

    Skills are the reusable capability building blocks referenced in SOP steps.
    Each skill is backed by a ``SKILL.md`` file (and optional companion scripts)
    on disk.
    """

    name: str
    """Logical skill name, e.g. 'triage' or 'developer'."""

    path: Path
    """Path to the SKILL.md file."""

    raw_markdown: str
    """Full contents of the SKILL.md file."""

    scripts: list[SkillScript] = field(default_factory=list)
    """Companion scripts discovered in the same directory."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """
    Parsed front-matter or extracted metadata, e.g.:
      {
        "purpose": "...",
        "trigger": "...",
        "inputs": [...],
        "outputs": [...],
      }
    """

    _version: int = field(default=0, repr=False)
    """Hot-reload version counter. Incremented each time the file is reloaded."""

    # ── Helpers ───────────────────────────────────────────────────────────────

    @property
    def purpose(self) -> str:
        return self.metadata.get("purpose", "")

    @property
    def trigger(self) -> str:
        return self.metadata.get("trigger", "")

    @property
    def system_prompt(self) -> str:
        """
        Return the skill content formatted as a system prompt fragment.
        Agents prepend this to the LLM context when the skill is active.
        """
        return f"## Skill: {self.name}\n\n{self.raw_markdown}"

    def get_script(self, name: str) -> SkillScript | None:
        """Return the script with *name*, or None if not found."""
        return next((s for s in self.scripts if s.name == name), None)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict for logging."""
        return {
            "name": self.name,
            "path": str(self.path),
            "scripts": [s.name for s in self.scripts],
            "version": self._version,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"Skill(name={self.name!r}, scripts={[s.name for s in self.scripts]})"
