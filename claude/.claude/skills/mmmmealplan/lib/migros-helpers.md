# Migros MCP — Usage patterns for meal-planner

The Migros MCP server exposes these tools. SKILL.md references this file when planning a run.

## Available tools

| Tool | Purpose | Required args |
|---|---|---|
| `mcp__migros__search_products` | Search products by keyword. Returns product IDs (UIDs). | `query` (str) |
| `mcp__migros__get_product_details` | Full product info: price, nutrition, ingredients, allergens. | `productIds` (list of str UIDs) |
| `mcp__migros__get_promotions` | Current promotions. | (none typically) |
| `mcp__migros__get_categories` | Product categories. | (none) |
| `mcp__migros__get_stock` | Stock check. | productId |
| `mcp__migros__search_stores` | Find stores. | query |

In the meal-planner flow we primarily use **search_products**, **get_product_details**, and **get_promotions**.

## Pattern: Resolve an ingredient name to a Migros product

```
1. Call mcp__migros__search_products(query=<canonical ingredient name>, language="de")
2. If numberOfProducts == 0:
     a. Retry with relaxed query (e.g., drop adjectives: "Bio Hafer" → "Hafer")
     b. If still empty, mark the ingredient [unavailable] in the shopping list and continue
3. Otherwise, take the first 3-5 productIds and call mcp__migros__get_product_details
4. Pick the result that best matches by:
     - Name closeness to the canonical ingredient
     - Price per 100g (prefer mid-range, avoid premium/luxury variants unless specified)
     - In-stock status if available
5. Return: { name, productId, price, unitPrice, quantity, nutrition_per_100g, gtins }
```

## Pattern: Per-run ingredient cache

To avoid duplicate MCP calls when the same ingredient appears in multiple recipes:

- Maintain an in-session dict `ingredient_cache: { canonical_name: resolved_product }`
- Before calling `search_products`, check the cache
- The cache lives only for the duration of one `/meal-planner` invocation

## Pattern: Parse nutrition from `get_product_details` response

The `nutrition` field is a markdown table string. Per 100g values appear in the second column. Extract:

- `Eiweiss` (or `Eiweiß`) → `protein_g`
- `Kohlenhydrate` → `carbs_g`
- `Fett` → `fat_g`
- `Energie` → `kcal` (parse from the `kcal` value in the same cell, e.g. `1765 kJ (420 kcal)`)

If any of these are missing in the response, mark that product's nutrition as partial. Skip missing values from per-day macro sums and append `*` annotations to the totals header.

## Pattern: Promotions query

```
result = mcp__migros__get_promotions()
```

The result is a list of promoted products. Extract product names + discount info. Pass these as a "promotions list" to the LLM in the generation prompt.

If the call fails or returns empty, proceed without promotion bias and add to the plan output:
> Promotions data unavailable this run.

## Failure modes

| Failure | Handling |
|---|---|
| MCP server unavailable | Abort the entire run with: "Migros MCP server unreachable. Cannot proceed." |
| `search_products` returns 0 results for an ingredient | Retry relaxed; if still empty, mark `[unavailable]` |
| `get_product_details` partial response (missing nutrition) | Use what's there; annotate macro totals with `*` |
| `get_promotions` fails | Proceed without bias, note in output |
