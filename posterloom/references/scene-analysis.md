
# Scene Analysis

PosterLoom always builds a scene map before style selection.

## Required fields
- `subject.type`: portrait, architecture, landscape, still-life, tea, street, performance, object, etc.
- `subject.summary`: one factual sentence.
- `subject.identity_anchors`: the smallest set of details that make this exact source recognizable.
- `environment`: factual background/context.
- `lighting`: normalized lighting cues.
- `mood`: normalized emotional cues.
- `geometry`: useful spatial/shape cues.
- `palette`: source-derived color families.
- `materials`: visible surface/material cues.
- `text_safe_zones`: regions where small text can sit without covering identity.
- `realism_value`: low, medium, high, or very-high.
- `transformation_tolerance`: low, medium, medium-high, or high.
- `user_preferences`: ratio, title, subtitle, typography size, preferred/avoided styles, hybrid permission.

## Identity anchors

Identity anchors are not generic descriptions. Prefer:
- **person:** face shape, hair, expression, pose, clothing silhouette, hand count/gesture;
- **architecture:** roof profile, tower/floor count, window and door arrangement, facade proportion, perspective;
- **vehicle/object:** overall proportions, component count, distinctive silhouette, key colors;
- **place:** mountain profile, canal/bridge relationship, landmark geometry, street direction;
- **cultural object:** authentic text, costume components, craft pattern, vessel form.

## Source truth

Never infer a place name, date, brand, historical period, ethnicity, identity, or event from appearance alone. If factual text is not supplied or legible, omit it or use a mood-based title.

## Text-safe zones

A text-safe zone has:
- low visual detail;
- enough contrast;
- no face, key hand, important sign, logo, or identity-critical geometry;
- enough margin for restrained typography.

## Example

```json
{
  "subject": {
    "type": "teahouse",
    "summary": "Traditional wooden tea-house facade at night",
    "identity_anchors": [
      "roof tile silhouette",
      "window grid",
      "warm interior light",
      "original perspective"
    ]
  },
  "environment": "dark street edge with limited background clutter",
  "lighting": ["night", "warm-light", "window-light"],
  "mood": ["quiet", "intimate", "cultural", "cinematic"],
  "geometry": ["roof-lines", "window-grid", "dark-negative-space"],
  "palette": ["amber-charcoal", "muted-green"],
  "materials": ["wood", "tile", "glass"],
  "text_safe_zones": ["upper-right dark region"],
  "realism_value": "high",
  "transformation_tolerance": "medium",
  "user_preferences": {
    "output_ratio": "3:4",
    "typography": "small",
    "hybrid_allowed": true
  }
}
```
