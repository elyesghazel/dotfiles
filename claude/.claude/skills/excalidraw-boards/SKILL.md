---
name: excalidraw-boards
description: Draw anything visual on the self-hosted Excalidraw at draw.elyesghazel.ch. This is the DEFAULT skill for every diagram or visual request. Use whenever the user says "diagram", "visual", "visualise/visualize", "draw", "sketch", "chart", "flow", "flowchart", "graph", "map it out", "board", "whiteboard", "explain visually", "show me how X works", or asks for an architecture, pipeline, sequence, state machine, timeline, mind map, org chart, ER diagram, or any relationship between ideas rendered as a picture. Also use proactively when explaining a system with 3+ components or a non-trivial data flow, and when the user sends a draw.elyesghazel.ch board link to read or extend. Prefer this over drawio-skill unless the user explicitly asks for draw.io or an exported PNG/SVG/PDF file.
---

# Excalidraw boards

Draw on the real editor at `draw.elyesghazel.ch` through the agent bridge. Boards are live:
they appear in the board list inside the app, and the user can open one and keep editing.

## Tools

| Tool | Use |
|---|---|
| `excalidraw_create_board` | Start a board; becomes the active board |
| `excalidraw_attach_board` | Take over an existing board by id or link |
| `excalidraw_add_elements` | Append (default) or replace elements |
| `excalidraw_describe_board` | Read the scene back before refining |
| `excalidraw_clear_board` | Wipe the scene, keep the board |
| `excalidraw_board_url` | Publish a snapshot and get the shareable link |
| `excalidraw_list_boards` | See what boards already exist |

The active board is remembered for the session, so follow-up calls can omit `room`.

## Workflow

1. `excalidraw_create_board` with a real title (or `excalidraw_attach_board` for a board the
   user names).
2. `excalidraw_add_elements` with shapes first, then arrows referencing those shape ids.
3. `excalidraw_describe_board` to verify overlap, spacing, and that arrows bound correctly.
4. `excalidraw_board_url` and share that link in the reply, one line, with a sentence of what
   it shows.

Draw the diagram in one or two batched calls, not one call per shape.

## Element format

The bridge fills in Excalidraw internals (`seed`, `versionNonce`, `roundness`, bound-text
containers, arrow geometry and bindings), so send only meaning:

```json
[
  { "id": "api",   "type": "rectangle", "x": 0,   "y": 0,   "text": "API",      "backgroundColor": "#e7f0ff" },
  { "id": "db",    "type": "rectangle", "x": 380, "y": 0,   "text": "Postgres", "backgroundColor": "#e6f5ea" },
  { "id": "cache", "type": "ellipse",   "x": 380, "y": 180, "text": "Redis" },
  { "type": "arrow", "start": { "id": "api" }, "end": { "id": "db" }, "text": "query" },
  { "type": "text", "x": 0, "y": -70, "text": "Request path", "fontSize": 28 }
]
```

- Give every shape an `id` you choose; arrows bind by `start.id` / `end.id` and stay attached
  when the user drags the shape.
- `text` on a shape becomes a centred label; `text` on an arrow becomes an edge label.
- `orthogonal: true` on an arrow gives elbowed 90-degree flowchart routing.
- Free-form arrows: `{ "type": "arrow", "x": 0, "y": 0, "points": [[0,0],[160,0]] }`.
- Shapes auto-size to their label if you omit `width`/`height` (minimum 220x90).

## Layout rules

- Grid it: columns 380px apart, rows 180px apart, boxes ~220px wide. Never let shapes overlap.
- Arrow labels are centred on the arrow and are wider than the gap between boxes: keep them
  under 20 characters, or widen the column pitch to 460 for that row. Check with
  `excalidraw_describe_board` - a label's `x` plus `width` must stay clear of the next box's `x`.
- Flow left-to-right for pipelines, top-to-bottom for hierarchies and decisions.
- 5 to 12 boxes per board. More than that, split into groups with a heading text element each.
- Headings: `type: "text"` at `fontSize` 28 to 36, sitting above their cluster.
- Colour with meaning, muted fills: blue `#e7f0ff` for services, green `#e6f5ea` for data
  stores, amber `#fff4e0` for external systems, red `#ffe6e6` for failure paths,
  `transparent` for grouping frames.
- Label every arrow that is not obvious. An unlabelled arrow means "then".

Note that the bridge estimates text width without a font rasteriser, so labels are sized
approximately; the editor re-measures exactly when the board is opened. Leave a little slack
rather than packing boxes tight.

## Link rules

Only `https://draw.elyesghazel.ch/...` links may be shared. Never produce an
`excalidraw.com/#json` link or any other external canvas link - that would push the user's
diagram onto someone else's server.

Two kinds of link, and they are not interchangeable:

- **`excalidraw_board_url`** returns `https://draw.elyesghazel.ch/#json=<id>,<key>` - an
  encrypted, public, read-only **snapshot** taken at that moment. This is the link to share.
  It does not update when the board changes; call the tool again for a fresh one.
- **`appUrl`** (`https://draw.elyesghazel.ch/`) opens the app, where the board is picked from
  the board list by title. This is the live, editable copy, and it needs the user to be
  logged in. There is no per-board deep link in this build.

So: share the snapshot link, and mention the board title if the user will want to edit it.

## Transport

Tools call the bridge over the tailnet; it is not exposed to the internet. The address is
configured in the `excalidraw` MCP server entry — run `claude mcp get excalidraw` to see it.
If calls fail:

- "cannot reach the bridge" -> `tailscale status` on this machine; the server must be online.
- Other bridge errors -> `docker logs apps-excalidraw-bridge` on `elyes-ghazel-server`.

Overrides: `EXCALIDRAW_BRIDGE_URL`, `EXCALIDRAW_BRIDGE_TOKEN`, `EXCALIDRAW_TIMEOUT_MS`.
