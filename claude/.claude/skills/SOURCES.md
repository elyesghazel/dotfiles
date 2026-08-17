# Skill sources

Provenance for the skills in this directory. Three were installed from public repos by a
skill installer that tracked them in `~/.agents/.skill-lock.json`; that directory has been
removed in favour of this repo, so the upstream references are recorded here instead. To
update a vendored skill, re-fetch the path below and diff it in.

## Vendored from upstream

| Skill | Upstream | Path in upstream | Vendored |
|---|---|---|---|
| `content-strategy` | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | `skills/content-strategy/` | 2026-06-11 |
| `mega-goal-prompt` | [agentara/skills](https://github.com/agentara/skills) | `skills/productivity/mega-goal-prompt/` | 2026-06-11 |
| `find-skills` | [vercel-labs/skills](https://github.com/vercel-labs/skills) | `skills/find-skills/` | 2026-06-11 |

Upstream folder hashes at vendor time:

```
content-strategy  8a2387b41d046b1b5a72a346103120b3c28e8bf5
mega-goal-prompt  88cbe8433a97a1c3e0e8225ed9dc0532bc3926e5
find-skills       3013fdeb8a11b10b1eb795ec3ae8bfca38f7c26d
```

## Shared

`sdx-design` — authored here, documenting the public
[SDX design system](https://sdx.swisscom.com). A copy was shared with a colleague and lives
at [isaaclins/.config](https://github.com/isaaclins/.config/tree/main/agents/skills/sdx-design)
(`agents/skills/sdx-design/`). As of 2026-08-17 the two are identical apart from the
frontmatter `description`; this repo's version lists the concrete components, which gives the
model more to match on. **This repo is authoritative** — if the copies drift, reconcile here
first.

## Local

`drawio-skill`, `ui-ux-pro-max`, `graphify`, `markitdown`, `excalidraw-boards` — maintained
in this repo. `excalidraw-boards` and `markitdown` depend on the MCP servers registered by
`../bin/mcp-bootstrap.fish`.
