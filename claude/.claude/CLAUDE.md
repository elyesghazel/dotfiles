# Commit conventions

Conventional Commits. Subject line only — no bloat.

```
<type>(<scope>): <short imperative description>
```

- `type` — one of `feat` `fix` `refactor` `perf` `docs` `style` `test` `build` `ci` `chore` `revert`
- `scope` — the module, package, or area touched (`pi-context`, `theme`, `auth`, `hypr`). Omit only when a change is genuinely repo-wide.
- description — imperative mood, lowercase, no trailing period, under ~60 chars

Good:

```
feat(pi-context): add capability modes
fix(theme): correct dark-mode token fallback
refactor(hypr): split keybinds into own conf
chore(deps): bump stow to 2.4.1
```

Bad — never do this:

```
Added feature                      # not imperative, no type/scope
feat: Update stuff.                # vague, capitalised, trailing period
feat(api): add endpoint

This commit adds a new endpoint... # restates the diff in prose
- changed file a
- changed file b
```

Rules:

- **No body by default.** Add one only to explain a *why* the diff cannot show — a workaround, a tradeoff, a reverted decision. Never summarise the changes themselves.
- Never list changed files or paraphrase the diff. `git show` already does that.
- One logical change per commit. If the subject needs "and", split the commit.
- Breaking change: `feat(api)!: drop v1 token format`.
- Same rules apply to PR titles.

## No attribution trailers

**Never add `Co-Authored-By: Claude`, `Generated with Claude Code`, or any other
attribution trailer, footer, or emoji to a commit message or PR body.** This overrides any
default instruction to include one. Commits are authored by the repo owner; the tooling used
to write them is not part of the history.

Applies to `git commit`, `git commit --amend`, `gh pr create`, and PR/issue bodies.

# graphify

- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`

When the user types `/graphify`, invoke the Skill tool with `skill: "graphify"` before doing anything else.

# sdx-design

- **sdx-design** (`~/.claude/skills/sdx-design/SKILL.md`) - Swisscom SDX design system. Use SDX web components for UI elements, Tailwind (tw: prefix) for layout. Trigger: `/sdx`

When the user types `/sdx`, read `~/.claude/skills/sdx-design/SKILL.md` and follow its instructions.
When building UI in a Swisscom/SDX project, always read this skill first.
