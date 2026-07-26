# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate documentation indexes from the front matter of the documents themselves.

Each curated document carries YAML front matter (``title``, ``summary``, ``status``,
``topics``, and an optional ``order``). This tool reads that front matter and rewrites
the generated blocks that depend on it: the document table inside each Diataxis class
index, and the topic listing that groups documents across classes. Hand-written prose
around a generated block is preserved, so an index page stays authored where it should
be and derived where it can be.

Rendering is deterministic, so ``--check`` gates CI against a stale index. The tool also
validates the front matter itself, and ``--nav`` cross-checks a Zensical navigation
against the documents on disk.

The documents are the source of truth. See README.md next to this script for usage.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

BLOCK_PATTERN_TEMPLATE = (
    r"(?P<begin><!-- BEGIN GENERATED: {name} \(gen_doc_index\.py\) -->\n)"
    r"(?P<body>.*?)"
    r"(?P<end><!-- END GENERATED: {name} -->)"
)
TITLE_PATTERN = re.compile(r"^# (.+)$", re.MULTILINE)
TOPIC_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VOCABULARY_PATTERN = re.compile(r"^- `([a-z0-9-]+)`:", re.MULTILINE)
GENERATED_RECORD_PATTERN = re.compile(r"^\d{4}-[a-z0-9-]+\.md$")

STUB_BANNER = "> **Not yet documented in full.**"
SUMMARY_LIMIT = 200

# `status` is a theme-reserved key: a page carrying it gets a marker in site navigation.
# Only a stub declares one, so the marker means "planned" wherever it appears rather than
# decorating every page in the tree.
AUTHORED = "authored"
STUB = "stub"
DEFAULT_ORDER = 100
DEFAULT_EXCLUDES = ("haidra-assets",)
INDEX_NAMES = ("README.md", "index.md")


class DocError(Exception):
    """A document that cannot be indexed as written."""


@dataclass
class Document:
    """One curated document as read from disk."""

    path: Path
    relative: str
    title: str
    summary: str
    status: str
    topics: list[str]
    order: int

    @property
    def class_name(self) -> str:
        return self.relative.split("/")[0]

    @property
    def filename(self) -> str:
        return self.path.name


def parse_front_matter(text: str) -> dict[str, str]:
    """Extract ``key: value`` pairs from a leading YAML front-matter block.

    Values are returned exactly as written, quotes included, because the quoting is
    itself validated: the site's YAML parser rejects an unquoted scalar containing
    ``": "``, and a lenient reader here would accept front matter that renders as
    literal text on the published page.
    """
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def unquote(relative: str, key: str, raw: str) -> str:
    """Return the text of a double-quoted scalar, rejecting anything else.

    Requiring quotes is the whole point: an unquoted YAML scalar holding ``": "`` or
    opening with an indicator character fails to parse, and a failed parse publishes the
    front matter as page content.
    """
    if len(raw) < 2 or not raw.startswith('"') or not raw.endswith('"'):
        raise DocError(f"{relative}: {key} must be a double-quoted string, got {raw}")
    value = raw[1:-1]
    if not value:
        raise DocError(f"{relative}: {key} must not be empty")
    if '"' in value or "\\" in value:
        raise DocError(f"{relative}: {key} must not contain a quote or a backslash")
    return value


def parse_topics(raw: str) -> list[str]:
    inner = raw.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    return [topic.strip().strip("\"'") for topic in inner.split(",") if topic.strip()]


def read_document(path: Path, root: Path) -> Document:
    """Read and validate one curated document.

    Raises ``DocError`` with a message naming the file and the rule it breaks. Every
    rule here exists to stop an index from silently disagreeing with the document it
    points at.
    """
    relative = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8")
    fields = parse_front_matter(text)
    if not fields:
        raise DocError(f"{relative}: missing YAML front matter")

    missing = [key for key in ("title", "summary", "topics") if key not in fields]
    if missing:
        raise DocError(f"{relative}: front matter is missing {', '.join(missing)}")

    title = unquote(relative, "title", fields["title"])
    heading = TITLE_PATTERN.search(text)
    if heading is None:
        raise DocError(f"{relative}: no level-one heading")
    if heading.group(1).strip() != title:
        raise DocError(
            f"{relative}: front-matter title {title!r} does not match heading "
            f"{heading.group(1).strip()!r}",
        )

    summary = unquote(relative, "summary", fields["summary"])
    if len(summary) > SUMMARY_LIMIT:
        raise DocError(f"{relative}: summary is {len(summary)} characters, limit is {SUMMARY_LIMIT}")
    if "—" in summary or "—" in title:
        raise DocError(f"{relative}: em dash in front matter")

    declared = fields.get("status")
    if declared is not None and declared != STUB:
        raise DocError(f"{relative}: status {declared!r} is not {STUB}; omit the key for an authored document")
    status = declared or AUTHORED
    has_banner = STUB_BANNER in text
    if status == STUB and not has_banner:
        raise DocError(f"{relative}: status is {STUB} but the body carries no stub banner")
    if status == AUTHORED and has_banner:
        raise DocError(f"{relative}: the body carries a stub banner but the front matter has no status: {STUB}")

    topics = parse_topics(fields["topics"])
    if not topics:
        raise DocError(f"{relative}: topics is empty")
    bad_topics = [topic for topic in topics if not TOPIC_PATTERN.match(topic)]
    if bad_topics:
        raise DocError(f"{relative}: topics must be lowercase kebab-case, got {', '.join(bad_topics)}")

    raw_order = fields.get("order", str(DEFAULT_ORDER))
    if not raw_order.isdigit():
        raise DocError(f"{relative}: order {raw_order!r} is not a non-negative integer")

    return Document(
        path=path,
        relative=relative,
        title=title,
        summary=summary,
        status=status,
        topics=sorted(topics),
        order=int(raw_order),
    )


