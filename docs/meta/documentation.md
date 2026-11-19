# Haidra Documentation Standard

This document governs in-repository documentation (the `docs/` tree) for Haidra-Org repositories. It applies to
documents written for contributors and operators, not to docstrings, which are covered by [python.md](python.md), nor
to user-facing product text, which is covered by [copy.md](copy.md).

In brief:

- Organize `docs/` by [Diátaxis](https://diataxis.fr/) class, each class carrying its own index.
- Declare a document's title, summary, status, and topics in front matter, and generate the indexes from it.
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
a repository actually needs. A class directory is created when its first document is written, never in advance.

Indexing is two-level. Each class carries a `README.md` that says in a line or two what a reader finds there and lists
its documents. `docs/README.md` routes between the classes and does not list individual documents, so the landing page
stays a constant size as the tree grows.

Diátaxis settles where a document is filed and what mode it is written in. It is a tool for the people writing the
tree, not a subject the tree teaches: a class index names its directory and gets on with it, and the authoring rules
for each class live here rather than on the pages readers came to read.

The rules below govern quality, and they apply within every class.

## Audience and task

Before drafting or restructuring a page, identify its primary task, assumed knowledge and successful outcome in
review notes. Assume ordinary expertise in the reader's discipline. Introduce repository-specific terms when they
first affect understanding or an action, with the relevant object, response field or consequence.

Qualify terms that could denote several things in context. For example, specify the service or process meant by
"instance". Use enough qualification to distinguish the referent, including in headings and sections reached
directly. Shorter subsequent mentions are fine while that meaning remains clear.

Keep secondary-audience material when it helps with the primary task. Move independently useful material to its
appropriate page and link where it becomes relevant. Moving unrelated material to the end does not resolve an
audience mismatch. Split by task or conceptual boundary, not by a fixed page length.

The literal language, consistent terminology and claim-scoping principles in [copy.md](copy.md) also apply here.
Its product-interface requirements and novice image-user assumptions do not apply automatically to technical docs.
Preserve precise technical terms and explain them for the intended audience instead of replacing them with synonyms.

## Front matter and generated indexes

Every curated document declares its own metadata, and every index that lists documents is generated from those
declarations. An index maintained by hand disagrees with the tree it indexes, and the disagreement is invisible until a
reader is already lost.

```yaml
---
title: "Job matching and pop" # equals the document's level-one heading
summary: "One line, at most 200 characters, shown wherever this document is listed."
status: stub # omitted entirely for an authored document
topics: [requests, workers] # each defined in the topics page
order: 30 # optional; sequences the document within its class
---
```

- `title` and `summary` are double-quoted. An unquoted scalar containing `": "` is not valid YAML, and a site
  generator that cannot parse front matter publishes it as page text. Front matter is validated against the parser
  that will consume it, never against a lenient reader.
- `summary` is what an index shows. It states what the document holds, not that the document exists.
- `status` marks a stub and is absent otherwise. A stub is published rather than withheld, and what it publishes is
  about the subsystem, not about itself: a short factual description of the thing, the code that holds the behavior,
  and links onward. It carries one banner line saying the detail is not written yet, and is marked as planned in its
  class index. A stub says what is missing; it never says when it will arrive, and it never spends a paragraph
  describing the document it is going to become. The key is reserved by Material-derived themes, which mark the
  navigation entry of every page carrying it, so marking only stubs is what makes the marker informative.
- `topics` are subject tags shared across classes. A topics page defines each tag and collects the documents carrying
  it, which is how a reader holding a subject reaches the explanation, the reference, and the procedure together. Each
  document also carries its own topics, generated, so a reader who arrives mid-tree can leave through the subject. A
  tag must be defined before it is used, and a defined tag no document uses is removed. Without that rule the tag set
  splinters into near-duplicates and stops being a navigation surface.

Where a repository publishes a site, navigation order and display titles stay curated; navigation membership does not.
Membership is checked against the tree so a document cannot be added without appearing, or removed while still listed.

## Opening summary

Every document opens with a summary a reader can stop after and still know what the document covers, who it is for, and
where to go next.

- It is the first substantive prose after the title and generated metadata.
- It is at most roughly ten lines or five bullets.
- A label such as `TL;DR` or `In brief:` is permitted when the summary helps readers decide whether to read the page,
  or gives central takeaways that a typical reader can use without the full nuance. An unlabelled opening is also
  sufficient. Do not add a second summary that repeats the opening.
- Keep qualifications that change an action or make a takeaway true. A summary may omit supporting detail, but must
  not promise a result that the body makes conditional.

## Progressive disclosure

Heading hierarchy runs from overview to detail. A reader who stops at `##` has a correct picture at lower precision
than a reader who continues to `###`. Detail refines the level above it and never contradicts it.

Group sections by the concepts needed to understand them. Within a paragraph, state the main relationship before
its mechanism and qualifications. Introduce concepts in dependency order before shortening individual sentences.

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

Beyond the code map:

- Cite code by module path and symbol, never by line number. Write `horde/classes/base/worker.py`, `Worker.check_in`.
  Line numbers rot on the next edit; module and symbol names survive, and a checker can verify a path still exists.
- Collect sharp edges rather than editorialising inline. Where current behavior carries a hazard (a cache with no
  invalidation, a non-obvious ordering, an ORM freshness trap), describe the mechanism and its consequences factually,
  gathered under one heading near the end for lookup. Also state a consequential caveat before the action or beside
  the claim it qualifies. A final hazards section must not be the first notice of a prerequisite or possible loss.
- Give the reason where there is evidence for it. When a comment, commit message, or decision record says why a thing
  is done a certain way, state it and link the record. Where the reason is genuinely unknown, say that the rationale is
  not recorded rather than inventing one.
- Prefer prose and tables to code. Where an excerpt is unavoidable, keep it small. Use a diagram only where it does
  work prose cannot: a state flow, a cache topology, a class hierarchy.

## Explanation documents

An explanation builds the mental model behind a subsystem: what problem it solves, what the alternatives were, and
which properties the design buys.

- Explain the design, do not specify it. Field lists, schemas, and exhaustive orderings belong in reference; link there
  rather than restating them, so the two cannot drift apart.
- Name the alternatives. An explanation that never says what was rejected leaves the reader unable to judge the design.
  Where a rejection is recorded as a decision, link the record rather than repeating its reasoning.
- State the properties the design buys and what they cost. Durability, ordering, staleness bounds, and failure behavior
  are the payload.

## How-to documents

A how-to is a procedure for someone who already knows what they want to achieve.

- Open with the preconditions and the end state, so a reader can tell before running anything whether this is the
  procedure they want.
- Give observable checks at meaningful failure boundaries and for the final outcome. Name the query, endpoint or
  field that confirms success. Related actions may share a check when a failure remains easy to locate. Avoid
  verification boilerplate for actions whose result is already evident.
- Put prerequisites, saved state and decision-relevant consequences before the action that requires them. Explain
  recovery for consequential changes, including limits on reversal. Omit empty statements such as "reversal: none"
  for a read-only operation and obvious instructions to remove newly added configuration.
- Number steps when they form a sequence. Mark alternatives and optional branches, and identify the earlier outputs
  each branch needs. Independent tasks do not become a sequence merely because they share a page.
- For waiting and verification, state success and relevant terminal failures, then give a diagnostic next step if
  success is not reached. Do not invent a timeout or service guarantee to make the procedure seem complete.
- Distinguish illustrative output from exact assertions. Identify variable fields and conditional outcomes.
- Keep commands exact and parameterised. Values that vary by deployment appear as named placeholders, never as one
  machine's values pasted in.

## Tutorial documents

A tutorial provides a bounded learning path to an observable result. State prerequisites and follow one coherent
example. Apply the how-to rules for dependencies, verification and recovery. Explain example-specific choices so
readers can distinguish them from normal practice. Optional extensions must not obscure the core completion point.
When an outcome depends on a model or external service, explain the acceptable alternatives and how to continue.

## Headings and prose

- Headings name the content beneath them. Apart from the opening-summary labels permitted above, avoid headings
  about the document's length or the reader's attention.
- Confidence comes from specifics: numbers, file names, measured values. Adjectives do not supply it.
- No em dashes. Use a colon, a full stop, a parenthetical, or a comma.
- Avoid the "not X, but Y" construction. State what is true.
- Write in the present tense and describe behavior as it is. Milestone, incident, and point-in-time language ages out
  of date and is disallowed.
- Write about the system, not about the documentation. A page does not define the documentation framework, classify
  itself within it, rank its own importance, or refer to the batch of pages it was written alongside. "This document
  explains X" is fine once, at the top, where it saves the reader time; a paragraph on what kind of document it is, is
  not. Instructions to whoever writes and regenerates the tree belong in this standard, or in a comment the published
  page does not show.
- Address the reader as someone with a task, not as a category. Say what a page holds and let them choose; do not
  narrate what sort of reader they are or which question they are holding.

## Cross-linking

Explanation, reference, and how-to documents link to each other at the point where the other document becomes relevant,
and each link says what the target holds. A reader following a link knows before clicking whether it answers their
question.

Where the publishing format supports it, link critical terms and concepts to existing explanations at their first
consequential use. Prefer the specific section that explains the concept over a broad landing page. Choose links
that help the intended reader understand a distinction or perform an action. Avoid linking ordinary vocabulary or
every repeated occurrence. A later independently useful section may repeat a link for readers arriving there
directly. Keep enough explanation locally to follow the passage without opening the link. Do not create a glossary
page solely to provide a link target.

Give each contract a canonical reference home. Procedures include the subset needed for the task and link to the
full contract. Keep short facts locally when removing them would force a reader to leave the procedure to understand
or safely perform the next action. Check repeated facts for agreement when the contract changes.

## Site navigation

Where a repository publishes its `docs/` tree as a site, navigation obeys four rules:

- Top-level navigation mirrors the Diátaxis classes, ordered Home, Explanation, Reference, How-to, then supporting
  sections. A reader's first choice on the site is the same choice the directory structure makes.
- Navigation lists curated documents. A generated corpus (decision records, generated API references) enters navigation
  as its single index page; its members are reached through that index, cross-links, and search. Navigation size must
  not grow with corpus size.
- Navigation depth stays within two levels. Structure deeper than that belongs inside a page, where the table of
  contents carries it.
- The landing page routes within its opening summary: each class named, linked, and described by what a reader finds
  there. A reader should spend their first screenful choosing a direction, never decoding the site.

## Maintenance

Review structure, procedural dependencies and terminology before sentence style. Check a direct arrival at each
page: can the intended reader understand the terms, complete the task or locate the contract, and recognize an
unexpected result? Record unresolved audience or behavior questions for review. Do not invent product policy to
resolve an editorial ambiguity. Mechanical checks supplement this reading review.

A documentation change lands in the same pull request as the behavior change it describes. Documentation that trails
the code it documents is treated as a defect in that pull request.

A repository publishing its docs runs the gates in CI: the site builds in strict mode, every generated index verifies
clean against its inputs (`--check`), front matter is valid and agrees with the document body, site navigation matches
the tree, cited code paths exist, prose style rules that can be checked mechanically are checked, license compliance
passes, and internal links resolve. Tooling that gates the documentation is itself tested. A generated file that can
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
Topical organization belongs to the index. The records are indexed by a generated `docs/decisions/index.md` carrying
each record's status and date, and that page is how the corpus enters navigation: records are never listed
individually, so navigation does not grow with the record count.

An accepted record is immutable in substance once its decision has stood through a production release. Permissible
edits are then typo fixes and repairing file or symbol references that the codebase has moved out from under the
record. Context, Decision Outcome, and Consequences are never rewritten to match later reality; a changed decision gets
a new record.

While the initiative a record belongs to is still being built out, a record whose decision is reversed or narrowed by
that same initiative is amended in place: the body states the current decision, the date is updated, and no amendment
section is added. Separate records for each reversal within one initiative would leave a trail that no reader follows.
The record's history stays in version control.

The records are the asset; publishing tooling is replaceable and is not part of this standard. A browse surface, when a
repository or the organization wants one, is a static site built from the same flat directory the records live in, with
its index generated from the records' front matter rather than maintained by hand. Any tool that renders a Markdown
tree qualifies, and the corpus must remain readable and complete without one. Two branches can claim the same `NNNN`
number; a number is final when its record merges, and a collision is resolved by renaming before merge.

Reference documents and pull requests link to the relevant ADR rather than restating its reasoning.
