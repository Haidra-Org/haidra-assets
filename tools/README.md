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
