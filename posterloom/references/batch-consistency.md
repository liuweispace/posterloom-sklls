
# Batch Consistency

Batch consistency means **consistent quality**, not forced visual sameness.

## Rules
- Route each source independently.
- A style may repeat if it is genuinely the best fit.
- Do not rotate through styles just to make the batch look diverse.
- Keep output ratio, typography restraint, identity preservation, and QA threshold consistent.
- Do not let one source image contaminate another source's prompt or reference set.
- Never generate one composite from a batch unless explicitly requested.

## Batch planner
```bash
python scripts/batch_plan.py examples/batch-profiles.json
```

The planner warns about repeated styles but does not change correct choices.
