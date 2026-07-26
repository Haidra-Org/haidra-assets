# SPDX-FileCopyrightText: 2026 Tazlin
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Behavior of the documentation index generator."""

from __future__ import annotations

from pathlib import Path

import gen_doc_index
import pytest

CLASS_INDEX = """# {title}

Hand-written framing that the generator must leave alone.

## Documents

<!-- BEGIN GENERATED: documents (gen_doc_index.py) -->
<!-- END GENERATED: documents -->

## Afterword

Hand-written closing that the generator must leave alone.
"""

TOPICS_PAGE = """# Topics

## Vocabulary

- `alpha`: the first subject.
- `beta`: the second subject.

## By topic

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
<!-- END GENERATED: topics -->
"""

NAV_TEMPLATE = """[project]
site_name = "Test"
nav = [
{entries}
]
"""

STUB_BANNER_BODY = f"{gen_doc_index.STUB_BANNER} Scope only.\n"


def write_doc(
    directory: Path,
    slug: str,
    *,
    title: str,
    summary: str = "A one-line summary.",
    status: str | None = None,
    topics: str = "[alpha]",
    order: int | None = None,
    heading: str | None = None,
    body: str = "Body text.\n",
    quoted: bool = True,
) -> Path:
    quote = '"' if quoted else ""
    status_line = f"status: {status}\n" if status is not None else ""
    order_line = f"order: {order}\n" if order is not None else ""
    path = directory / f"{slug}.md"
    path.write_text(
        f"---\ntitle: {quote}{title}{quote}\nsummary: {quote}{summary}{quote}\n"
        f"{status_line}topics: {topics}\n{order_line}---\n\n"
        f"# {heading or title}\n\n{body}",
        encoding="utf-8",
        newline="\n",
    )
    return path


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A minimal documentation root with two classes and one document each."""
    root = tmp_path / "docs"
    for class_name, title in (("reference", "Reference"), ("how-to", "How-to")):
        class_dir = root / class_name
        class_dir.mkdir(parents=True)
        (class_dir / "README.md").write_text(CLASS_INDEX.format(title=title), encoding="utf-8", newline="\n")
    (root / "topics.md").write_text(TOPICS_PAGE, encoding="utf-8", newline="\n")
    write_doc(root / "reference", "widgets", title="Widgets", topics="[alpha, beta]")
    write_doc(root / "how-to", "replace_a_widget", title="Replace a widget", topics="[beta]")
    return root


def run(root: Path, *extra: str) -> int:
    return gen_doc_index.main([str(root), *extra])


def test_generated_block_is_filled_and_surrounding_prose_survives(tree: Path) -> None:
    assert run(tree) == 0

    index = (tree / "reference" / "README.md").read_text(encoding="utf-8")
    assert "Hand-written framing that the generator must leave alone." in index
    assert "Hand-written closing that the generator must leave alone." in index
    assert "| [Widgets](widgets.md) | A one-line summary. |" in index


def test_regenerating_unchanged_documents_is_a_no_op(tree: Path) -> None:
    run(tree)
    before = (tree / "reference" / "README.md").read_text(encoding="utf-8")
    run(tree)
    assert (tree / "reference" / "README.md").read_text(encoding="utf-8") == before


def test_authored_documents_precede_planned_stubs(tree: Path) -> None:
    write_doc(
        tree / "reference",
        "gadgets",
        title="Gadgets",
        status="stub",
        body=STUB_BANNER_BODY,
    )
    run(tree)

    index = (tree / "reference" / "README.md").read_text(encoding="utf-8")
    assert index.index("[Widgets](widgets.md)") < index.index("### Planned") < index.index("[Gadgets](gadgets.md)")


def test_order_field_sequences_documents_within_a_class(tree: Path) -> None:
    write_doc(tree / "reference", "aardvarks", title="Aardvarks", order=10)
    write_doc(tree / "reference", "zebras", title="Zebras", order=5)
    run(tree)

    index = (tree / "reference" / "README.md").read_text(encoding="utf-8")
    assert index.index("[Zebras]") < index.index("[Aardvarks]") < index.index("[Widgets]")


