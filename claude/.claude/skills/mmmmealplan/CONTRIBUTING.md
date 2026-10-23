# Contributing to Mmmmealplan

Thanks for thinking about contributing. The most useful PRs are small.

## Recipes

Recipe contributions are very welcome — every saved recipe makes the cold-start experience better for the next person.

### Adding a recipe

1. Pick the right slot directory: `recipes/breakfast/`, `recipes/lunch/`, or `recipes/dinner/`.
2. Filename = lowercase slug, words joined by hyphens, no special chars: `red-lentil-dahl-with-rice-yogurt.md`.
3. Use the format in [`lib/recipe-template.md`](lib/recipe-template.md). Required frontmatter: `name`, `slot`, `servings`, `time_minutes`, `tags`, `ingredients`. `nutrition_per_serving` is optional but encouraged.
4. Use canonical ingredient names that resolve at Migros. German names work best (e.g., `kartoffeln`, not `potatoes`). Quantities are per single serving with units (`200g`, `15ml`, `0.5`).
5. Use the standard tag vocabulary so config restrictions match:
   - Dietary: `vegetarian`, `vegan`, `pescatarian`
   - Allergens: `lactose-free`, `gluten-free`, `nut-free`, `contains-lactose`, `contains-gluten`, `contains-pork`, `contains-shellfish`
   - Style: `high-protein`, `low-carb`, `no-cook`, `one-pan`, `meal-prep`
   - Cuisine tags are free-form: `italian`, `asian`, `mexican`, etc.
6. Steps under `## Steps` should be cookable from a tired weeknight brain. Times, temperatures, and "while X is happening, do Y" are useful.

### Recipe sanity check

Before opening a PR, run the skill against a config that includes your recipe in `fixed_slots` — at minimum the planner should accept the file (no validation error) and the shopping list should resolve every ingredient against Migros.

## Bug reports

Open an issue with:

1. The slash command you ran.
2. Your `config.yaml` (redacted as needed).
3. The error / unexpected output.
4. The output of `claude mcp list` (to confirm `migros` is registered).

## Code / SKILL.md changes

The skill logic lives entirely in [`SKILL.md`](SKILL.md) and the helper docs in `lib/`. Changes there change behaviour. Two things to keep in mind:

- The skill runs in an LLM context. New steps are followed only if they're explicit and clearly numbered.
- Before submitting, run the skill end-to-end on at least one config and verify both output files are well-formed.

## License

By contributing, you agree your contributions are licensed under the project's [MIT License](LICENSE).
