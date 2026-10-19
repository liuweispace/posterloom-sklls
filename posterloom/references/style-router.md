
# AutoStyle Router

The router ranks **32 direct visual styles** (29 general + 3 portrait-dedicated). `Controlled Hybrid` is a meta-style and is never ranked as a normal style.

## Routing sequence
1. Build the scene profile.
2. Eliminate obvious poor fits using each style's `Reject when` conditions.
3. Score the remaining styles across subject, lighting, mood, geometry, materials, palette, realism, and transformation tolerance.
4. Review the top five against the actual image.
5. Prefer the less destructive style when scores are close and identity risk is high.
6. Apply explicit user preference as a bias, not as permission to violate source truth.
7. Consider Controlled Hybrid only if:
   - top two direct styles are both strong fits;
   - their score gap is small;
   - the pair is explicitly allowed by `data/compatibility.json`;
   - one style can clearly remain primary;
   - the secondary can be restricted to one subsystem.

## Portrait routing (identity guard)

When the subject is a person and `transformation_tolerance` is not `high`/`medium-high`,
the router treats likeness as at risk and refuses to route into a face-repainting medium
(watercolor, gouache, ink wash, screenprint, riso, lithograph, paper-cut, relief print).
Such a request is redirected to an identity-safe style:

- `editorial-portrait` — magazine/interview likeness, natural skin;
- `photojournalistic` — maximum fidelity, captured moment;
- `fine-art-portrait` — painted surface with the likeness held constant.

If the user explicitly asks for heavy transformation, stylized styles remain available.
The decision is reported in `diagnostics.identity_guard`.

## Confidence

Confidence is measured **relative to the best score achievable in that profile**, not
against the absolute weight sum. A sparse profile cannot score highly in absolute terms
even when it matches perfectly, so absolute bands made nearly every route look `low`
and collapsed output onto one conservative style.

- `high` — winner leads the field by a clear margin (ratio >= 0.80, margin >= 5)
- `medium` — winner is credible but the field is close
- `low` — weak signal; a conservative style is substituted only when it matches within 3 points

The conservative override is a fallback, not a default. Inspect
`diagnostics.override` and `diagnostics.winner` to see when it fired.

## Production behavior
- Route every source image independently.
- Do not randomize.
- Do not force style diversity across a batch.
- Repeated styles are valid when the sources genuinely fit them.
- Low-confidence cases should lean toward a conservative photographic/editorial treatment.

## Deterministic helper

```bash
python scripts/rank_styles.py examples/scene-night-teahouse.json
python scripts/rank_styles.py examples/scene-portrait.json
```

The helper provides a repeatable ranking signal. The agent still performs the final visual review against the source image.