def test_topics_page_groups_documents_across_classes(tree: Path) -> None:
    run(tree)

    topics = (tree / "topics.md").read_text(encoding="utf-8")
    beta = topics[topics.index("### beta") :]
    assert "- How-to: [Replace a widget](how-to/replace_a_widget.md)" in beta
    assert "- Reference: [Widgets](reference/widgets.md)" in beta
    assert "Reference: [Widgets](reference/widgets.md)" in topics[topics.index("### alpha") : topics.index("### beta")]


def test_each_document_gets_its_own_topic_line_below_the_heading(tree: Path) -> None:
    run(tree)

    document = (tree / "reference" / "widgets.md").read_text(encoding="utf-8")
    assert "# Widgets\n\n<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->\n" in document
    assert "Topics: [alpha](../topics.md#alpha), [beta](../topics.md#beta)\n" in document
    assert document.endswith("Body text.\n")


def test_a_document_topic_line_is_refreshed_rather_than_duplicated(tree: Path) -> None:
    run(tree)
    write_doc(tree / "reference", "widgets", title="Widgets", topics="[alpha]")
    run(tree)

    document = (tree / "reference" / "widgets.md").read_text(encoding="utf-8")
    assert document.count("BEGIN GENERATED: topics") == 1
    assert "Topics: [alpha](../topics.md#alpha)\n" in document


def test_a_changed_topic_set_rewrites_the_existing_block_in_place(tree: Path) -> None:
    run(tree)
    path = tree / "reference" / "widgets.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("topics: [alpha, beta]", "topics: [alpha]"), encoding="utf-8", newline="\n")
    assert run(tree) == 0

    document = path.read_text(encoding="utf-8")
    assert document.count("BEGIN GENERATED: topics") == 1
    assert "Topics: [alpha](../topics.md#alpha)\n" in document
    assert "topics.md#beta" not in document


def test_planned_documents_are_marked_in_the_topics_page(tree: Path) -> None:
    write_doc(tree / "reference", "gadgets", title="Gadgets", status="stub", body=STUB_BANNER_BODY)
    run(tree)

    assert "[Gadgets](reference/gadgets.md) (planned)" in (tree / "topics.md").read_text(encoding="utf-8")


def test_check_passes_on_current_output_and_fails_once_a_document_changes(tree: Path) -> None:
    run(tree)
    assert run(tree, "--check") == 0

    write_doc(tree / "reference", "widgets", title="Widgets", summary="A different summary.", topics="[alpha, beta]")
    assert run(tree, "--check") == 1


def test_check_fails_when_a_generated_block_was_never_filled(tree: Path) -> None:
    assert run(tree, "--check") == 1


def test_title_must_match_the_heading(tree: Path) -> None:
    write_doc(tree / "reference", "mismatch", title="Declared", heading="Actual")
    assert run(tree) == 1


def test_missing_front_matter_is_rejected(tree: Path) -> None:
    (tree / "reference" / "bare.md").write_text("# Bare\n\nNo front matter.\n", encoding="utf-8", newline="\n")
    assert run(tree) == 1


def test_unknown_status_is_rejected(tree: Path) -> None:
    write_doc(tree / "reference", "odd", title="Odd", status="draft")
    assert run(tree) == 1


def test_authored_status_must_be_omitted_rather_than_declared(tree: Path) -> None:
    write_doc(tree / "reference", "explicit", title="Explicit", status="authored")
    assert run(tree) == 1


def test_unquoted_title_and_summary_are_rejected(tree: Path) -> None:
    write_doc(tree / "reference", "bare", title="Bare", quoted=False)
    assert run(tree) == 1


def test_summary_holding_a_colon_is_accepted_when_quoted(tree: Path) -> None:
    write_doc(tree / "reference", "colonic", title="Colonic", summary="A subject: its elaboration.")
    assert run(tree) == 0


