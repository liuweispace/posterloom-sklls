
# AutoStyle Router

The router ranks **29 direct visual styles**. `Controlled Hybrid` is a meta-style and is never ranked as a normal style.

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

## Production behavior
- Route every source image independently.
- Do not randomize.
- Do not force style diversity across a batch.
- Repeated styles are valid when the sources genuinely fit them.
- Low-confidence cases should lean toward a conservative photographic/editorial treatment.

## Deterministic helper

```bash
python scripts/rank_styles.py examples/scene-night-teahouse.json
```

The helper provides a repeatable ranking signal. The agent still performs the final visual review against the source image.
