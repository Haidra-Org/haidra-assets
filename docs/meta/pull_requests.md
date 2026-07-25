# Haidra Pull Request Standard

This document governs pull request descriptions for Haidra-Org repositories.

In brief:

- Two things are required: the upshot first, and an explicit behavior boundary.
- Everything else follows the change, its audience, and the repository.
- The recommended elements below are used when the change warrants them and omitted when it does not.

A description exists to get a reviewer to a correct decision quickly. A one-line dependency bump and a scheduler
rewrite need different descriptions, so this document fixes only what every description needs.

## Requirements

### Upshot first

The opening paragraph states what the change does, why it is being made, and what happens when it is deployed. The
first line stands alone as a complete summary of the change, following
[Google's CL description guidance](https://google.github.io/eng-practices/review/developer/cl-descriptions.html).

A reader who sees only the title and first line in a notification or a commit log knows what landed.

### Behavior boundary

A pull request that changes behavior states what changes and what deliberately does not.

Distinguish a changed outcome from a changed mechanism that produces an identical outcome. A reviewer needs to know
which parts of a diff they must reason about for correctness and which parts they can confirm are equivalent.

## Recommended elements

- **Review order.** Suggest a path through the diff that separates the core of the change from mechanical fallout, so a
  reviewer spends attention where the argument is.
- **Verification with specifics.** Give test counts, measurements against production data, and reproduction commands.
  State plainly what was not verified.
- **Permalink excerpts.** Quote the hunks that carry the argument, linked by commit permalink so they stay valid as the
  branch moves.
- **Links to durable rationale.** Reasoning that outlives the review belongs in an ADR or a reference document (see
  [documentation.md](./documentation.md)). Link to it from the pull request rather than restating it.
- **Deployment ordering.** Where rollout is order-sensitive, say what must happen before and after the merge, including
  migrations and configuration changes.
- **Incidental changes.** Call out formatting catch-up and drive-by fixes so reviewers can discount them.

## Exemplars

These pull requests calibrate depth and tone:

- [AI-Horde#533](https://github.com/Haidra-Org/AI-Horde/pull/533)
- [AI-Horde#534](https://github.com/Haidra-Org/AI-Horde/pull/534)

## Prose

Pull request text follows the heading and prose rules in [documentation.md](./documentation.md).

## On these rules

These rules are opinionated and deliberately narrow. Change proposals are welcome where a requirement is overly
restrictive, missing, or could be improved.