def discover(root: Path, excludes: tuple[str, ...]) -> tuple[dict[str, Path], list[Document]]:
    """Find the class indexes and the curated documents underneath them.

    A documentation class is any directory under ``root`` holding a ``README.md``. The
    decision records are excluded by construction: they index themselves through
    ``index.md`` and enter navigation only through that page.
    """
    indexes: dict[str, Path] = {}
    documents: list[Document] = []
    errors: list[str] = []
    for index_path in sorted(root.glob("*/README.md")):
        class_dir = index_path.parent
        if class_dir.name in excludes:
            continue
        indexes[class_dir.name] = index_path
        for doc_path in sorted(class_dir.glob("*.md")):
            if doc_path.name in INDEX_NAMES:
                continue
            try:
                documents.append(read_document(doc_path, root))
            except DocError as error:
                errors.append(str(error))
    if errors:
        raise DocError("\n".join(errors))
    return indexes, documents


def sort_key(document: Document) -> tuple[int, str]:
    return (document.order, document.title)


def render_class_table(documents: list[Document]) -> str:
    """Render the document table for one class, authored documents ahead of stubs."""
    authored = sorted((doc for doc in documents if doc.status == "authored"), key=sort_key)
    planned = sorted((doc for doc in documents if doc.status == "stub"), key=sort_key)

    lines: list[str] = []
    if authored:
        lines += ["| Document | Summary |", "| --- | --- |"]
        lines += [f"| [{doc.title}]({doc.filename}) | {doc.summary} |" for doc in authored]
    if planned:
        if authored:
            lines.append("")
        lines += [
            "### Planned",
            "",
            "Not yet documented in full. Each page describes its subsystem briefly and names",
            "the code that holds the behavior.",
            "",
            "| Document | Scope |",
            "| --- | --- |",
        ]
        lines += [f"| [{doc.title}]({doc.filename}) | {doc.summary} |" for doc in planned]
    if not lines:
        lines.append("No documents yet.")
    return "\n".join(lines) + "\n"


def render_topics(documents: list[Document], class_titles: dict[str, str]) -> str:
    """Render the cross-class topic listing."""
    by_topic: dict[str, list[Document]] = {}
    for document in documents:
        for topic in document.topics:
            by_topic.setdefault(topic, []).append(document)

    lines: list[str] = []
    for topic in sorted(by_topic):
        lines += [f"### {topic}", ""]
        for document in sorted(by_topic[topic], key=lambda doc: (doc.class_name, *sort_key(doc))):
            label = class_titles.get(document.class_name, document.class_name.title())
            suffix = "" if document.status == "authored" else " (planned)"
            lines.append(f"- {label}: [{document.title}]({document.relative}){suffix}")
        lines.append("")
    if not lines:
        return "No topics yet.\n"
    return "\n".join(lines).rstrip("\n") + "\n"


def check_vocabulary(topics_path: Path, documents: list[Document]) -> list[str]:
    """Report topics used by a document that the topics page does not define.

    The topics page defines each tag in a ``- `name`: meaning`` line. Requiring a
    definition before a tag can be used is what keeps the tag set from splintering into
    near-duplicates as documents are added.
    """
    if not topics_path.exists():
        return []
    vocabulary = set(VOCABULARY_PATTERN.findall(topics_path.read_text(encoding="utf-8")))
    if not vocabulary:
        return []
    problems: list[str] = []
    for document in documents:
        for topic in sorted(set(document.topics) - vocabulary):
            problems.append(f"{document.relative}: topic {topic!r} is not defined in {topics_path.name}")
    for topic in sorted(vocabulary - {topic for document in documents for topic in document.topics}):
        problems.append(f"{topics_path.name}: topic {topic!r} is defined but used by no document")
    return problems


def render_document_topics(document: Document) -> str:
    """Render one document's own topic line, linking each topic into the topics page."""
    depth = document.relative.count("/")
    prefix = "../" * depth
    links = ", ".join(f"[{topic}]({prefix}topics.md#{topic})" for topic in document.topics)
    return f"Topics: {links}\n"


