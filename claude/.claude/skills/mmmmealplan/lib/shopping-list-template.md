# Shopping list output template

Use this structure when writing `shopping-lists/<window>.md`.

```markdown
# Shopping List — Week {WEEK_LABEL}

**Total: CHF {TOTAL}** | **Daily protein avg: {AVG_PROTEIN}g** | **Daily kcal: {AVG_KCAL}**

## Produce
- [ ] {PRODUCT_NAME}, {QUANTITY} — CHF {PRICE}{PROMO_NOTE}

## Meat & Fish
- [ ] ...

## Dairy
- [ ] ...

## Pantry
- [ ] ...

## Frozen
- [ ] ...

## Other
- [ ] ...

## Unavailable / not found
- {INGREDIENT} ({REASON}) — substitute manually
```

### Category mapping

Map Migros category strings to these display categories:

| Display category | Migros category keywords |
|---|---|
| Produce | Früchte, Gemüse, Obst, Salate |
| Meat & Fish | Fleisch, Geflügel, Fisch, Meeresfrüchte |
| Dairy | Milch, Käse, Joghurt, Eier |
| Pantry | Teigwaren, Reis, Mehl, Konserven, Öl, Gewürze |
| Frozen | Tiefkühl, TK |
| Other | (anything else) |

Order categories in the output as listed above (the typical store-walk order).

`{PROMO_NOTE}` is empty or ` (PROMO {DISCOUNT})`.

Omit `## Unavailable` section if there are no unavailable ingredients.
