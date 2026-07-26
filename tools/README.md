# Tools

Shared tooling for Haidra repositories, safe to run from a submodule checkout. The documentation tools are
standard-library Python and need no installation. The one exception is `param_sweeps/`, which renders images
and is installed as its own package with its own dependencies.

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
title: "Job matching and pop" # must equal the document's level-one heading
summary: "One line, at most 200 characters, shown in every index that lists this document."
status: stub # omit entirely for an authored document
topics: [requests, workers] # each topic must be defined in topics.md
order: 30 # optional, orders the document within its class (default 100)
---
```

`title` and `summary` must be double-quoted. An unquoted YAML scalar containing `": "` does not parse, and a
site generator that fails to parse front matter publishes it as page text without reporting an error.

`status` is omitted from an authored document. The key is reserved by Material-derived themes, which put a
marker beside the navigation entry of any page carrying it, so declaring it everywhere marks everything and
says nothing. A stub declares `status: stub` and the theme is given the matching label:

```toml
[project.extra.status]
stub = "Planned document, not yet authored"
```

From that front matter, the tool rewrites three kinds of generated block, leaving the hand-written prose around
them untouched:

- `documents` in each class index (`docs/<class>/README.md`): a table of authored documents, then a table of
  planned stubs.
- `topics` in `docs/topics.md`: every topic with the documents that declare it, across classes.
- `topics` in each document: its own topic line, linking into the topics page. This block is inserted below the
  level-one heading when it is absent, so a new document needs no boilerplate.

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

## param_sweeps/

Renders the parameter-sweep illustration library the Learn surfaces teach from: for each generation parameter,
a strip of images that differ in that parameter and nothing else, each stop carrying a plain-language caption.
One checked-in specification describes the library, and two runners render it, one on a local GPU through
`horde-engine` and one through the public AI Horde API.

```sh
cd docs/haidra-assets/tools/param_sweeps
uv sync --group dev

# What would be downloaded, and how many images, generating nothing
uv run param-sweeps plan

# Regenerate one strip
uv run param-sweeps horde --parameter clip_skip --model anything-diffusion --scene person
```

Unlike the tools above, this one has dependencies and its own `pyproject.toml`. Output lands in
`assets/param-sweeps/`, with an `index.json` a web app can render every strip from on its own. See
[param_sweeps/README.md](param_sweeps/README.md) for the runbook, including the GPU-backend note that has to be
settled before `horde-engine` is installed.
