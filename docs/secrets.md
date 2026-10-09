# Secrets - one source of truth in Vaultwarden

Credential files (`~/.config/*/…env`, tokens, `~/.claude/secrets.fish`) used to live only on
the machine they were made on. A tool built on the Arch PC broke on the laptop or the server
until the file was copied by hand.

Now **Vaultwarden (vault.elyesghazel.ch) holds every one of them**, and `secrets` writes
the plain files on each machine. Scripts, timers and agents keep reading their files exactly
as before (chmod 600), so nothing needs an unlocked vault at runtime and nothing breaks when
the server reboots.

```
Vaultwarden                         machine
Secrets/                            ~/.config/slideplate/send.env
  slideplate/slideplate-send  ──pull──▶  (chmod 600, read by the script)
  slideplate/webstamp         ◀──push──  after you edit the file locally
  shared/ntfy                 ◀── ref:ntfy/<KEY> from the items above
  ...
```

## Files

| Path | What |
|---|---|
| `secrets/.local/bin/secrets` | the CLI (Python 3, wraps `bw`) |
| `secrets/.config/secrets/manifest.tsv` | which file belongs to which item, on which hosts |
| `fish/.config/fish/functions/secrets-unlock.fish` | sets `BW_SESSION` in the current shell |

Both are stowed (`stow secrets`, already in `install.sh`).

## How an item is stored

One **Secure Note** per file in the folder `Secrets/<group>`:

- every value is a **hidden custom field** (`SMTP_PASSWORD`, `NTFY_TOKEN`, …)
- the note body is the file with values replaced by `{{KEY}}`, so comments, order and quoting
  come back exactly as they were
- `raw` files (single tokens) are one field called `content`

You can view or edit any value in the Vaultwarden web UI. Change it there, then `secrets pull`
on each machine that uses it.

### Shared values (ntfy tokens)

Values that several files share live once in `Secrets/shared`, e.g. the item `ntfy` with one
field per topic token. A file item points at it with `ref:ntfy/<KEY>`. `secrets push`
swaps in the reference by itself whenever a value equals a shared field (8+ chars), so
rotating a token means changing **one** field and pulling.

```fish
secrets set ntfy SLIDEPLATE_TOKEN     # prompts, hidden - create/rotate a shared value
```

## Daily use

```fish
secrets-unlock               # once per shell (master password)
secrets status               # what this host should have + in sync / differs / missing
secrets pull                 # write every file this host needs
secrets pull webstamp        # just one
secrets push slideplate-send # after editing the local file
bw lock                      # when done
```

`pull` never overwrites a local file that is newer than the vault copy - it tells you to push
first (or `--force`). `--dry-run` works for pull and push.

**Speed.** Every `bw` call costs ~1.5 s (Node start + decrypt), so `secrets` reads the whole
vault once - folders and items in parallel - and does the rest locally: `status` / `pull` are
~1.5 s regardless of how many items. `bw sync` (re-download from the server, another ~1.5 s)
only runs when the last one is older than 5 min (`~/.cache/secrets/last-sync`). Changed a value
in the web UI a minute ago? Add `--sync`. A push adds one `bw` write per item (plus one per new
folder the first time).

## New machine

Step-by-step runbook (written so a Claude session on the new device can follow it): [secrets-new-device.md](secrets-new-device.md). Short version:

1. Install the Bitwarden CLI as the **standalone binary, pinned to 2026.7.0** (same as the server):
   ```fish
   curl -L -o /tmp/bw.zip https://github.com/bitwarden/clients/releases/download/cli-v2026.7.0/bw-linux-2026.7.0.zip
   unzip -o /tmp/bw.zip bw -d ~/.local/bin; and rm /tmp/bw.zip
   ```
   Not `pacman -S bitwarden-cli`: it pulls `nodejs-lts` and wants to remove Node 26. Not the latest
   release either: 2026.9.x calls a key-id endpoint Vaultwarden 1.37.1 lacks (`KeyIdBackfillError`, 404).
   Upgrade `bw` only after Vaultwarden is updated. Windows: `bw-windows-2026.7.0.zip` from the same
   release page, or inside WSL as above.
2. `bw config server https://vault.elyesghazel.ch && bw login`
3. Clone dotfiles, `stow secrets fish` (or `./install.sh`)
4. `secrets-unlock && secrets pull`

The hostname picks the files: `elyes-arch` (Arch PC), `elyes-ghazel-server` (VPS). A new
machine gets every `*` item; add its hostname to the `hosts` column for the rest. `!host`
excludes one machine from a `*` line - used where the server needs its own variant of a file
(`claude-mcp` vs `claude-mcp-server`, both `~/.claude/secrets.fish`). Override with
`SECRETS_HOST=<name>` if a hostname is odd (WSL).

## New tool that needs a credential

1. Write the file where the tool expects it (`~/.config/<tool>/config.env`, chmod 600)
2. Add a line to `manifest.tsv` (item, group, format, hosts, path), commit dotfiles
3. `secrets push <item>`

## Deliberately not synced

| What | Why |
|---|---|
| `/opt/docker/*/.env` | root-owned stack secrets, server-only, in the `/opt/docker` restic backup |
| `~/.config/hevy-mcp/token.json` | OAuth token the MCP refreshes itself - a copy goes stale |
| `~/.config/Bitwarden CLI/` | the vault login itself |

## Security notes

- An unlocked shell (`BW_SESSION` set) can read **every** item - including from an agent
  running in that shell. Unlock only when syncing, `bw lock` after.
- Values never appear in output and reach `bw` on stdin, not in `argv` (so not in `ps`).
- Files are written atomically with mode 600, parent dirs 700.
