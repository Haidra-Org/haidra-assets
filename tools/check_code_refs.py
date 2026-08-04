# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify that repository paths cited in documentation exist.

Documentation that cites code paths rots silently when files move. This tool
extracts backticked repository paths from Markdown files (for example
``horde/database/kudos_ledger.py`` or ``sql_statements/5.1.0.txt``) and fails
if any cited path does not exist relative to the repository root, turning doc
rot into a CI failure.

A citation is any backticked token that starts with one of the repository's
top-level directories and names a file with an extension. Paths inside fenced
code blocks are ignored: fences hold illustrative code, prose holds claims.
See README.md next to this script for usage.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CITATION_PATTERN = re.compile(r"`([A-Za-z0-9_./-]+\.[A-Za-z0-9_]+)(?::\d+(?:-\d+)?)?`")
FENCE_PATTERN = re.compile(r"^(```|~~~)")


def iter_markdown_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
        elif path.suffix == ".md":
            files.append(path)
    return files


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Lines of a Markdown document outside fenced code blocks, 1-indexed."""
    lines: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE_PATTERN.match(line.strip()):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append((number, line))
    return lines


def find_missing(doc_paths: list[Path], repo_root: Path, roots: set[str]) -> list[tuple[Path, int, str]]:
    missing: list[tuple[Path, int, str]] = []
    for doc in iter_markdown_files(doc_paths):
        for number, line in prose_lines(doc.read_text(encoding="utf-8")):
            for cited in CITATION_PATTERN.findall(line):
                top = cited.split("/", 1)[0]
                if "/" not in cited or top not in roots:
                    continue
                if not (repo_root / cited).exists():
                    missing.append((doc, number, cited))
    return missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("docs", nargs="+", type=Path, help="Markdown files or directories to scan")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root that cited paths are relative to (default: current directory)",
    )
    parser.add_argument(
        "--roots",
        default="horde,tools,tests,sql_statements,docs",
        help="Comma-separated top-level directories that mark a token as a repository path",
    )
    args = parser.parse_args(argv)

    roots = {root.strip() for root in args.roots.split(",") if root.strip()}
    missing = find_missing(args.docs, args.repo_root, roots)
    if missing:
        for doc, number, cited in missing:
            print(f"{doc}:{number}: cited path does not exist: {cited}", file=sys.stderr)
        print(f"{len(missing)} stale citation(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
