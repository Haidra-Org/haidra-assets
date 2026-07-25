# Tools

Shared documentation tooling for Haidra repositories. Everything here is standard-library Python and safe to
run from a submodule checkout.

## gen_adr_index.py

Generates `index.md` for a directory of MADR decision records: a table of every record with its front-matter
status and date, and a Mermaid graph of the cross-references between records. Output is deterministic, so the
`--check` mode can gate CI against a stale index.

```sh
# Write (or refresh) docs/decisions/index.md
python docs/haidra-assets/tools/gen_adr_index.py docs/decisions

# CI: fail if the committed index no longer matches the records
python docs/haidra-assets/tools/gen_adr_index.py docs/decisions --check
```

The index renders on GitHub (which draws `mermaid` fences natively) and on any static site generator whose
Markdown pipeline has a Mermaid fence configured, such as Zensical via `pymdownx.superfences`.

## gen_doc_index.py

Builds the parts of a documentation tree that can be derived from the documents themselves, so an index cannot
disagree with what it indexes. Each curated document carries YAML front matter:

```yaml
---
title: Job matching and pop            # must equal the document's level-one heading
summary: One line, at most 200 characters, shown in every index that lists this document.
status: authored                       # authored | stub
topics: [requests, workers]            # each topic must be defined in topics.md
order: 30                              # optional, orders the document within its class (default 100)
---
```

From that, the tool rewrites two kinds of generated block, leaving the hand-written prose around them untouched:

- `documents` in each class index (`docs/<class>/README.md`): a table of authored documents, then a table of
  planned stubs.
- `topics` in `docs/topics.md`: every topic with the documents that declare it, across classes.

A block is delimited by `<!-- BEGIN GENERATED: name (gen_doc_index.py) -->` and `<!-- END GENERATED: name -->`.
A documentation class is any directory under the docs root holding a `README.md`, minus `--exclude` names
(`haidra-assets` by default). Decision records are excluded by construction: they carry an `index.md`, not a
`README.md`, and are indexed by `gen_adr_index.py`.

```sh
# Rewrite the generated blocks
python docs/haidra-assets/tools/gen_doc_index.py docs

# CI: fail on a stale block, invalid front matter, or navigation drift
python docs/haidra-assets/tools/gen_doc_index.py docs --check --nav zensical.toml
```

The tool fails rather than generating a misleading index when a document's front matter is missing or invalid,
its title disagrees with its heading, its `status` disagrees with the presence of a stub banner, or it uses a
topic that `topics.md` does not define (and, in reverse, when `topics.md` defines a topic no document uses).

`--nav` cross-checks a Zensical configuration against the tree. Navigation order and display titles stay
curated; membership does not. It fails when a curated document is missing from `nav`, listed twice, or absent
from disk, and when a generated record such as `decisions/0001-*.md` is listed individually instead of being
reached through its index.

## check_code_refs.py

Fails when documentation cites a repository path that does not exist. It extracts backticked tokens that start
with a known top-level directory (`horde`, `tools`, `tests`, `sql_statements`, `docs` by default; override
with `--roots`) and name a file with an extension, then checks each against the repository root. Fenced code
blocks are ignored. Trailing `:line` suffixes are accepted and stripped.

```sh
python docs/haidra-assets/tools/check_code_refs.py docs/README.md docs/explanation docs/reference \
    docs/how-to docs/decisions
```

Run it from the repository root, or pass `--repo-root`. Each stale citation is reported as `file:line: cited
path does not exist`.
