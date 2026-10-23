---
name: mmmmealplan
description: Generate a personalized weekly meal plan and Migros shopping list from user preferences (macros, restrictions, meal cadence, fixed slots). Uses the Migros MCP for promotions, ingredient lookup, and nutrition verification. Triggers on '/mmmmealplan', 'plan my meals', 'meal plan', 'weekly menu', 'grocery list for the week'.
---

# Mmmmealplan

Generate a weekly meal plan and Migros shopping list.

> *Mmm + Migros + Meal-planning.* A Claude Code skill that turns a YAML config + a recipe library into a real weekly plan: it pulls live promotions and nutrition data from the unofficial [Migros MCP](https://github.com/lewpgs/migros-mcp), respects your macros and restrictions, and writes the plan and a categorised shopping list straight to disk.

## Invocation

- `/mmmmealplan` — plan the next 7 days starting Monday
- `/mmmmealplan --days N` — plan the next N days starting today

## Prerequisites

- `~/.claude/skills/mmmmealplan/config.yaml` must exist (copy from `config.yaml.example`)
- The Migros MCP server (`mcp__migros__*`) must be available — see [README](README.md) for install steps

## Configuration

Read `~/.claude/skills/mmmmealplan/config.yaml` at the start of every run. If the file does not exist, output:

```
config.yaml not found at ~/.claude/skills/mmmmealplan/config.yaml.
Copy config.yaml.example and edit it to your preferences:

  cp ~/.claude/skills/mmmmealplan/config.yaml.example ~/.claude/skills/mmmmealplan/config.yaml

Then re-run /mmmmealplan.
```

Then stop. Do not proceed.

### Schema

| Field | Type | Required | Notes |
|---|---|---|---|
| `household_size` | int | yes | Default servings count if `slot_servings` is not set for a slot |
| `slot_servings.breakfast` | int | optional | Override servings just for breakfast (e.g., 2 people share breakfast but only 1 has dinner). Default: `household_size` |
| `slot_servings.lunch` | int | optional | Same; default: `household_size` |
| `slot_servings.dinner` | int | optional | Same; default: `household_size` |
| `macros.protein_g` | int | yes | Daily target in grams (applies to the primary eater — see `is_primary` below) |
| `macros.carbs_g` | int | yes | Daily target in grams |
| `macros.fat_g` | int | yes | Daily target in grams |
| `macros.kcal` | int | yes | Daily target |
| `restrictions` | list[str] | yes | Hard constraints; recipes violating these are rejected |
| `dislikes` | list[str] | yes | Soft; avoid when possible |
| `meal_cadence.breakfast` | int 0-7 | yes | Days per week this slot is consumed (per-week; scaled pro-rata for shorter windows) |
| `meal_cadence.lunch` | int 0-7 | yes | Same |
| `meal_cadence.dinner` | int 0-7 | yes | Same |
| `fixed_slots.<slot>` | str OR list | optional | Either a single recipe filename (everyone in the slot eats the same) **or** a list of `{recipe: <filename>, servings: <int>, is_primary: <bool>}` entries to split the slot across people. Sum of `servings` in a list must equal the slot's effective servings count |
| `constraints.weeknight_dinner_max_minutes` | int | optional | Time ceiling Mon-Thu |
| `equipment` | list[str] | yes | Available cooking equipment |

### Validation rules

Before generating a plan, validate:

1. All required fields present.
2. For each `fixed_slots` entry (or each item if it's a list), the corresponding recipe file exists.
3. For each `fixed_slots` entry (or each item if it's a list), the recipe's tags do not violate any item in `restrictions`. (E.g., a fixed breakfast tagged `contains-lactose` with restriction `lactose-free` is a conflict.) This is a tag-based check; for ingredient-level allergen verification using real Migros data, see Step 6.5 of the Run flow.
4. If `fixed_slots.<slot>` is a list, the sum of `servings` across items must equal the slot's effective servings (`slot_servings.<slot>` if defined, else `household_size`). Exactly one item should have `is_primary: true` (the recipe whose nutrition counts toward the user's macro targets); if none is marked, the first item is treated as primary.

If any validation fails, abort with a specific error pointing at the conflict. Do not produce partial output.

## Recipe library

At run start, scan `~/.claude/skills/mmmmealplan/recipes/<slot>/*.md` for each slot in `meal_cadence`. For each file, parse the YAML frontmatter to extract: `name`, `slot`, `servings`, `time_minutes`, `tags`, `ingredients`, `nutrition_per_serving` (optional).

Build an in-memory list of available library recipes per slot. This list is used in two places:

1. **Fixed slot resolution** — match `fixed_slots.<slot>` against filenames (without `.md`).
2. **LLM generation prompt** — pass the list of (filename, name, tags, time_minutes) per slot as candidate library recipes the LLM can select from.

If a recipe file is malformed (invalid YAML frontmatter, missing required fields), skip it and emit a warning in the output: `Skipped recipe <path>: <reason>`. Do not abort.

### Required frontmatter fields

`name`, `slot`, `servings`, `time_minutes`, `tags`, `ingredients`. `nutrition_per_serving` is optional.

If `nutrition_per_serving` is absent, the run flow will compute it from Migros product data during ingredient resolution (Step 6 of the Run flow).

## Migros MCP usage

Read `lib/migros-helpers.md` when you need to call any Migros MCP tool. It documents the patterns for ingredient resolution, caching, nutrition parsing, and failure handling.

## Run flow

When invoked, execute these steps in order. Do not skip steps. If any step fails irrecoverably, abort with a clear error.

### Step 1 — Determine planning window

- Default: next Mon–Sun (7 days).
- If invoked with `--days N`, plan N days starting today.
- Compute the ISO week label for output filenames: `YYYY-WXX` (e.g., `2026-W18`). For non-week-aligned windows use `YYYY-MM-DD` instead.

### Step 2 — Load config and recipe library

- Read `~/.claude/skills/mmmmealplan/config.yaml`. Apply the validation rules from the Configuration section. Abort on validation failure.
- Scan `~/.claude/skills/mmmmealplan/recipes/<slot>/*.md` per the Recipe library section. Build the in-memory candidate list.
- Read the last 2 plan files from `~/.claude/skills/mmmmealplan/plans/` (sorted by filename). Extract the recipe names used. Build a `recently_used` set per slot.

### Step 3 — Compute slot demand

`meal_cadence` is expressed per week (assumes a 7-day window). For shorter or longer windows, scale pro-rata.

For each slot in `meal_cadence`:
- `scaled_cadence = round(meal_cadence[slot] × window_days / 7)` — scale per-week cadence to the actual window
- `total_needed = scaled_cadence`
- `fixed_count = number of days in window with fixed_slots[slot] set` — usually all days if a fixed slot is set
- `free_count = max(0, total_needed - fixed_count)`
- `free_count` is what the LLM must fill
- `effective_servings = slot_servings[slot] if defined else household_size` — drives ingredient quantity scaling for that slot

Examples:
- Cadence `breakfast: 7`, fixed `breakfast: overnight-oats`, window 7 days → scaled_cadence = 7, fixed_count = 7, free_count = 0.
- Cadence `dinner: 4`, no fixed dinner, window 3 days → scaled_cadence = round(4 × 3/7) = 2, fixed_count = 0, free_count = 2.
- Cadence `lunch: 0`, any window → scaled_cadence = 0, free_count = 0 (slot is skipped).

### Step 4 — Query Migros promotions

Call `mcp__migros__get_promotions`. See `lib/migros-helpers.md` for parsing and failure handling. Result is a list of promoted products (name, discount). If failed/empty, set `promotions = []` and continue.

### Step 5 — Generate the candidate plan (LLM step)

Construct a prompt for the model with these inputs:

- Planning window (start date, end date, day count)
- Free slots per day (from step 3)
- Fixed slots per day (recipes already chosen)
- Config: macros targets, restrictions, dislikes, equipment, time constraints
- Library candidates per slot: list of `{filename, name, tags, time_minutes}`
- `recently_used` set per slot (avoid repeating)
- Promotions list

Ask the model to produce, in JSON:

```json
{
  "days": [
    {
      "date": "2026-04-28",
      "weekday": "Mon",
      "meals": {
        "breakfast": { "source": "library", "filename": "overnight-oats" },
        "dinner":    { "source": "new", "name": "Sheet-pan chicken & broccoli", "ingredients": ["chicken breast 200g", "broccoli 200g", "olive oil 15g", "lemon 1/2"], "time_minutes": 25, "tags": ["high-protein", "one-pan"] }
      }
    }
  ],
  "ingredient_overlap": [
    { "ingredient": "broccoli", "days": ["Mon", "Tue"] }
  ],
  "promotion_picks": [
    { "ingredient": "salmon", "day": "Thu", "discount": "-30%" }
  ]
}
```

Constraints the model must respect:
1. Hard restrictions are absolute. Reject any recipe that violates them.
2. Avoid `recently_used` recipes (soft — only override if no alternative).
3. Maximize ingredient overlap across the week.
4. Bias toward promoted ingredients when it does not compromise constraints.
5. Each day's projected macros (LLM's best estimate, refined later) should aim for the daily target.
6. `NEW` recipes must include canonical ingredient names (so they resolve at Migros) and quantities for one serving.

### Step 6 — Resolve ingredients via Migros MCP

Collect the union of all ingredients across the week (from library recipes and NEW recipes). Deduplicate by canonical name. For each unique ingredient, follow the resolution pattern in `lib/migros-helpers.md`:

1. Check the in-session ingredient cache.
2. If miss, call `search_products`, then `get_product_details`.
3. Cache the result.

Aggregate per-ingredient quantities across the week (e.g., 200g chicken Mon + 200g Tue + 200g Thu → 600g total). Round up to a buyable unit when needed (e.g., 600g → 1 packet of ~600g).

**Quantity scaling by servings:** Recipe `ingredients` are expressed per single serving. Multiply by the recipe's effective servings before aggregating:
- Single recipe (string `fixed_slots.<slot>` or LLM choice): multiply by `effective_servings` for that slot.
- Split recipe (list `fixed_slots.<slot>`): multiply each item's recipe ingredients by that item's `servings` count, then sum across items and across days.

For ingredients that fail resolution, mark them `[unavailable]` and continue.

### Step 6.5 — Ingredient-level allergen validation

After ingredient resolution, walk every resolved product's `allergens` field and check it against the user's `restrictions`. This catches cases where a recipe's tag claims it satisfies a restriction but the actual Migros product flags an allergen that violates it (example: a recipe tagged `lactose-free` but using skyr, which Migros allergens flag as containing milk).

Allergen mapping (Migros German allergen strings → restriction keyword):

| Restriction | Migros allergen string contains |
|---|---|
| `lactose-free` | "Milch und daraus gewonnene Erzeugnisse" |
| `gluten-free` | "Getreidekörner, die Gluten enthalten", "Weizen", "Gerste", "Hafer", "Roggen" |
| `nut-free` | "Nüsse", "Mandeln", "Haselnuss", "Cashewnuss", "Pistazie" |
| `peanut-free` | "Erdnüsse" |
| `soy-free` | "Sojabohne" |
| `egg-free` | "Eier" |
| `fish-free` | "Fische" |
| `shellfish-free` | "Krebstiere", "Weichtiere" |
| `sesame-free` | "Sesamsamen" |

For each violation found, append a flag in the plan output:

> ⚠ Allergen conflict: `<recipe-name>` contains `<allergen>` via `<ingredient>` — violates restriction `<restriction>`. Recipe tag may be inaccurate.

**Do NOT abort.** Surface the conflict and let the user decide whether to swap the ingredient, edit the recipe tag, or accept the conflict (e.g., they tolerate trace lactose). The tag-based check in Step 2 remains the authoritative source for hard validation; this is a soft secondary check using real Migros data.

### Step 7 — Verify nutrition per day

**Whose macros count?** Macro targets in `config.macros` apply to one person — the *primary eater*. For split slots (a list in `fixed_slots`), only the recipe item marked `is_primary: true` (or the first item if none marked) feeds into the daily macro tally. Other items in the list represent meals for other household members; their nutrition is tracked only for shopping-list ingredient quantities, not for macro totals.

For each day:
- Sum `protein_g`, `carbs_g`, `fat_g`, `kcal` across the primary eater's meals only.
- For library recipes with `nutrition_per_serving` in frontmatter, use those values directly.
- For library recipes without it, compute by summing each ingredient's per-100g nutrition × quantity (from Migros data).
- For NEW recipes, compute the same way.
- If any ingredient has missing nutrition data, exclude it from sums and note `*` in the day's totals.

Compare each day's totals to `config.macros`. Flag days outside ±10% of any target. The flag in the plan output is a one-line note like `⚠ Wed: protein 110g vs target 150g — consider adding a protein side`.

Do NOT auto-rebalance.

Compute weekly averages for the plan-output header.

### Step 8 — Render outputs

Generate two files using the templates in `lib/plan-template.md` and `lib/shopping-list-template.md`:

1. `~/.claude/skills/mmmmealplan/plans/<window>.md` — the meal plan
2. `~/.claude/skills/mmmmealplan/shopping-lists/<window>.md` — the shopping list

After writing, print both absolute paths to the user.

## NEW recipe save flow

After printing the plan and shopping-list paths, look at the plan for any meals marked `NEW`. If there are none, skip this step.

Otherwise, ask the user, one at a time:

> The plan includes a NEW recipe: **{RECIPE_NAME}** ({slot}, ~{TIME_MINUTES}min, tags: {TAGS}). Save it to your library? (y/n)

If the user says yes, write the recipe to `recipes/<slot>/<slug>.md` using the `lib/recipe-template.md` format, populated from the LLM's NEW-recipe data plus the resolved Migros nutrition (if available). The slug is the recipe name lowercased with spaces replaced by `-` and non-alphanumerics stripped.

If the user says no, do nothing — that recipe stays as a one-off in this week's plan only.

Repeat until all NEW recipes have been resolved. Then exit.

## Edge cases & failure handling

| Case | Behavior |
|---|---|
| `config.yaml` missing | Print copy-from-example instructions. Stop. |
| Config validation fails (missing field, fixed-slot violates restriction, fixed-slot recipe not found) | Print specific error pointing at the problem. Stop. |
| Recipe library empty (cold start) | Generate every meal as `NEW`. Proceed normally. After the run, the user can save the ones they liked — library grows. |
| Library recipe file has malformed frontmatter | Skip with a warning `Skipped recipe <path>: <reason>`. Continue. |
| Migros MCP server unreachable | Abort: "Migros MCP server unreachable. Cannot proceed." Do not write partial files. |
| `search_products` returns 0 for an ingredient | Retry with relaxed query. If still empty, mark `[unavailable]` in shopping list, continue. |
| `get_product_details` returns partial nutrition | Use what's there. Annotate macro totals with `*` (1 ingredient missing data). |
| `get_promotions` fails or is empty | Proceed without bias. Note in plan output: "Promotions data unavailable this run." |
| Day's macros miss target by >10% | Flag inline in plan with a swap suggestion. Do NOT auto-rebalance. |
| Same recipe appears in both of the last 2 plans | LLM avoids it (soft constraint from `recently_used`). Only override if no alternative. |
| User says no to all NEW recipe saves | Plan still works for this week — recipes just don't enter the library. |
