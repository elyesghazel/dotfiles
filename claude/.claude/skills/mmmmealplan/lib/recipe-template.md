# Recipe template

Every recipe file in `recipes/<slot>/` follows this shape:

```yaml
---
name: <Display name>
slot: breakfast | lunch | dinner
servings: <int>
time_minutes: <int>            # total prep+cook time
tags: [<tag>, ...]              # e.g. high-protein, lactose-free, no-cook, vegetarian, contains-pork
ingredients:                    # canonical names; quantities for one serving
  - <ingredient>: <amount with unit>
nutrition_per_serving:          # OPTIONAL — if absent, computed at runtime from Migros data
  protein_g: <int>
  carbs_g: <int>
  fat_g: <int>
  kcal: <int>                   # optional within nutrition block
---

## Steps
1. <Step one>
2. <Step two>
```

### Tag conventions

Use these standard tags so config restrictions match recipe constraints:

- Dietary: `vegetarian`, `vegan`, `pescatarian`
- Allergens/restrictions: `lactose-free`, `gluten-free`, `nut-free`, `contains-lactose`, `contains-gluten`, `contains-pork`, `contains-shellfish`
- Style: `high-protein`, `low-carb`, `no-cook`, `one-pan`, `meal-prep`
- Cuisine: `italian`, `asian`, `mexican`, etc. (free-form)