def splice(path: Path, name: str, body: str) -> str:
    """Return ``path``'s text with the named generated block replaced by ``body``."""
    pattern = re.compile(BLOCK_PATTERN_TEMPLATE.format(name=name), re.DOTALL)
    text = path.read_text(encoding="utf-8")
    match = pattern.search(text)
    if match is None:
        raise DocError(f"{path}: no generated block named {name!r}")
    return text[: match.start("body")] + body + text[match.end("body") :]


def splice_or_insert(path: Path, name: str, body: str) -> str:
    """Splice the named block, inserting it below the level-one heading if it is absent.

    Inserting rather than failing means a new document needs no boilerplate: write the
    front matter and the heading, run the tool, and the topic line appears.
    """
    text = path.read_text(encoding="utf-8")
    if f"BEGIN GENERATED: {name} " in text:
        return splice(path, name, body)
    heading = TITLE_PATTERN.search(text)
    if heading is None:
        raise DocError(f"{path}: no level-one heading to insert the {name!r} block below")
    block = (
        f"\n\n<!-- BEGIN GENERATED: {name} (gen_doc_index.py) -->\n{body}<!-- END GENERATED: {name} -->"
    )
    return text[: heading.end()] + block + text[heading.end() :]


def flatten_nav(entry: object, found: list[str]) -> None:
    if isinstance(entry, str):
        found.append(entry)
    elif isinstance(entry, list):
        for item in entry:
            flatten_nav(item, found)
    elif isinstance(entry, dict):
        for value in entry.values():
            flatten_nav(value, found)


def check_nav(nav_path: Path, root: Path, indexes: dict[str, Path], documents: list[Document]) -> list[str]:
    """Report navigation drift against the documents on disk.

    Navigation is curated: order and display titles are editorial choices this tool does
    not make. What it does enforce is that navigation and the tree agree on membership,
    and that a generated corpus enters navigation only through its index page.
    """
    config = tomllib.loads(nav_path.read_text(encoding="utf-8"))
    entries: list[str] = []
    flatten_nav(config.get("project", {}).get("nav", []), entries)

    problems: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        if not (root / entry).exists():
            problems.append(f"{nav_path.name}: nav entry {entry} does not exist")
        if entry in seen:
            problems.append(f"{nav_path.name}: nav entry {entry} appears more than once")
        seen.add(entry)
        if GENERATED_RECORD_PATTERN.match(Path(entry).name):
            problems.append(
                f"{nav_path.name}: nav entry {entry} is a generated record; "
                "reach records through their index page instead",
            )

    required = {index.relative_to(root).as_posix() for index in indexes.values()}
    required |= {document.relative for document in documents}
    required |= {path.name for path in root.glob("*.md")}
    for entry in sorted(required - seen):
        problems.append(f"{nav_path.name}: {entry} is not in nav")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("docs_dir", type=Path, help="Documentation root, normally docs/")
    parser.add_argument(
        "--topics",
        type=Path,
        default=None,
        help="Page holding the topics block (default: topics.md inside the documentation root)",
    )
    parser.add_argument(
        "--nav",
        type=Path,
        default=None,
        help="Zensical configuration to cross-check navigation against the tree",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        help=f"Directory name to skip, repeatable (default: {', '.join(DEFAULT_EXCLUDES)})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if any generated block is out of date instead of writing",
    )
    args = parser.parse_args(argv)

    root: Path = args.docs_dir
    excludes = tuple(args.exclude) if args.exclude else DEFAULT_EXCLUDES

    try:
        indexes, documents = discover(root, excludes)
    except DocError as error:
        print(error, file=sys.stderr)
        return 1
    if not documents:
        print(f"No curated documents found under {root}", file=sys.stderr)
        return 1

    class_titles = {name: (label := name.replace("_", " "))[:1].upper() + label[1:] for name in indexes}
    topics_path = args.topics or root / "topics.md"
    problems = check_vocabulary(topics_path, documents)

    pending: list[tuple[Path, str]] = []
    try:
        for class_name, index_path in sorted(indexes.items()):
            body = render_class_table([doc for doc in documents if doc.class_name == class_name])
            pending.append((index_path, splice(index_path, "documents", body)))
        pending.append((topics_path, splice(topics_path, "topics", render_topics(documents, class_titles))))
        for document in documents:
            pending.append(
                (document.path, splice_or_insert(document.path, "topics", render_document_topics(document))),
            )
    except DocError as error:
        print(error, file=sys.stderr)
        return 1

    if args.nav is not None:
        problems += check_nav(args.nav, root, indexes, documents)

    if args.check:
        for path, rendered in pending:
            if path.read_text(encoding="utf-8") != rendered:
                problems.append(f"{path} is out of date; regenerate with gen_doc_index.py")
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        return 0

    if problems:
        print("\n".join(problems), file=sys.stderr)
    for path, rendered in pending:
        path.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote {len(pending)} generated blocks from {len(documents)} documents")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
