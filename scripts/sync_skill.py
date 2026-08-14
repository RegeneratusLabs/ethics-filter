#!/usr/bin/env python3
"""Sync the Hermes plugin bundle and (optionally) the local Hermes skill from
canonical sources.

Canonical sources:
  SKILL.md                       -> the portable skill definition
  ethics_filter/modules/*.md     -> module rubrics
  ethics_filter/constitution/templates.json
  references/*.md                -> skill reference docs
  ethics_filter/*.py             -> vendored engine for the plugin

Targets:
  plugin/skills/ethics-filter/   (always — the plugin's bundled skill)
  plugin/ethics_filter/          (always — vendored engine so the plugin is
                                 self-contained without pip install)
  ~/.hermes/skills/ethics-filter (with --hermes)

Usage:
  python scripts/sync_skill.py [--hermes] [--check]
  --check: fail if any target file differs from canonical (CI gate)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HERMES_SKILL = Path.home() / ".hermes" / "skills" / "ethics-filter"

CANONICAL_FILES = [
    ("SKILL.md", "SKILL.md"),
    ("ethics_filter/modules/environmental.md", "modules/environmental.md"),
    ("ethics_filter/modules/fairness.md", "modules/fairness.md"),
    ("ethics_filter/modules/transparency.md", "modules/transparency.md"),
    ("ethics_filter/modules/conscious-leadership.md", "modules/conscious-leadership.md"),
    ("ethics_filter/modules/ethical-framework.md", "modules/ethical-framework.md"),
    ("ethics_filter/modules/compliance.md", "modules/compliance.md"),
    ("ethics_filter/constitution/templates.json", "constitution/templates.json"),
]

# reference files copied into the skill bundle (if present)
REFERENCE_GLOBS = ["*.md"]

PLUGIN_ENGINE_FILES = [
    "ethics_filter/__init__.py",
    "ethics_filter/engine.py",
    "ethics_filter/cli.py",
    "ethics_filter/mcp_server.py",
]

PLUGIN_ENGINE_DATA = [
    "ethics_filter/modules/environmental.md",
    "ethics_filter/modules/fairness.md",
    "ethics_filter/modules/transparency.md",
    "ethics_filter/modules/conscious-leadership.md",
    "ethics_filter/modules/ethical-framework.md",
    "ethics_filter/modules/compliance.md",
    "ethics_filter/constitution/templates.json",
]


def _same(a: Path, b: Path) -> bool:
    return a.exists() and b.exists() and a.read_bytes() == b.read_bytes()


# In a skill bundle the linked_files paths are relative to the bundle's own
# SKILL.md, so the canonical "ethics_filter/modules/..." prefixes must be
# rewritten to the bundle's local "modules/..." layout.
SKILL_LINKED_REWRITES = [
    ("ethics_filter/modules/", "modules/"),
    ("ethics_filter/constitution/", "constitution/"),
]


def transform_skill(text: str) -> str:
    for old, new in SKILL_LINKED_REWRITES:
        text = text.replace(old, new)
    return text


def sync_file(
    src: Path,
    dst: Path,
    check: bool,
    changed: list[str],
    transform=None,
) -> None:
    src_bytes = src.read_bytes()
    if transform:
        src_bytes = transform(src_bytes.decode("utf-8")).encode("utf-8")
    if check:
        if not (dst.exists() and dst.read_bytes() == src_bytes):
            print(f"DRIFT: {dst.relative_to(REPO)} differs from canonical")
            sys.exit(1)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not (dst.exists() and dst.read_bytes() == src_bytes):
        dst.write_bytes(src_bytes)
        label = dst.relative_to(REPO) if REPO in dst.parents else dst
        changed.append(str(label))


def sync_skill_bundle(target: Path, check: bool, changed: list[str]) -> None:
    for src_rel, dst_rel in CANONICAL_FILES:
        transform = transform_skill if dst_rel == "SKILL.md" else None
        sync_file(REPO / src_rel, target / dst_rel, check, changed, transform)
    # references
    refs_dir = REPO / "references"
    if refs_dir.exists():
        for ref in sorted(refs_dir.glob("*.md")):
            sync_file(ref, target / "references" / ref.name, check, changed)


def sync_plugin(check: bool, changed: list[str]) -> None:
    bundle = REPO / "plugin" / "skills" / "ethics-filter"
    sync_skill_bundle(bundle, check, changed)
    # vendored engine
    for src_rel in PLUGIN_ENGINE_FILES + PLUGIN_ENGINE_DATA:
        sync_file(REPO / src_rel, REPO / "plugin" / src_rel, check, changed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hermes", action="store_true",
                        help="Also sync the local ~/.hermes skill")
    parser.add_argument("--check", action="store_true",
                        help="Verify targets match canonical; exit 1 on drift")
    args = parser.parse_args()

    changed: list[str] = []
    sync_plugin(args.check, changed)

    if args.hermes:
        sync_skill_bundle(HERMES_SKILL, args.check, changed)
        # preserve the local skill's extra references by copying all refs
        refs_dir = REPO / "references"
        if refs_dir.exists():
            for ref in sorted(refs_dir.glob("*.md")):
                sync_file(ref, HERMES_SKILL / "references" / ref.name, args.check, changed)

    if args.check:
        print("Sync check passed: all targets match canonical.")
        return 0

    if changed:
        print(f"Synced {len(changed)} file(s):")
        for c in changed:
            print(f"  + {c}")
    else:
        print("All targets up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
