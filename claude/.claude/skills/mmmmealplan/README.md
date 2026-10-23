<p align="center">
  <img src="assets/header.png" alt="Mmmmealplan" width="640">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Claude%20Code-skill-orange" alt="Claude Code skill">
  <a href="https://github.com/lewpgs/migros-mcp"><img src="https://img.shields.io/badge/Powered%20by-Migros%20MCP-red" alt="Powered by Migros MCP"></a>
</p>

> *Mmm + Migros + Meal-planning.* A Claude Code skill that turns a YAML config plus a recipe library into a real weekly plan: it pulls live promotions and nutrition data from the (unofficial) [Migros MCP](https://github.com/lewpgs/migros-mcp), respects your macros and restrictions, and writes the plan and a categorised shopping list straight to disk.

## What it does

Run `/mmmmealplan` and you get:

- A weekly meal plan (Mon–Sun) tailored to your macros, restrictions, and meal cadence.
- A categorised Migros shopping list with quantities aggregated across the week, biased toward current promotions.
- Per-day macro verification with ±10% flags (no silent rebalancing — gaps surface inline).
- Optional: split-slot meals (one pan, two plates) for households where one person counts macros and the other does not.
- A growing recipe library: when the planner invents a NEW dish you like, save it back to disk with one prompt.

## Features

- **Library + LLM hybrid.** Reuses recipes you've saved (frontmatter-tagged Markdown) and lets the model fill gaps with NEW recipes that respect your equipment, time caps, and restrictions.
- **Recently-used dampening.** Reads the last two plans and biases the model away from repeating dishes.
- **Promo-aware.** Calls `mcp__migros__get_promotions` and lets discounted ingredients influence the menu.
- **Real allergen check.** After Migros resolves real products, their German allergen strings are mapped against your `restrictions` (`lactose-free`, `gluten-free`, `nut-free`, etc.) and conflicts are flagged inline.
- **Quantity-correct shopping list.** Per-serving recipe ingredients × effective servings × days, rounded up to buyable units.
- **Failure modes documented.** MCP unreachable → abort; partial nutrition → annotate; promotions empty → continue without bias.

## Requirements

- [Claude Code](https://claude.ai/download) installed and working.
- The [Migros MCP](https://github.com/lewpgs/migros-mcp) server installed and registered with Claude Code (`mcp__migros__*` tools must be reachable).

### Installing the Migros MCP

From the [migros-mcp README](https://github.com/lewpgs/migros-mcp):

```bash
# Anonymous (sufficient for this skill — search, details, promotions all work)
claude mcp add migros -- npx -y migros-mcp
```

Then verify it's registered:

```bash
claude mcp list
```

You should see `migros` listed. Restart any open Claude Code sessions afterward.

## Install

```bash
git clone https://github.com/<you>/mmmmealplan.git
cd mmmmealplan
./install.sh
```

`install.sh` symlinks the package into `~/.claude/skills/mmmmealplan/` and bootstraps `config.yaml` from the example. If you'd rather copy than symlink (e.g., to keep the active version pinned), edit `install.sh` accordingly — it's six lines of shell.

Alternatively, install manually:

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)" ~/.claude/skills/mmmmealplan
cp ~/.claude/skills/mmmmealplan/config.yaml.example ~/.claude/skills/mmmmealplan/config.yaml
```

## Configure

Edit `~/.claude/skills/mmmmealplan/config.yaml`. Two examples ship in `config.yaml.example`:

- **Single eater** — straightforward macros + cadence.
- **Two-eater split slot** — household_size 2, one breakfast for the macro-tracked eater, a different one for the other person, shared dinner.

The schema and validation rules live in [`SKILL.md`](SKILL.md). The short version:

- `macros` — daily targets for the *primary* eater.
- `restrictions` — hard. Recipes whose tags violate any item are rejected. After ingredient resolution, real Migros allergen strings are also checked.
- `meal_cadence` — how many breakfasts/lunches/dinners per week (0–7). Set unused slots to 0.
- `fixed_slots` — lock specific recipes into specific slots. Either a single filename string, or a list of `{recipe, servings, is_primary}` for split slots.
- `equipment` — limits which recipes the planner picks.

## Usage

```
/mmmmealplan              # plan the next 7 days starting Monday
/mmmmealplan --days 3     # plan 3 days starting today
```

Output lands in:

- `~/.claude/skills/mmmmealplan/plans/<YYYY-WXX>.md`
- `~/.claude/skills/mmmmealplan/shopping-lists/<YYYY-WXX>.md`

For non-week-aligned windows (`--days 3`, `--days 5`, etc.), filenames use `YYYY-MM-DD` instead of `YYYY-WXX`.

## How it works (one paragraph)

The skill loads your config, scans the recipe library, computes how many slots need filling per day, queries Migros for current promotions, and asks the model to produce a JSON plan that respects every constraint (hard restrictions absolute, recently-used soft, ingredient overlap maximised, promotions favoured). It then resolves every canonical ingredient against the Migros catalogue (search → product details → in-session cache), aggregates quantities, runs an allergen check on real product data, and verifies per-day macros for the primary eater. Finally it renders the plan and shopping-list templates and writes them to disk. Any recipes the model invented are offered for one-click save into the library.

## Adding your own recipes

Drop a Markdown file into `recipes/breakfast/`, `recipes/lunch/`, or `recipes/dinner/` with frontmatter like this:

```yaml
---
name: Sheet-pan halloumi traybake
slot: dinner
servings: 1
time_minutes: 25
tags: [vegetarian, high-protein, one-pan]
ingredients:
  - halloumi: 150g
  - kartoffeln: 250g
  - cherry-tomaten: 200g
  - olivenöl: 15g
nutrition_per_serving:        # optional — computed from Migros data if absent
  protein_g: 32
  carbs_g: 54
  fat_g: 38
  kcal: 670
---

## Steps
1. ...
2. ...
```

Use ingredient names that map cleanly to Migros search results (German names work best). The full template is in [`lib/recipe-template.md`](lib/recipe-template.md).

## Output samples

A real plan and shopping list look like this:

```
~/.claude/skills/mmmmealplan/plans/2026-W19.md
# Week 2026-W19 Meal Plan (2026-05-04 – 2026-05-10)
...
- Mon (2026-05-04): Pan-seared halloumi with potatoes & asparagus *(library)*
- Wed (2026-05-06): Veggie schnitzel with potatoes & green salad *(library)*
- Thu (2026-05-07): Red lentil dahl with rice & yogurt *(NEW — save?)*
...

~/.claude/skills/mmmmealplan/shopping-lists/2026-W19.md
**Total: CHF 103.87**

## Produce
- [ ] Kartoffeln mehligkochend, 1kg — CHF 1.00 (PROMO -41%)
- [ ] Spargelspitzen grün, 300g — CHF 4.75 (PROMO -27%)
...
```

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `config.yaml not found` | Copy from `config.yaml.example` and edit. |
| `Migros MCP server unreachable` | Run `claude mcp list` — `migros` should be there. If not, see [Installing the Migros MCP](#installing-the-migros-mcp). Restart Claude Code after registering. |
| Recipe filename in `fixed_slots` doesn't resolve | Filename is the slug without `.md`. Check `recipes/<slot>/` for the exact name. |
| Allergen flag fires on a recipe you trust | Tag-level says one thing, real product says another. Adjust the recipe's tags or swap the ingredient — the conflict is surfaced, not enforced. |
| All macros way under target | Likely `meal_cadence: lunch: 0`. Add a lunch slot or count breakfasts as denser. The skill flags the gap; it does not auto-rebalance. |
| German ingredient names don't resolve | Try a more generic synonym (e.g., `tomaten-pelati` → `pelati`). The skill retries with relaxed queries; if still no result, the ingredient is marked `[unavailable]` rather than crashing the run. |

## Limitations

- Migros-only. The product catalogue, prices, and allergen strings all come from Migros. If you shop elsewhere, the shopping-list pricing won't match (recipes still work — only the cost line is Migros-specific).
- German-language ingredient names match the catalogue best.
- The planner does not place orders. It generates a list; you go shopping.
- Promotions data is fetched at run time and reflects the catalogue *now*, not the day you shop.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Recipe contributions especially welcome — drop them in a PR.

## Disclaimers

See [DISCLAIMERS.md](DISCLAIMERS.md). Short version:

- **Not affiliated with Migros.** This project depends on the [Migros MCP](https://github.com/lewpgs/migros-mcp), which itself uses the unofficial Migros endpoints. Neither project is associated with, endorsed by, or supported by Migros.
- **Nutrition is informational, not medical advice.** Macros and allergen flags are approximations. Always verify product labels for definitive allergen and dietary information.
- **AI-generated recipes can hallucinate.** Read NEW recipes before cooking — the model can produce plausible-looking dishes with technique gaps or unsafe combinations.
- **Pricing accuracy.** Promotions and prices reflect what the Migros API returns at run time. The store may charge differently.
- **Use at your own risk.** No guarantees of correctness, completeness, or fitness for any purpose.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

- [@lewpgs](https://github.com/lewpgs) for the Migros MCP server, without which none of this exists.
- The Claude Code team for the skills system.
