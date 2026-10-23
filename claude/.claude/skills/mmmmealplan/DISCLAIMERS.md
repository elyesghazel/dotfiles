# Disclaimers

Read this before using Mmmmealplan in earnest.

## Not affiliated with Migros

Mmmmealplan is an independent open-source project. It depends on the
[Migros MCP](https://github.com/lewpgs/migros-mcp), which itself uses
**unofficial endpoints** that power the Migros website and mobile app.

Neither this project nor the upstream MCP are affiliated with, endorsed by,
sponsored by, or connected to **Migros-Genossenschafts-Bund** or any of its
subsidiaries in any way. The Migros name and trademarks remain the property
of their respective owners. The unofficial endpoints can break, rate-limit,
or be withdrawn at any time without warning, in which case the skill will
abort cleanly and write nothing.

## Nutrition is informational, not medical advice

The macro figures, allergen flags, and shopping-list calorie totals are
**approximations** based on the data Migros publishes for each product.
They are intended for casual planning, not for clinical, sport-performance,
or medical use.

- If you have a diagnosed dietary condition (coeliac disease, severe
  allergies, diabetes, kidney disease, eating disorder history, etc.),
  consult a qualified registered dietitian or physician — do not use this
  skill as a substitute.
- If you have a life-threatening allergy, **always read the actual product
  label** before consuming. The allergen mapping in this skill is a
  convenience check, not a replacement for label-reading. Manufacturers can
  change formulations without warning.
- "Per 100 g" values from Migros are themselves approximate and may differ
  between batches.

## AI-generated recipes can hallucinate

The skill asks an LLM to invent recipes when the library is thin. The model
can produce dishes that look plausible but contain technique gaps, unsafe
combinations, or quantities that don't actually feed one person. Read every
NEW recipe before cooking. The user retains full responsibility for what
ends up on the plate.

## Pricing accuracy

Prices and promotions reflect what the Migros API returns at the moment the
skill runs. They may differ from what the store charges:

- Promotions can end between plan generation and shopping.
- Regional pricing variation is not modelled.
- Pack sizes and unit prices are taken at face value; weighing fresh produce
  in store may yield different totals.

The shopping-list total is a best-effort estimate, not a guaranteed bill.

## Not a checkout

Mmmmealplan **does not place orders**. It generates a list. You go shopping
(physically or via the Migros web shop). Nothing in this skill mutates your
Migros account or any other external state.

## Use at your own risk

The software is provided "as is", without warranty of any kind, as set out
in the [MIT License](LICENSE). The authors and contributors are not liable
for any consequence of using the skill — including but not limited to
allergic reactions, incorrect nutrition, missed deals, wasted ingredients,
unsuccessful dinners, or arguments at the dinner table.

If you find a bug, please open an issue. If you find an allergen-mapping
gap, please open an issue *quickly*.
