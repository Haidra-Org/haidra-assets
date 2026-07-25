# Haidra Documentation Standard

This document governs in-repository documentation (the `docs/` tree) for Haidra-Org repositories. It applies to
documents written for contributors and operators, not to docstrings, which are covered by [python.md](python.md).

In brief:

- Organize `docs/` by [Diátaxis](https://diataxis.fr/) class, with `docs/README.md` as the index.
- Open every document with a summary that survives truncation.
- Order headings from overview to detail so a reader can stop at any depth.
- Give reference documents a code map from concept to file and symbol.
- Record decisions as one-per-file ADRs under `docs/decisions/`.

These rules are prescriptive. Deviate where the document is better for it, and state the reason in review.

## On these rules

These rules are opinionated and exist for consistency across repositories. They do not claim to be the only workable
set. Change proposals are welcome where a rule is overly restrictive, missing, or could be improved.

## Organization

Documents are filed by Diátaxis class: `explanation/`, `reference/`, `how-to/`, and `tutorial/`, using only the classes
a repository actually needs. `docs/README.md` indexes the tree and says what each document holds.

Diátaxis settles where a document is filed and what mode it is written in. The rules below govern quality, and they
apply within every class.

## Opening summary

Every document opens with a summary a reader can stop after and still know what the document covers, who it is for, and
where to go next.

- It is positional. It comes first, before any other heading or body content.
- It is at most roughly ten lines or five bullets.
- It is introduced plainly with  `TL;DR`, `Too long; didn't read`, and `If you read nothing else`, `In brief:` or
  carries no label at all.

## Progressive disclosure

Heading hierarchy runs from overview to detail. A reader who stops at `##` has a correct picture at lower precision
than a reader who continues to `###`. Detail refines the level above it and never contradicts it.

## Reference documents

A reference document includes a code map: a table from concept or responsibility to the file and symbol that implements
it.

| Concept | File                    | Symbol        |
| ------- | ----------------------- | ------------- |
| Job pop | `horde/apis/v2/base.py` | `JobPop.post` |

The code map exists so the document launches a reader into the code. A reference document describes contracts and
intent; the code remains the authority on behavior.

Where a document states a testable contract, it also names the test that covers it, so a reader can confirm the
contract holds and a maintainer can see what breaks when it changes.

## Headings and prose

- Headings name the content beneath them. A heading never describes the document, its length, or the reader's
  attention.
- Summaries are positional. Their placement identifies them, so they need no performative label.
- Confidence comes from specifics: numbers, file names, measured values. Adjectives do not supply it.
- No em dashes. Use a colon, a full stop, a parenthetical, or a comma.
- Avoid the "not X, but Y" construction. State what is true.
- Write in the present tense and describe behavior as it is. Milestone, incident, and point-in-time language ages out
  of date and is disallowed.

## Cross-linking

Explanation, reference, and how-to documents link to each other at the point where the other document becomes relevant,
and each link says what the target holds. A reader following a link knows before clicking whether it answers their
question.

## Site navigation

Where a repository publishes its `docs/` tree as a site, navigation obeys four rules:

- Top-level navigation mirrors the Diátaxis classes, ordered Home, Explanation, Reference, How-to, then supporting
  sections. A reader's first choice on the site is the same choice the directory structure makes.
- Navigation lists curated documents. A generated corpus (decision records, generated API references) enters navigation
  as its single index page; its members are reached through that index, cross-links, and search. Navigation size must
  not grow with corpus size.
- Navigation depth stays within two levels. Structure deeper than that belongs inside a page, where the table of
  contents carries it.
- The landing page routes by intent within its opening summary: which class answers which kind of question, each named
  with a link. A reader should spend their first screenful choosing a direction, never decoding the site.

## Maintenance

A documentation change lands in the same pull request as the behavior change it describes. Documentation that trails
the code it documents is treated as a defect in that pull request.

A repository publishing its docs runs the gates in CI: the site builds in strict mode, every generated index verifies
clean against its records (`--check`), license compliance passes, and internal links resolve. A generated file that can
drift from its inputs without failing CI will.

## Architecture Decision Records

Decisions live in ADRs, one decision per file, at `docs/decisions/NNNN-kebab-title.md` with a zero-padded four-digit
sequence number.

Records use [MADR 4](https://adr.github.io/madr/): YAML front matter carrying at least `status` and `date`
(`decision-makers`, `consulted`, and `informed` where they add information), then Context and Problem Statement,
Decision Drivers, Considered Options, and Decision Outcome with its Consequences. Alternatives that were weighed appear
in Considered Options, each with the reason it was rejected under Pros and Cons of the Options. The remaining optional
MADR sections (Confirmation, More Information) are used only when they earn their length.

In REUSE-compliant repositories, SPDX tags go in an HTML comment between the front matter and the title. A `#`-prefixed
tag inside the front matter can be mistaken for a Markdown heading, and therefore the record's title, by publishing
tools.

`status` is one of MADR's values:

- `proposed`
- `rejected`
- `accepted`
- `deprecated`
- `superseded by ADR-NNNN`

A superseding record links to the record it replaces under More Information, and the superseded record's status names
and links its replacement. A decision changed in part stays `accepted` and links its amendment under More Information,
two ways as well.

The directory stays flat and numbers are global: never reused, never renumbered, never sharded into subdirectories.
Topical organization belongs to the index. While a repository holds few records, `docs/README.md` lists them; past
that, `docs/decisions/README.md` indexes them, grouped by system and showing status.

An accepted record is immutable in substance. Permissible edits are typo fixes and repairing file or symbol references
that the codebase has moved out from under the record. Context, Decision Outcome, and Consequences are never rewritten
to match later reality; a changed decision gets a new record.

The records are the asset; publishing tooling is replaceable and is not part of this standard. A browse surface, when a
repository or the organization wants one, is a static site built from the same flat directory the records live in, with
its index generated from the records' front matter rather than maintained by hand. Any tool that renders a Markdown
tree qualifies, and the corpus must remain readable and complete without one. Two branches can claim the same `NNNN`
number; a number is final when its record merges, and a collision is resolved by renaming before merge.

Reference documents and pull requests link to the relevant ADR rather than restating its reasoning.
