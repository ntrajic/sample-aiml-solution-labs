"""
skills_engine/loader.py
Skill loader with optional hot-reload via watchfiles.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Callable

import structlog
from watchfiles import awatch

from skills_engine.skill import Skill, SkillScript

logger = structlog.get_logger(__name__)

_SCRIPT_SUFFIXES: dict[str, str] = {
    ".py": "python",
    ".sh": "bash",
}

# Regex to extract the first heading from a SKILL.md
_HEADING_RE = re.compile(r"^#\s+SKILL:\s*(.+)$", re.MULTILINE)
# Simple section extractor: ## Purpose, ## Trigger
_SECTION_RE = re.compile(r"^##\s+(.+)\n(.*?)(?=^##|\Z)", re.MULTILINE | re.DOTALL)


class SkillLoader:
    """
    Discovers, parses, and caches skill files from a directory on disk.

    Usage::

        loader = SkillLoader(skills_dir=Path("skills"))
        loader.load_all()
        triage = loader.get("triage")

    Hot-reload::

        async def main():
            loader = SkillLoader(Path("skills"))
            loader.load_all()
            await loader.watch()  # blocks; reloads skills on file change
    """

    def __init__(
        self,
        skills_dir: Path,
        *,
        on_reload: Callable[[Skill], None] | None = None,
    ) -> None:
        self._dir = skills_dir
        self._cache: dict[str, Skill] = {}
        self._on_reload = on_reload
        self._log = logger.bind(loader="SkillLoader", dir=str(skills_dir))

    # ── Public API ────────────────────────────────────────────────────────────

    def load_all(self) -> dict[str, Skill]:
        """
        Scan *skills_dir* for ``*SKILL*.md`` files and load each one.
        Returns the full skill cache.
        """
        if not self._dir.exists():
            self._log.warning("skills_dir.missing", path=str(self._dir))
            return {}

        for path in sorted(self._dir.glob("**/*SKILL*.md")):
            self._load_file(path)

        self._log.info("skills.loaded", count=len(self._cache))
        return dict(self._cache)

    def get(self, name: str) -> Skill | None:
        """Return the skill with logical *name*, or None."""
        return self._cache.get(name.lower())

    def get_or_raise(self, name: str) -> Skill:
        skill = self.get(name)
        if skill is None:
            raise KeyError(f"Skill {name!r} not found. Available: {list(self._cache)}")
        return skill

    def list_skills(self) -> list[str]:
        return sorted(self._cache.keys())

    async def watch(self) -> None:
        """
        Watch *skills_dir* for changes and hot-reload affected skills.
        This coroutine runs indefinitely — cancel it to stop watching.
        """
        self._log.info("skills.watching")
        async for changes in awatch(self._dir):
            for _change_type, path_str in changes:
                path = Path(path_str)
                if "SKILL" in path.name and path.suffix == ".md":
                    self._log.info("skill.file_changed", path=path_str)
                    skill = self._load_file(path)
                    if skill and self._on_reload:
                        self._on_reload(skill)
            await asyncio.sleep(0)  # yield to event loop

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load_file(self, path: Path) -> Skill | None:
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            self._log.warning("skill.read_error", path=str(path), error=str(exc))
            return None

        name = self._derive_name(raw, path)
        metadata = self._extract_metadata(raw)
        scripts = self._discover_scripts(path.parent)

        existing = self._cache.get(name)
        version = (existing._version + 1) if existing else 0

        skill = Skill(
            name=name,
            path=path,
            raw_markdown=raw,
            scripts=scripts,
            metadata=metadata,
            _version=version,
        )
        self._cache[name] = skill
        self._log.debug("skill.loaded", name=name, version=version)
        return skill

    @staticmethod
    def _derive_name(raw: str, path: Path) -> str:
        """Extract skill name from the first ``# SKILL: <name>`` heading."""
        match = _HEADING_RE.search(raw)
        if match:
            return match.group(1).strip().lower().replace(" ", "_")
        # Fall back to the filename stem, e.g. TRIAGE_SKILL.md → triage
        return path.stem.replace("_SKILL", "").lower()

    @staticmethod
    def _extract_metadata(raw: str) -> dict[str, str]:
        """Extract ``## Section`` content as a dict."""
        meta: dict[str, str] = {}
        for match in _SECTION_RE.finditer(raw):
            key = match.group(1).strip().lower().replace(" ", "_")
            value = match.group(2).strip()
            meta[key] = value
        return meta

    @staticmethod
    def _discover_scripts(directory: Path) -> list[SkillScript]:
        """Find companion .py and .sh files in the same directory as the skill."""
        scripts: list[SkillScript] = []
        for path in sorted(directory.iterdir()):
            language = _SCRIPT_SUFFIXES.get(path.suffix)
            if language:
                try:
                    content = path.read_text(encoding="utf-8")
                except OSError:
                    content = ""
                scripts.append(
                    SkillScript(name=path.name, path=path, language=language, content=content)
                )
        return scripts
