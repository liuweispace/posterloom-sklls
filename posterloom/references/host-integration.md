
# Host Integration

PosterLoom is an Agent Skill, not an image-generation model.

## Minimum host capability
The host agent must be able to:
1. inspect the source image;
2. read skill resources;
3. reason over the scene profile;
4. invoke an image-generation or image-editing backend **or** return the compiled prompt for another generator.

## Preferred generation behavior
When an image tool exists:
- pass exactly **one source image reference** for each generation job;
- pass the compiled prompt;
- request one finished poster;
- inspect the result using the Visual Benchmark.

When no image tool exists:
- do not pretend an image was generated;
- return the scene map, route decision, and compiled prompt.

## Batch execution
Never pass an entire batch as reference images to one generation call unless the user explicitly requests a composite.
