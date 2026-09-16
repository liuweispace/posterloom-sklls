# PosterLoom v1.0.0 — Engineering Release Report

Generated: 2026-09-16

## Status

**Engineering validation: PASS**

This release has been locally checked for repository structure, Agent Skill metadata, style-library counts, hybrid compatibility data, routing regressions, prompt compilation, prompt validation, helper-script syntax, JSON integrity, and local installation.

Engineering validation is intentionally kept separate from visual validation: image quality still depends on the host image-generation/editing backend and the source image.

## Verified package facts

- 29 direct Gold visual styles
- 1 Controlled Hybrid meta-style
- 30 style contracts total
- 74 explicit compatible Hybrid pairs
- 30 routing regression cases
- `SKILL.md`: 85 lines
- one-source / one-poster hard rule
- restrained typography rule
- identity-preservation QA
- anti-slop QA
- 10-axis Visual Benchmark with default 17/20 pass threshold
- standard-library-only Python helper scripts
- local installer smoke-tested successfully

## Repository validation

```text
VALIDATION PASS
- direct styles: 29
- meta styles: 1
- style contracts: 30
- compatible hybrid pairs: 74
- SKILL.md lines: 85
- legacy-name scan: clean
```

## Routing regression

```text
Routing regression cases: 30
Exact primary matches: 30/30
PASS
```

## Prompt smoke test

Prompt compilation return code: `0`  
Prompt validation:

```text
PASS: source binding, single-poster rule, style block, negatives, and final QA are present.
```

Example route:

- Primary: `moody-night-editorial`
- Fallback: `tea-house-minimal`
- Confidence: `high`

## Visual validation status

The repository includes the rubric and benchmark template, but a broader real-photo, multi-backend image benchmark remains appropriate future work for v1.1. The README does not claim that engineering tests guarantee beautiful output on every generator.
