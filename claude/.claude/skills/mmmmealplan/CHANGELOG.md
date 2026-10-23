# Changelog

All notable changes to Mmmmealplan are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
uses [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-05-01

Initial public release.

### Added
- Slash command `/mmmmealplan` (and `--days N` variant for non-week windows).
- YAML config schema with single-eater and split-slot two-eater examples
  (`config.yaml.example`).
- Library-driven recipe system: any `*.md` file in `recipes/<slot>/` with
  valid frontmatter is picked up at run time.
- Migros MCP integration:
  - `get_promotions` for promo bias.
  - `search_products` + `get_product_details` for ingredient resolution and
    nutrition lookup.
  - In-session ingredient cache to avoid duplicate calls.
- Per-day macro verification for the primary eater with ±10% flagging
  (no auto-rebalance).
- Ingredient-level allergen validation: real Migros allergen strings checked
  against config restrictions, with a German→keyword mapping for
  `lactose-free`, `gluten-free`, `nut-free`, `peanut-free`, `soy-free`,
  `egg-free`, `fish-free`, `shellfish-free`, `sesame-free`.
- Categorised shopping-list output (Produce / Meat & Fish / Dairy / Pantry /
  Frozen / Other) with promo annotations.
- "NEW recipe save" prompt: invented recipes can be saved into the library
  one at a time.
- Starter recipe library: 3 breakfasts (cooked-oats, overnight-oats,
  skyr-with-muesli) and 4 vegetarian dinners (halloumi traybake, veggie
  schnitzel, red lentil dahl, tofu stir-fry).
- `install.sh` for one-shot symlink-based install.

### Known limitations
- Migros-only product catalogue and pricing.
- German ingredient names match best.
- The skill does not place orders.
- Promotions reflect the API at run time, not at shopping time.
- Cold-start runs (empty library) generate every meal as NEW; the library
  grows from there.
