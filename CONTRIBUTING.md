# Contributing

Contributions are welcome.

Before opening a PR:

```bash
python posterloom/scripts/validate_repo.py posterloom
python posterloom/evals/run_evals.py
```

When changing a style, change its actual visual mechanism—not only adjectives. Update the style contract, machine-readable data, routing cues, and regressions when behavior intentionally changes.

Prompt/style changes should also be tested on real images and scored with `posterloom/references/visual-benchmark.md`.

Do not paste proprietary or third-party prompt text into PosterLoom.
