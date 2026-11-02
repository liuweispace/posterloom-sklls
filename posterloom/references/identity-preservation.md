
# Identity Preservation

PosterLoom is source-led. Style never has permission to replace the source.

## Priority order
1. subject identity;
2. spatial logic and perspective;
3. source-specific materials and cultural details;
4. lighting motivation;
5. source-derived palette;
6. style expression;
7. typography.

If a style conflicts with a higher-priority item, weaken the style.

## The lock needs a test the source can actually fail

A likeness check is only evidence if the source could have produced a
different face. A flat vector pictogram, a low-detail avatar or a heavily
stylised figure cannot: any photoreal result already "passes" against it,
so the result is the absence of a counter-example, not a verification.

Use a real photograph with features that are individually checkable — a
distinctive haircut colour and cut, eye shape, nose width, brow thickness,
an open smile. Then compare feature by feature. A style that reproduces
the source against a real face but was only ever checked against an
avatar has not been checked.

**Words cannot carry identity.** A written description of a face
describes *a* face, not *this* face, so a text-only pipeline invents a
face that fits the description. Measured on a real photographic source,
the same prompt with and without the source photo attached:

| feature | photo attached | words only |
|---|---|---|
| hair | platinum pixie, preserved | long brown hair, invented |
| eyes | almond, preserved | round and light |
| nose | narrow and straight, preserved | broad and round |
| expression | closed-lip smile | the open smile, lost |

So for a photographic style the source photo must be attached to the
image request. See [generation pipeline](generation-pipeline.md) for why
print styles do the opposite.

## Human subjects
Protect:
- face structure and expression;
- body count;
- pose;
- hand count and gesture;
- clothing silhouette;
- visible age-relevant appearance.

Do not beautify, age-shift, gender-shift, costume-shift, or identity-shift unless explicitly requested.

## Architecture
Protect:
- silhouette;
- roof/tower/floor count;
- window and door relationships;
- facade proportion;
- perspective;
- authentic signage placement.

## Objects
Protect:
- shape and proportion;
- count;
- distinctive components;
- real labels when legible;
- material and color anchors.

## Identity risk
When identity risk is high, reduce transformation strength or select a more photographic style.

## Identity-lock modes

The facial lock (`scripts/face_identity.py`) has three modes. The mode is chosen by the
routed style, never by the model, and it is reported as `identity_mode` in the route.

| Mode | Applies to | What the lock demands |
|---|---|---|
| `single` | every other style | reproduce the face: shape, eyes, brow, nose, mouth, jawline, hairline, skin tone, age, expression, gaze |
| `repeat` | `duotone-identity-stack` | every copy is the same verified person; no drift into another face |
| `abstract` | `scene-distillation-zine` | derive, do not invent: head shape, head angle, hairline, age cues, gesture and gaze must trace to the source, but rendered as illustration, never as a photographic likeness |

`abstract` is not a weakened lock. It is the same guarantee restated in the only form
the style can honour, and it adds negative constraints of its own
(`no photorealistic face`, `no celebrity lookalike`, `no model-default face`,
`no face averaged toward a composite`). The delivery gate changes accordingly: it checks
derivation rather than pixel-level facial match, and explicitly does not demand
photographic fidelity.

Generalize the rendering, never the identity.
