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

# excalidraw-boards

- **excalidraw-boards** (`~/.claude/skills/excalidraw-boards/SKILL.md`) - draw on the self-hosted Excalidraw at `draw.elyesghazel.ch`. Trigger: `/excalidraw-boards`

Whenever I ask for a **diagram, visual, drawing, sketch, chart, flow/flowchart, graph,
board/whiteboard, mind map**, say "visualise this", "draw this", "map it out", "explain
visually", or ask how a system works in a way that's clearer as a picture — invoke the Skill
tool with `skill: "excalidraw-boards"` before answering. Same when I paste a
`draw.elyesghazel.ch` board link.

This is the default for anything visual, and it wins over `drawio-skill`. Only reach for
`drawio-skill` when I explicitly say draw.io, or I need an exported PNG/SVG/PDF file.

# sumry

- **sumry** (`~/.claude/skills/sumry/SKILL.md`) - my self-hosted finances at
  `sumry.elyesghazel.ch`, via the `sumry` MCP server. Trigger: `/sumry`

Whenever I mention **money, a balance, an account** (PostFinance, Revolut, Sparkonto,
Portemonnaie / Cash), **what I spent or earned, whether I can afford something, budgets**, or
ask you to **log, book, record or correct a transaction** — invoke the Skill tool with
`skill: "sumry"` before answering. Bare statements count: "spent 12.50 on lunch", "got paid",
"PostFinance is at 334.50", "add 460 to cash".

Read with `sumry_accounts` / `sumry_summary` rather than guessing from memory — balances move.

# apple-reminders

- **apple-reminders** (`~/.claude/skills/apple-reminders/SKILL.md`) - my iCloud Reminders
  via pyicloud and the `remind` / `icloud` fish functions. Trigger: `/apple-reminders`

Whenever I say **"remind me"**, ask to **add, list, complete or delete a reminder / to-do /
task**, or ask **what's on my reminders** or **what I have to do** — invoke the Skill tool with
`skill: "apple-reminders"` before answering. Bare statements count: "todo go shopping",
"I need to call the landlord", "don't let me forget the parcel".

**Todos go to Reminders, events go to Google Calendar.** Both land on my iPhone.
- **Reminders**: something I have to *do*, with or without a deadline. "Go shopping",
  "pay the bill by Friday", "call mum at 18:00" → `remind` (with `@ <when>` if a time is
  given).
- **Google Calendar** (the `Google_Calendar` connector): something that *happens* at a time,
  usually with a duration, a place or other people. "Dentist Tuesday 14:00", "dinner with
  Lea Saturday 19:30", "exam 12 Oct 9–11" → `create_event`.
- Unsure, e.g. "gym tomorrow 7am"? Default to a calendar event if it blocks time and to a
  reminder if it's a nudge. Don't ask unless both readings would be wrong in a way that
  matters.
