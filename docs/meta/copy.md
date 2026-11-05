# Haidra Copy Standard

This document governs user-facing text in Haidra-Org products. That includes labels, help notes, tutorial and guide
steps, concept pages, empty states, errors, and any other text a reader sees while using a tool. The contributor
`docs/` tree is covered by [documentation.md](documentation.md). Where both documents apply, its prose rules also
apply here.

These rules are prescriptive. If breaking a rule makes a text better, break it and give the reason in review.

## Summary

- Every string should help the reader understand what they are doing, so that they can do it again without help.
- Write literally. Use plain verbs and the names that the interface shows. Assume the reader is not a native speaker
  of English.
- Do not locate anything by direction or position on the screen. Identify it by its label, its role, or another
  attribute that does not change with the layout.
- A simplification must still be true and must agree with the rest of the product. Use the standard technical term
  when the interface uses it.
- State a fact as general only when it is true in general. Something seen in one example is an observation about that
  example. State the scope of an example once per page or strip, not in every caption.
- Indent a step under another step only when it is part of that step. Steps that do not depend on each other go at
  the same level.
- Every term and setting glyph links to an explanation: a short one on the same page, a full page one click away, and
  a way back.
- Readers describe their goal in their own words. Use words close to theirs, so they can find the control they need.

## The reader

Write for an adult who is learning on their own. They have a goal, such as "keep this face but change the background"
or "make my picture sharper", and they want to find the control that does it and understand how it works. Assume
that the reader:

- may not be a native speaker of English, and reads words at their literal meaning
- may use any screen size, either theme, or a screen reader, so their layout can differ from yours
- may open any page first, without having read the pages before it
- chooses how deep to go: skim, follow the steps, or read the full explanation

Do not be vague or assume prior knowledge, nor should you be patronizing.

## Words

- Use the verb for what the reader does and the name that the interface shows. The reader writes or types a prompt.
  They do not "say" it. They press a button, and the copy refers to the button by its label.
- Do not use idioms, metaphors or wordplay in instructions. "Pin the seed" is easy for a native speaker to decode.
  "Keep the same seed" is an instruction that anyone can follow. If a short product term is kept, define it the first
  time it appears on each page.
- Use one name for each concept everywhere. If the interface says "Denoising strength", the tutorial, the help note
  and the concept page say "Denoising strength" too. A synonym makes the reader wonder whether it means something
  else.
- Prefer plain words to technical ones, unless the technical term is clearer and the interface uses it. In that case
  use it, and introduce it once: "guidance, sometimes called CFG".
- Make numbers and units concrete: "1024 by 1024" and "about a minute", instead of "large" or "a while".
- Do not use the words that the team uses for the parts of its own code. Words such as door, track, world, sheet,
  dock, pane, strip, plate, lane, landmark, register, tier, flow, surface and evidence describe how the product is
  built, and readers do not know them. Describe what the reader sees or does: "the panel", "the tutorial", "the
  settings", "try it yourself", "the same lesson with a different subject". A word for something the reader can see,
  such as a button, a card or a slider, is fine.
- Write instructions in the present tense, in the active voice, and in the second person.
- Do not use em dashes or "not X, but Y" constructions. Do not group words in threes for rhythm. Do not praise the
  product or the reader.

## Plain register

Explanatory copy includes captions, help text, reference pages and the first paragraph of a page. Two kinds of reader
read it: adults who have never used the feature, and experienced users who have. On a first reading the new reader
must be able to follow it, and the experienced reader must not find anything wrong in it. Three habits make that
fail, and copy must avoid them.

- **Abstract nouns in place of the things themselves.** Examples are "the render", "the source", "the hold" and "a
  way of holding a render to a source picture". The reader has real things in front of them: the picture they gave,
  the map that the detector drew from it, and the image that came back. Name those things every time.
- **Compressed sentences.** "Up to 0.15 the render is the prompt's own picture" fits a comparison, a threshold and a
  metaphor into nine words. Use more words: "Up to 0.15 the map has almost no effect. The image looks the way the
  prompt alone would make it."
- **Sentences that put the subject last.** "A ControlNet render never keeps..." and "What each way of holding..." make
  the reader wait to find out what the sentence is about. Start with the thing the reader has, and follow it with a
  plain verb.

Keep the real terms, such as control type, control map, control strength, denoise and seed, and define each one where
it first matters. Do not replace them with synonyms. Do not explain things the reader already knows, such as what a
picture is. Keep sentences short, with one idea in each. Write numbers the way the reader will type them.

To check a text, read it twice. First read it as someone who has used a phone camera and nothing more. Then read it
as someone who trains ControlNet models. If either reader would be confused or would object, rewrite it.