def test_quote_inside_a_value_is_rejected(tree: Path) -> None:
    write_doc(tree / "reference", "nested", title="Nested", summary='A "quoted" phrase.')
    assert run(tree) == 1


def test_an_empty_summary_is_rejected(tree: Path) -> None:
    write_doc(tree / "reference", "hollow", title="Hollow", summary="")
    assert run(tree) == 1


def test_stub_status_requires_the_stub_banner(tree: Path) -> None:
    write_doc(tree / "reference", "unbannered", title="Unbannered", status="stub")
    assert run(tree) == 1


def test_stub_banner_requires_stub_status(tree: Path) -> None:
    write_doc(tree / "reference", "misbannered", title="Misbannered", body=STUB_BANNER_BODY)
    assert run(tree) == 1


def test_oversized_summary_is_rejected(tree: Path) -> None:
    write_doc(tree / "reference", "verbose", title="Verbose", summary="x" * (gen_doc_index.SUMMARY_LIMIT + 1))
    assert run(tree) == 1


def test_topic_outside_the_vocabulary_is_rejected(tree: Path) -> None:
    write_doc(tree / "reference", "stray", title="Stray", topics="[gamma]")
    assert run(tree) == 1


def test_vocabulary_entry_used_by_no_document_is_rejected(tree: Path) -> None:
    page = (tree / "topics.md").read_text(encoding="utf-8")
    (tree / "topics.md").write_text(page + "\n- `gamma`: nobody's subject.\n", encoding="utf-8", newline="\n")
    assert run(tree) == 1


def test_index_pages_are_not_listed_as_documents(tree: Path) -> None:
    run(tree)
    assert "README.md)" not in (tree / "reference" / "README.md").read_text(encoding="utf-8")


def test_excluded_directories_are_skipped(tree: Path) -> None:
    vendored = tree / "vendored"
    vendored.mkdir()
    (vendored / "README.md").write_text("# Vendored\n", encoding="utf-8", newline="\n")
    (vendored / "loose.md").write_text("# Loose\n\nNo front matter here.\n", encoding="utf-8", newline="\n")

    assert run(tree, "--exclude", "vendored") == 0


def write_nav(root: Path, *entries: str) -> Path:
    path = root.parent / "zensical.toml"
    body = "\n".join(f'    {{ "Page {index}" = "{entry}" }},' for index, entry in enumerate(entries))
    path.write_text(NAV_TEMPLATE.format(entries=body), encoding="utf-8", newline="\n")
    return path


FULL_NAV = (
    "topics.md",
    "reference/README.md",
    "reference/widgets.md",
    "how-to/README.md",
    "how-to/replace_a_widget.md",
)


def test_complete_nav_passes(tree: Path) -> None:
    nav = write_nav(tree, *FULL_NAV)
    assert run(tree, "--nav", str(nav)) == 0


def test_root_page_missing_from_nav_fails(tree: Path) -> None:
    nav = write_nav(tree, *[entry for entry in FULL_NAV if entry != "topics.md"])
    assert run(tree, "--nav", str(nav)) == 1


def test_document_missing_from_nav_fails(tree: Path) -> None:
    nav = write_nav(tree, *[entry for entry in FULL_NAV if entry != "reference/widgets.md"])
    assert run(tree, "--nav", str(nav)) == 1


def test_duplicated_nav_entry_fails(tree: Path) -> None:
    nav = write_nav(tree, *FULL_NAV, "reference/widgets.md")
    assert run(tree, "--nav", str(nav)) == 1


def test_nav_entry_without_a_file_fails(tree: Path) -> None:
    nav = write_nav(tree, *FULL_NAV, "reference/imaginary.md")
    assert run(tree, "--nav", str(nav)) == 1


def test_individually_listed_generated_record_fails(tree: Path) -> None:
    decisions = tree / "decisions"
    decisions.mkdir()
    (decisions / "0001-a-decision.md").write_text("# A decision\n", encoding="utf-8", newline="\n")
    nav = write_nav(tree, *FULL_NAV, "decisions/0001-a-decision.md")
    assert run(tree, "--nav", str(nav)) == 1
