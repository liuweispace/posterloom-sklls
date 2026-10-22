# Duotone Identity Stack — visual reference

Reference frames sampled from a published poster series by 设计师@郝鸣威
(Douyin video 7690585719798651387, posted 2026-09-28), used to derive the
`duotone-identity-stack` style contract.

These frames are **style references only**. They are not redistributable source
assets and are not a substitute for the user's own photograph.

## Observed system

**Subject treatment**
- One real person, repeated 2-4 times on a single canvas.
- Copies align to the vertical centreline so several eyes, noses and mouths
  coexist in one frame.
- Scale and angle vary between copies: largest copy upper-left and tilted,
  smaller copies cascade toward the centre.
- Cheeks, temples and jaw are clipped into angular, mask-like points rather
  than natural silhouettes.
- A foreground anchor occupies the lower half — either a hand entering from the
  bottom edge or a large circular disc overlapping the lower face.

**Colour**
- Strict two-ink duotone plus one accent.
- Observed ramps: crimson/raspberry into chalky white; peach/coral into
  vermilion. Near-black reserved for deepest shadow.
- Natural skin colour is removed entirely.
- One saturated accent carries the title and the small registration marks.

**Surface**
- Risograph / screen-print: visible ink grain, speckling, uneven coverage,
  slight misregistration, softened edges where ink does not take.
- Hair strands, pores and stubble stay legible inside the ink texture.

**Typography**
- Large high-contrast display serif (Didone / Bodoni italic) for the title,
  set tight into one corner on the open quadrant. Observed: *My Face*.
- Heavy neo-grotesk all-caps (Helvetica Black class) as the alternate variant.
  Observed: *MY FACE*.
- Small Song/Ming Chinese serif characters set far apart as corner markers
  (observed: 脸 / 谱 with tiny tracked pinyin beneath).
- Tiny uppercase microtype as edition marks: `NNN / 100`, date, series credit.
- Hairline orbital arcs and registration marks across the field.

## Identity rule

This style repeats one verified identity, so it is the single exception to the
skill's "never duplicate faces" rule. The identity lock stays on; only the
duplication clause is relaxed. See `../../references/style-router.md`.

## What this reference does NOT establish

- It does not prove the backend reproduces the same face across every copy.
  That still requires reference-image conditioning and per-copy face-embedding
  verification at generation time.
- Colour values are read from a compressed 576px-wide video frame, not from a
  print-ready original.