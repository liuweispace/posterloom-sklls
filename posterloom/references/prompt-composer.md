
# Prompt Composer

The composer combines:
1. global source-truth rules;
2. scene profile;
3. primary style contract;
4. optional Controlled Hybrid role;
5. typography decision;
6. output constraints;
7. negative constraints.

## Compilation order
- Source binding
- Identity anchors
- Scene facts
- Single-poster output rule
- Primary style mechanism
- Optional secondary subsystem
- Typography
- Hard negatives
- Final QA reminder

## Grounding
Do not leave vague adjectives such as “beautiful”, “premium”, or “cinematic” unsupported. Name the actual:
- light source;
- geometry;
- material;
- palette;
- edge behavior;
- print/painterly mechanism;
- text-safe zone.

## Helper
```bash
python scripts/compose_prompt.py examples/scene-night-teahouse.json
```
