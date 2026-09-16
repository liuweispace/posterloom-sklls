---
name: posterloom
description: Analyze source photos, preserve identity anchors, adaptively route each image to one of 29 direct poster styles or a constrained hybrid, reframe composition, apply restrained typography, compile generation prompts, and quality-check outputs. Use when a user wants a real photo transformed into a polished editorial, travel, cultural, painterly, print, conceptual, or modern-design poster, including batches of independent posters.
license: MIT
compatibility: Requires an agent that can inspect images. Final image creation also requires an image-generation or image-editing tool; otherwise return the compiled prompt and route decision. Helper scripts use Python 3.9+ standard library only.
metadata:
  version: "1.0.0"
  tagline: "Adaptive Photo-to-Poster Skill"
---

# PosterLoom

**Adaptive Photo-to-Poster Skill**

PosterLoom turns real source photographs into art-directed posters through scene analysis, adaptive style routing, source-aware prompt composition, restrained typography, and explicit visual QA.

## Use When
- A user wants a photo turned into a finished poster rather than a simple filter.
- A source image should be automatically matched to an appropriate visual direction.
- A batch of photos should become independent poster artworks.
- The task benefits from preserving real subject identity while changing composition, medium, texture, or design language.
- The user wants small, refined typography instead of oversized headline treatment.

## Don't Use When
- The user only wants basic exposure, crop, denoise, or color correction with no poster transformation.
- The request is explicitly for a collage or moodboard; follow that request instead of PosterLoom's one-source/one-poster default.
- No source image exists and the request is pure text-to-image; use a general image-generation workflow.
- The host cannot inspect images and the user expects automatic scene-aware routing; ask for a textual scene description or return a manual prompt workflow.

## Workflow
1. **Bind one source image to one job.** In a batch, isolate every source. Never let multiple reference images bleed into one generation.
2. **Analyze the scene.** Build a scene profile using [references/scene-analysis.md](references/scene-analysis.md).
3. **Lock identity anchors.** Read [references/identity-preservation.md](references/identity-preservation.md).
4. **Route the style.** Rank 29 direct styles using [references/style-router.md](references/style-router.md) and `scripts/rank_styles.py` when available.
5. **Load only the chosen style contract.** Read the relevant file under `styles/`. Do not bulk-load all 30 contracts unless auditing the library.
6. **Consider Controlled Hybrid only after routing.** It is a meta-style, not a normal filter. Use it only when two compatible direct styles are both strong fits and the secondary can control one subsystem.
7. **Compose the prompt.** Follow [references/prompt-composer.md](references/prompt-composer.md) or run `scripts/compose_prompt.py`.
8. **Generate one finished poster.** Default to 3:4 vertical unless the user requests another ratio. Use exactly one source image reference per generation job.
9. **Apply restrained typography.** Follow [references/typography.md](references/typography.md). If text rendering is unreliable, prefer a second typography pass when tooling allows.
10. **Quality-check the result.** Use [references/anti-slop.md](references/anti-slop.md) and [references/visual-benchmark.md](references/visual-benchmark.md).
11. **For batches, repeat independently.** Follow [references/batch-consistency.md](references/batch-consistency.md). Do not force style diversity.
12. **If no image tool exists, be transparent.** Return the scene map, selected style, and compiled prompt instead of claiming an image was generated.

## Rules
- **Source first.** The uploaded photograph is the factual and visual anchor.
- **One source -> one poster.** Never create a collage, contact sheet, moodboard, scrapbook, album, or multi-panel output unless the user explicitly requests it.
- **Identity outranks style.** If stylization damages a face, pose, architecture, object geometry, cultural detail, or material truth, reduce transformation.
- **No invented facts.** Do not fabricate people, brands, dates, landmarks, signatures, seals, locations, historical claims, or unreadable text.
- **No fake characters.** Never invent Chinese or other non-Latin characters. Use only verified source text or user-provided wording.
- **Typography stays small.** Text normally occupies 5–10% or less of the visual area and never covers identity-critical regions.
- **AutoStyle is analytical, not random.** Score scene features, apply reject conditions, then review the top candidates against the actual image.
- **Do not force batch variety.** Repeated styles are allowed when they are actually the best match.
- **Controlled Hybrid stays controlled.** One primary style at roughly 80%; one compatible secondary style at roughly 20%; the secondary controls one subsystem only.
- **Anti-slop is mandatory.** Avoid generic AI gradients, glow, fog, particles, fake film borders, malformed structure, duplicated subjects, and one-click-filter appearance.
- **Engineering validation is not visual validation.** Passing scripts/evals does not prove every image backend will produce a visually excellent result.

## Examples
- "Turn this night tea-house photo into a poster." -> analyze -> route -> likely night/tea editorial direction -> compile -> generate one 3:4 poster.
- "Make these eight travel photos into posters." -> eight isolated jobs -> route each independently -> eight outputs, even if some styles repeat.
- "Keep it very realistic with tiny type." -> bias toward photographic/editorial styles and lower transformation strength.
- "Use watercolor if it truly fits." -> route normally; use Transparent Watercolor only when source cues support it.
- "Mix cinematic and ink." -> verify compatibility; if both fit, use Controlled Hybrid with one declared secondary subsystem.

## Edge Cases
- **Low routing confidence:** choose the least destructive photographic/editorial option.
- **No text-safe zone:** omit text or create natural breathing room by crop/extension; never cover the subject.
- **Unreadable sign/calligraphy:** preserve it visually when possible but do not rewrite it as invented text.
- **Generator cannot render type well:** generate artwork first and add typography in a second pass when possible.
- **Multiple uploaded images cause reference contamination:** process one file reference at a time.
- **A requested style conflicts with identity:** preserve identity and weaken the style.
- **No image-generation tool:** return the compiled prompt and route decision; do not claim completion.

## References
- [Scene analysis](references/scene-analysis.md)
- [Style router](references/style-router.md)
- [Prompt composer](references/prompt-composer.md)
- [Composition](references/composition.md)
- [Identity preservation](references/identity-preservation.md)
- [Typography](references/typography.md)
- [Anti-slop](references/anti-slop.md)
- [Batch consistency](references/batch-consistency.md)
- [Visual benchmark](references/visual-benchmark.md)
- [Host integration](references/host-integration.md)
- [Originality and scope](references/originality.md)
- Style contracts live under `styles/`; machine-readable routing data lives under `data/`.
