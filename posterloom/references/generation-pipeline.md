# The generation pipeline

How PosterLoom turns a photograph into finished poster images, and why each
step is built the way it is. Every claim here was measured against a real
backend, not assumed. The measurements are reproducible with the scripts in
this directory.

## The shape

```
photo
  │
  ├─▶ scene_analyze      measure: ratio, palette, structure   (pixels only)
  ├─▶ rank_styles        route to one of 35 styles             (deterministic)
  ├─▶ describe           a vision model reads the subject      (facts, no style)
  ├─▶ compact_prompt     rebuild the prompt inside the cap    (by section)
  ├─▶ generate           the image backend                     (n images, one call)
  └─▶ describe           classify the result: print or photo   (acceptance gate)
```

## Backend limits

MiniMax `image-01`, the default backend:

| Limit | Value | Consequence |
|---|---|---|
| prompt length | < 1500 characters | a 4000-8000 character PosterLoom prompt cannot be sent as-is |
| images per call | 1, 3, 5, 9 | three posters is one request, not three |
| aspect ratios | 8 values, **not** `3:5` | the two zine styles are designed for `3:5` and must be mapped |
| reference image | one, base64 | usable, but see the section below |

The prompt cap and the ratio gap are declared in `data/backends.json` so the
code adapts to them instead of discovering them at runtime. The ratio mapping
always reports the substitution — shipping a 9:16 poster when the style asked
for 3:5 without saying so is exactly the kind of thing that looks fine and is
wrong.

## Finding 1 — vocabulary beats length

The first hypothesis was that long prompts failed and short ones worked. That
was wrong. Two prompts of identical structure produced different *media*:

```
"a young man's head and shoulders, hair rendered as a solid flat black mass,
 features simplified into hard flat shapes"        -> flat print

"a young man with thick tousled black hair and a coral shirt,
 looking down to the left"                          -> photograph
```

The second reads as a description of a photograph, so the model renders one.
Photographic vocabulary — *photograph*, *skin texture*, *pores*, *soft
shadows*, *gradients*, *studio lighting* — pulls the model back toward
continuous tone.

`compact_prompt.to_print_language()` rewrites that vocabulary before it
reaches the backend, and the prompt opens with a medium statement naming the
print process and the ink colours outright.

## Finding 2 — attaching the photo forces a photograph

This is the most consequential finding in the project.

With the **identical prompt**, only the attachment differing:

| Request | Result |
|---|---|
| no `subject_reference` | flat print |
| `subject_reference` = the source photo | photograph |

Adding "render the whole image as flat printed ink on paper, NOT as a
photograph" to the prompt did not change the outcome. The attachment itself
carries the photographic rendering.

So the pipeline **does not attach the photo**. A vision model reads it first
and the image is generated from words. The likeness is now a text description
rather than a pixel copy — a real trade-off, and the reason
`--send-reference` exists as an opt-in.

## Finding 3 — pixel statistics cannot tell a print from a photograph

The obvious cheap acceptance gate is a pixel metric. It does not work. On 13
labelled samples (6 true prints, 7 photographs):

| Metric | True prints | Photographs |
|---|---|---|
| flat area ratio | 0.62 - 0.83 | 0.70 - 0.82 |
| ink ratio | 0.58 - 0.84 | 0.42 - 0.63 |
| distinct colour buckets | 16 - 34 | 33 - 38 |
| mean edge strength | 12 - 23 | 10 - 16 |

The ranges overlap almost completely. A photograph with a duotone treatment and
a true flat print have nearly identical colour histograms; what separates them
is texture microstructure, not colour.

A vision model separates them correctly: 12 of 13 on the same labelled set.
That is what `describe.classify_style()` does, and it is the acceptance gate
for generation.

## Finding 4 — never truncate mid-sentence

The first implementation clipped the style mechanism to a character budget. That
cut it inside a clause — `...Exactly one copy is the canonical identity anchor
and must match the source face precisely...` — and the operative instruction
"repeat as a stack" was lost. The output was a single portrait instead of a
stack: the style's core failure mode, produced by the prompt builder rather
than by the model.

`compact_prompt._first_sentences()` takes whole sentences and drops the last
one if it does not fit. The same applies to the subject description and the
source clause.

## Finding 5 — three images from one call are three samples, not three designs

`n=3` in a single request returns three samples of the same prompt. Measured on
the `duotone-identity-stack` style:

| | sample 1 | sample 2 | sample 3 |
|---|---|---|---|
| faces | 4 | 5 | 4 |
| arrangement | vertical column | overlapping cascade | feature stack |
| crop | tight heads | tight heads | extreme facial close-up |

The rendering detail varies — grain, edge softness, how the copies overlap. The
composition does not. Three prints of one design is not what "give me three"
means, and no amount of `n` changes it.