Making a claim more careful (see [Claims](#claims)) does not allow it to become abstract. "Adjusts the distribution of
timesteps" and "a single-evaluation sampler" fail this standard just as "the hold" does. When a sentence has to be
less certain, use the plainer true statement, such as "how many steps help depends on the model". Do not switch to a
vaguer technical one.

| Before | After |
| --- | --- |
| Up to 0.15 the render is the prompt's own picture; the map's hold shows from 0.25 and is settled by 0.5. | Up to 0.15 the map has almost no effect: the image looks the way the prompt alone would make it. From 0.25 you can see the map guiding the image, and by 0.5 the composition follows the map completely. |
| A ControlNet render never keeps your picture; it keeps what the detector drew from it. | The image you get back is a new image. The worker first draws a map from your picture (an outline, a depth map or a pose), then makes a new image that follows that map. |
| What each way of holding a render to a source picture keeps, and what it leaves the model free to change. | Each control type reads something different from your picture, such as its edges, its depth, a pose or its colours. This page shows what each one keeps and what it lets the model change. |

## Simplifications

A simplification is allowed only if it is still true. "Starts from nothing" is a different claim from "starts from
noise", and it contradicts the page that explains noise. Before you shorten an explanation, check that the short
version agrees with every other place in the product that describes the same thing.

When a string includes a value that comes from data, such as a size, a seed or a model name, insert the value from
the data instead of typing it. Then the text stays correct when the example changes.

## Claims

Readers take every explanatory sentence as a fact about the product. Three kinds of claim are allowed. Write each one
so that the reader can tell which kind it is.

- **A general fact.** It is true for every model, worker and picture that the product handles. "Larger images take
  more time and kudos." "The same seed with the same settings and worker gives the same image."
- **A limit or a published suggestion.** Examples are the API's range, the studio's behaviour, and the values that a
  model or sampler recommends. Say where the value comes from. "The studio accepts 0.01 to 3." "Use the model's
  suggested CLIP skip value."
- **An observation about the example shown.** Say that it is about the example. "At 2 steps the scene has not formed."
  "In this set the colours wash out past 1.75."

These kinds of claim are not allowed:

- Rules of thumb stated as facts, such as "most models stop improving between 20 and 40", "5 to 10 suits most
  models" and "above 1.75 the colours wash out". If it is true of the example, say so about the example. If it is a
  published suggestion, say who published it.
- Opinion, such as "worth a look, not a stop sign", "the right setting for almost everything" and "more rarely
  helps".
- History of the product, such as "on older versions of the horde, denoise did that job". Copy describes the product
  as it is now.
- A description of a mechanism that is simplified until it means something else, such as "repaints it" for
  "generates from a noisy version of your image".

When the correct statement depends on the model, say so. Then give the reader a way to check: the model's suggested
values, the studio's estimate, or a comparison with the seed and the other settings fixed.

**Numbers.** Keep a number if it is a limit, a published suggestion or an observation that is labelled as one. Remove
it only if it is a rule of thumb. Deleting a number does not fix an unsupported claim. Saying where the number comes
from, or stating it as an observation, does. A concrete statement is better than a vague one (see [Words](#words)),
as long as it is true.

**Warnings.** Add a warning where a reader who believed the text literally would lose something. Examples: the
operator of a trusted worker can still see the request, a QR code that scanned once may not scan with another seed,
the NSFW check can miss an image, and a downgrade can still be refused. One sentence, placed where the reader would
form the mistaken belief, is enough.

**Scope of examples.** The fact that an example is only one example applies to the whole strip or page. State it
once, in one place, such as the first paragraph of the page, the note under the examples, or the comparison notes.
Do not repeat it in the captions. A caption says what can be seen in that image, in plain words, without a general
claim. A caption that only says "compare with the neighbouring values" does not teach anything. A caption that
repeats the page's note about scope does not add anything.

**Uncertainty.** Use "may", "can" and "generally" only where the outcome is uncertain. Do not use them to weaken a
known fact, such as "the studio sends denoising strength 1 in this mode". Do not use them to make a vague technical
phrase sound careful.

**Titles.** A title names what the section contains: "Image comparison", "Example settings", "Comparison grid". Avoid
titles such as "Where the difference is" or "The recipe". A tutorial's title can name the technique. In that case its
summary states the reader's goal in the reader's words, such as "change the weather in a picture you already have".

| Before | After |
| --- | --- |
| These are worth a look, not a stop sign. The horde makes the final call on what it will run. | Review these suggestions before generating. The Horde also checks whether it can accept the request. |
| Most models stop improving somewhere between 20 and 40. | How many steps help depends on the model and sampler. Start with the model's suggested range. In this example, little changes after 30. |
| Restricts the request to workers the horde has marked as trusted. Far fewer workers qualify, so expect a longer wait in exchange for the tighter guarantee. | Limits the request to workers run by users the Horde marks as trusted. Fewer workers qualify, so the wait can be longer. Trust status does not guarantee image quality, and the operator can still see what was sent. |
| Two steps is barely a start: coloured mush with a hint of where things will go. | At 2 steps the scene has not formed. (The note that other models and prompts respond differently is written once under the strip.) |
| Compare prompt agreement, contrast, and shape distortion with neighbouring values. (repeated on every frame) | Guidance 3: the sky is the colour from the prompt, and the outlines are still soft. |

## Position and time

- Do not locate anything by direction. Avoid "below", "above", "on the right" and "the panel beside". A direction is
  true on one screen size and wrong on another, and it becomes wrong when the design changes. Locate things by name,
  label or glyph, or by a marker that the interface shows, such as "the Source image card marked here".
- The same rule applies to sequence words that depend on the layout, such as "the next card down", and to references
  to the current design, such as "the blue button".
- Do not describe changes over time, such as "new" or "now". Copy describes the product as it is.
- When a page has to refer to something next to the text, such as a row of images or a result, give it a name or a
  caption and refer to that.

## Instructions that teach

If an instruction only tells the reader what to click, they cannot repeat the task alone. Each step includes:

1. **What to do**, using the names in the interface.
2. **What it does**, in one sentence that the reader can apply elsewhere.
3. **What people usually do**, when the tutorial needs a different value.

The third point matters most when a tutorial needs a fixed value so that readers can reproduce its result. A
tutorial fixes the seed so that the reader can compare their result with the tutorial's. When working on their own,
people usually leave the seed empty. They fix it only after they get a picture they like and want to adjust. State
both, in that order. Otherwise the tutorial teaches a habit that does not help the reader later. The same applies to
any value chosen for the example and not as a recommendation.

When a control has a range, describe what happens across the range and where the example's value is in it. For
example: "near 0 almost nothing changes, and near 1 almost nothing of the source picture is kept". Then the reader
can try other values without another tutorial.

Say what happens if the reader chooses differently. "Leave it empty and you get a different picture each time" lets
the reader make the choice.

## Structure

- The layout shows which steps depend on which. Steps that do not depend on each other go at the same level, even if
  they are on the same card. Indent a step under another only when it is part of that step, and say so.
- Each step has one action. When several settings must be set together for the result to work, say that they belong
  together and why, and offer one action that sets all of them.
- A step title names the action or the setting: "Set the size", "Choose the model". It is not a slogan.
- Start every page and every step with a sentence that says what it is for. That sentence is still useful when the
  rest of the text is cut off.
- Order the content from general to detailed, so the reader can stop at any point.

## Copy at several levels of detail

Some copy is written at more than one level of detail, for example for new, comfortable and expert readers of the
same step. In that case:

- Every level states the same facts and the same usual practice. The levels differ in how much they explain. They do
  not differ in content or advice.
- The most detailed level explains how the thing works in plain words. The shortest level can assume the reader knows
  the terms, but it must still be literal and must not refer to positions.
- Every level includes the inserted values, the setting names and the links, so a reader who switches level does not
  lose track of the interface.

## Links to explanations

Every setting glyph, product term and named concept in the copy links to an explanation, wherever it appears: in a
tutorial step, in a help note, or on an overview page outside any tutorial. Provide three things:

- **On the same page**: a short explanation that the reader can open without leaving the page. It gives the
  one-sentence explanation and the usual practice.
- **One click away**: a link to the full concept or reference page. The link text says what the page covers, so the
  reader knows before following it whether it has the information they need.
- **A way back**: a breadcrumb or similar link that returns the reader to where they were, with their work kept.

Add a link where the other page becomes relevant, in the sentence that makes it relevant. Do not link to the same
page twice in one passage.

## Buttons, empty states, errors and confirmations

- A button names the result ("Send to the studio"). It does not name the mechanism ("Submit").
- An empty state says what will appear and what makes it appear.
- An error says what happened and what the reader can do. It does not describe internal details that the reader
  cannot act on.
- A confirmation says what was done, in the past tense, and where the result is, by name and not by position.

## Review checklist

Before copy is released, read each string and check:

- Would a careful reader who is not a native speaker do the right thing by following the literal words?
- Does it identify things by label or glyph, without direction or position words?
- Does it use any word that only the people who built the product would use?
- Is every simplification true, and does it agree with the rest of the product?
- Is every general statement true for every model and worker? Is every number a limit, a published suggestion or a
  labelled observation about the example shown?
- Is the scope of an example stated once per page or strip? Does every caption describe what is visible without
  repeating that scope?
- Would a reader who believed the string literally lose something that it does not mention, such as privacy, a scan
  that works, filtering or cost?
- Does each instruction explain why, and give the usual practice where it differs from the tutorial's choice?
- Does the indentation show real dependencies between steps?
- Are values inserted from the same data that produced the example?
- Can the reader open an explanation of every term and glyph from here, and return?
- Is it the shortest text that still teaches?

## Changes to this standard

These rules exist to keep copy consistent across products. Proposals to change them are welcome, where a rule is too
strict, missing, or could be better.
