# Plan output template

Use this structure when writing `plans/<window>.md`.

```markdown
# Week {WEEK_LABEL} Meal Plan ({START_DATE} – {END_DATE})

## Daily macros (avg)
- Protein: {AVG_PROTEIN}g (target {TARGET_PROTEIN}g) {CHECK_OR_FLAG}
- Carbs: {AVG_CARBS}g (target {TARGET_CARBS}g) {CHECK_OR_FLAG}
- Fat: {AVG_FAT}g (target {TARGET_FAT}g) {CHECK_OR_FLAG}
- Kcal: {AVG_KCAL} (target {TARGET_KCAL}) {CHECK_OR_FLAG}

## Daily breakdown

### {WEEKDAY} ({DATE}) — {DAY_PROTEIN}g protein, {DAY_KCAL} kcal {DAY_FLAG}
- **Breakfast**: {RECIPE_NAME} *({SOURCE})*
- **Dinner**: {RECIPE_NAME} *({SOURCE})*

(repeat per day)

## Ingredient overlap
- {INGREDIENT}: {DAYS} ({QUANTITY_NOTE})

## Promotion-driven picks
- {INGREDIENT} ({DISCOUNT}) → {DAY} {SLOT}

## NEW recipes proposed this run
- {SLOT}/{RECIPE_NAME}  (save? y/n)

(omit section if no NEW recipes)
```

`{CHECK_OR_FLAG}` is `✓` if within ±10% of target, `⚠ off by Xg` otherwise.
`{DAY_FLAG}` is empty if the day is on target, or `⚠ low protein — consider swap` style if off.
`{SOURCE}` is `library` or `NEW — save?`.