The API takes one prompt per request, so distinct designs require distinct
requests. `variation.py` supplies a per-variant arrangement directive; `render.py`
issues one request per variant.

**The arrangement is its own section.** Putting the variant inside the LAYOUT
section failed twice, for two different reasons:

1. *Prepending it* — a style's composition often states a default arrangement
   ("build a vertical stack along the centerline"). The variant contradicted it
   and lost, so the sheet came out as the style's default. The later
   instruction wins, so the variant has to come **after**.
2. *Sharing the section* — the budget enforcement clips a section by whole
   sentences from the front, so the variant was the part that got cut. The
   sheet silently fell back to the style's default arrangement. A section of its
   own cannot be clipped into a different meaning.

`ARRANGEMENT:` is therefore a separate section, placed after `LAYOUT:`, and it
survives the absolute floor — it is the only thing distinguishing one sheet of
the set from another.

## Finding 6 — the print mechanism must survive the arrangement

Adding an arrangement costs about 150 characters, and the naive result was that
the STYLE section — which carries the posterised edges, the ink surface and the
discipline that keeps a sheet a print — was evicted entirely.

The sheets then came back as **duotone photographs**: correct palette, wrong
medium. Measured before and after:

| | before | after |
|---|---|---|
| `column` | flat two-colour print | flat two-colour print |
| `cascade` | duotone photograph | flat two-colour print |
| `pair` | duotone photograph | flat two-colour print |

So when an arrangement is present, the STYLE section becomes required and is
clipped last. The medium wins over the variety: a set of three wrong-medium
posters is worse than one right-medium poster.

The clipping loop also has to shrink the arrangement and the mechanism, not just
the subject and the layout. Without that, the loop could not reach a fitting
combination, fell through to the absolute floor, and dropped LAYOUT,
ARRANGEMENT and STYLE together — for 92 of the 630 style-and-variant
combinations.

## The variants obey the identity mode

A variant may only change the arrangement. It may not introduce a second face
into a `single`-mode style, and it may not change the palette — that would be a
different style, not a different take on this one. So the pools are keyed by
identity mode:

| mode | pool | what varies |
|---|---|---|
| `repeat` | `REPEAT_VARIANTS` | column, echo, cascade, cluster, pair — arrangements of repeated copies |
| `abstract` | `ABSTRACT_VARIANTS` | the same arrangements, worded as illustration |
| `single` + face | `SINGLE_VARIANTS` | crop, offset, scale — never a second face |
| no face | `SCENE_VARIANTS` | wide, tight, offset, diagonal, band |

Each directive is exactly one sentence. The budget clips by whole sentences, so
a two-sentence variant could lose its second half and leave an instruction the
model cannot act on.

## What the budget may not touch

The prompt is assembled from sections and the budget is spent top down:

| Section | Why it is protected |
|---|---|
| `medium` | decides print vs photograph |
| `source` | carries `NO PHOTOGRAPHY` for semantic-reference styles — a hard constraint |
| `subject` | carries the identity facts the lock refers back to |
| `LAYOUT` | without it a "stack" style renders one portrait |
| `ARRANGEMENT` | without it every sheet in the set is the same design |
| `STYLE` | without it the sheet comes back as a duotone photograph — the print mechanism |
| `COLOUR` | without it the model picks its own palette (usually black and cream) |
| `IDENTITY LOCK` | never dropped — it is what makes unattended sending safe |
| `AVOID` | the negative constraints; recoverable from the style contract |

The subject has a floor of about 230 characters. Cutting it to a stub while
keeping a full lock produces a *dangling* lock: the prompt insists on matching
features it never specified.

`scripts/check_prompt_budget.py` asserts all of this across every style and
scene combination, and runs as part of `selftest`.

## The identity lock is a prompt constraint, not a guarantee

No image API verifies a face. The lock binds face shape, eye shape and
spacing, brow, nose, mouth, jawline, hairline, skin tone, age, expression and
gaze **in the prompt**. Whether the backend honours it is not knowable from
the request. After generating, compare the face against the source on the
seven identity-critical points; if any differ, regenerate.

## Reproducing the measurements

```bash
# classify a generated image as a print or a photograph
python3 scripts/describe.py poster.jpg classify

# read a subject's identity card
python3 scripts/describe.py photo.jpg identity

# check the budget and section preservation across all styles
python3 scripts/check_prompt_budget.py
```

## Credentials

The backend key is read from `MINIMAX_API_KEY` in the environment or
`~/.hermes/.env`. It is never written into a prompt, a log line, a JSON
result, the repository, or a generated image. `data/backends.json` names the
environment variable and nothing else.

## Privacy

The source photo is uploaded to the image backend's vision API when the
pipeline describes it. That is the one place user content leaves the
machine. The prompt itself contains no file paths.
