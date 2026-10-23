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

## Finding 5 — what the budget may not touch

The prompt is assembled from sections and the budget is spent top down:

| Section | Why it is protected |
|---|---|
| `medium` | decides print vs photograph |
| `source` | carries `NO PHOTOGRAPHY` for semantic-reference styles — a hard constraint |
| `subject` | carries the identity facts the lock refers back to |
| `LAYOUT` | without it a "stack" style renders one portrait |
| `COLOUR` | without it the model picks its own palette (usually black and cream) |
| `IDENTITY LOCK` | never dropped — it is what makes unattended sending safe |
| `STYLE` | the mechanism prose; recoverable from the style contract |
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
