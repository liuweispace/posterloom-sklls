
# Anti-Slop QA

Reject or revise outputs that show generic AI aesthetics unrelated to the source.

## Global avoid list
- default purple-blue AI gradient;
- excessive bloom or glow;
- random fog;
- random particles;
- fake film borders or light leaks;
- fantasy sky;
- invented landmarks;
- duplicate subjects;
- malformed hands or architecture;
- plastic skin;
- arbitrary bokeh;
- random floating objects;
- giant headline that hides the photograph;
- decorative shapes with no source relationship;
- one-click-filter appearance;
- uniform texture over every surface.

## Source specificity test
Ask: could the same prompt/result have been produced from an entirely different photo with almost no changes?  
If yes, the result is too generic.

## Style specificity test
Ask: can a reviewer identify the selected style's **mechanism**, not merely its label?  
If no, the style is under-expressed.

## Iteration discipline
Change one major variable at a time:
- crop;
- transformation strength;
- palette;
- texture;
- typography;
- secondary style role.

Avoid changing everything simultaneously after a failure.
