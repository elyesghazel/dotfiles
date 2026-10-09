# Runbook: set up secrets sync on a new device

**Audience: a Claude Code session on the new device** (or Elyes doing it by hand).
Goal: this machine gets every credential file it needs from Vaultwarden via the `secrets`
CLI, so tools like `/webstamp`, `/slideplate-send` and the Claude MCP servers work.
Background on how the system works: [secrets.md](secrets.md).

## Rules for the agent - read first

1. **Never read, print, echo, cat, grep or log a secret value.** Not from env files, not from
   `bw`, not "just the first characters". Check files by *existence, size and permissions* only
   (`ls -l`, `stat -c '%a %s %n'`).
2. **Never type or ask for the master password, 2FA code or `BW_SESSION`.** Steps marked
   **[USER]** are run by Elyes in his own terminal. Tell him the exact command, wait for him to
   say it is done, then verify.
3. Do not install `bitwarden-cli` from pacman / apt / brew, and do not take the latest `bw`
   release. Use the **pinned standalone binary 2026.7.0** (see step 2 for why).
4. Do not edit the manifest's existing lines or other machines' files. Only add lines for this
   host when step 6 says so, and then commit just `secrets/.config/secrets/manifest.tsv`.
5. If something fails, stop and report the exact error. Do not work around it with
   copies of credential files from elsewhere.

## Facts

| | |
|---|---|
| Vaultwarden | `https://vault.elyesghazel.ch` (Vaultwarden 1.37.1) |
| Account | `elyes@elyesghazel.ch` |
| Dotfiles | `git@github.com:elyesghazel/dotfiles.git` -> `~/dotfiles` |
| CLI | `~/dotfiles/secrets/.local/bin/secrets` (Python 3, stowed to `~/.local/bin/secrets`) |
| Manifest | `~/dotfiles/secrets/.config/secrets/manifest.tsv` (stowed to `~/.config/secrets/`) |
| Vault layout | `Secrets/<group>/<item>` Secure Notes; shared ntfy tokens in `Secrets/shared/ntfy` |
| Known hosts | `elyes-arch` (Arch PC), `elyes-ghazel-server` (VPS) |

## Step 1 - identify the machine

```sh
cat /etc/hostname 2>/dev/null || hostname     # Windows PowerShell: $env:COMPUTERNAME
uname -a 2>/dev/null; python3 --version; git --version
```

Report the hostname, OS (Arch / other Linux / WSL / native Windows) and that Python 3 + git exist.
Python 3.8+ is required. Pick the matching path below; WSL counts as Linux.

## Step 2 - install `bw` 2026.7.0 (standalone)

Why pinned: `pacman -S bitwarden-cli` pulls `nodejs-lts` and wants to remove the system Node;
`bw` 2026.9.x fails against Vaultwarden 1.37.1 with `KeyIdBackfillError` (404).

**Linux / WSL**
```sh
mkdir -p ~/.local/bin
curl -L -o /tmp/bw.zip https://github.com/bitwarden/clients/releases/download/cli-v2026.7.0/bw-linux-2026.7.0.zip
unzip -o /tmp/bw.zip bw -d ~/.local/bin && chmod +x ~/.local/bin/bw && rm /tmp/bw.zip
bw --version        # must print 2026.7.0
```
Make sure `~/.local/bin` is on `PATH` (fish: `fish_add_path ~/.local/bin`).

**Native Windows (PowerShell)**
```powershell
$d = "$env:USERPROFILE\.local\bin"; New-Item -ItemType Directory -Force $d | Out-Null
Invoke-WebRequest https://github.com/bitwarden/clients/releases/download/cli-v2026.7.0/bw-windows-2026.7.0.zip -OutFile $env:TEMP\bw.zip
Expand-Archive -Force $env:TEMP\bw.zip $d; Remove-Item $env:TEMP\bw.zip
& "$d\bw.exe" --version     # 2026.7.0 - add $d to the user PATH if needed
```

If `bw --version` already shows 2026.7.0, skip this step.

## Step 3 - dotfiles

If `~/dotfiles` exists: `git -C ~/dotfiles pull --ff-only`. Otherwise clone it there.
Confirm `~/dotfiles/secrets/.local/bin/secrets` and `docs/secrets.md` exist - if not, the
secrets commit has not been pushed yet: stop and tell Elyes.

**Arch / Linux with stow** - link only these two packages (do not run the full `install.sh`
unless Elyes asks; it installs a whole desktop):
```sh
cd ~/dotfiles && stow secrets fish
ls -l ~/.local/bin/secrets ~/.config/secrets/manifest.tsv
```
If stow reports a conflict for an existing fish file, stop and report it - do not `--adopt`
or delete anything. Fallback without fish: `stow secrets` only.

**No stow / native Windows** - no linking needed, call it directly:
```sh
python3 ~/dotfiles/secrets/.local/bin/secrets --help
```
and set `SECRETS_MANIFEST=~/dotfiles/secrets/.config/secrets/manifest.tsv`
(PowerShell: `$env:SECRETS_MANIFEST = "$HOME\dotfiles\secrets\.config\secrets\manifest.tsv"`).
Native Windows is untested: file permissions (`chmod 600`) do not apply there; mention it.

## Step 4 - [USER] log in to Vaultwarden

First check: `bw status` - if it already shows `"serverUrl":"https://vault.elyesghazel.ch"` and
`"status":"locked"` or `"unlocked"`, skip to step 5.

Otherwise ask Elyes to run in **his own terminal** (it prompts for password + 2FA):
```sh
bw config server https://vault.elyesghazel.ch
bw login
```
Verify afterwards with `bw status` -> `"status":"locked"` (logged in, not unlocked) and the
correct `serverUrl`. Report only those two fields.

## Step 5 - see what this host gets

```sh
secrets list
```
Lines whose hosts column is `*` or this machine's hostname are pulled here. Report which
items that is. If the hostname is new, only the `*` items apply - that is expected.

## Step 6 - [USER] unlock + pull

The unlock token lives only in Elyes's shell, so he runs this himself:

fish:
```fish
secrets-unlock
secrets status
secrets pull
bw lock
```
bash / zsh:
```sh
export BW_SESSION="$(bw unlock --raw)"
secrets status && secrets pull
bw lock
```
PowerShell:
```powershell
$env:BW_SESSION = bw unlock --raw
python3 ~/dotfiles/secrets/.local/bin/secrets pull
bw lock
```

Expected `pull` output: `wrote <item> -> <path>` per item (or `ok ... in sync`). Ask him to paste
the output - it never contains values. `keep ... local file is newer` means a file already
existed here and was changed after the vault copy: ask him whether to `secrets push <item>`
(this machine wins) or `secrets pull --force <item>` (vault wins). Do not choose for him.

## Step 7 - verify

```sh
secrets list    # then for each path that applies to this host:
stat -c '%a %s %n' <path>      # expect 600 and size > 0
```
Then smoke-test the tools that exist on this machine - only commands that do not spend money
or send anything:
- `python3 ~/projects/elyes-vault/00_System/scripts/slideplate-send/slideplate-send.py check`
  (logs in to SMTP/IMAP, sends nothing)
- `node ~/projects/elyes-vault/00_System/scripts/webstamp/webstamp.mjs config` (prints config
  status, needs `npm install` in that folder first - see its README)
- Claude MCP servers: `fish ~/.claude/bin/mcp-bootstrap.fish` (needs `~/.claude/secrets.fish`
  from the `claude-mcp` item)

Skip anything not installed and say so.

## Step 8 - machine-specific items (only if Elyes wants them)

If this machine has credentials no other machine needs (e.g. a laptop-only token):
1. Elyes writes the file where the tool expects it, `chmod 600`.
2. Add a manifest line with **this** hostname in the hosts column:
   `item  group  format  hostname  ~/path/to/file`   (format: `env` / `fish` / `raw`)
3. [USER] `secrets push <item>` (vault must be unlocked).
4. Commit only the manifest:
   `git -C ~/dotfiles add secrets/.config/secrets/manifest.tsv && git -C ~/dotfiles commit -m "feat(secrets): add <item> for <hostname>"`
   Push only if Elyes says so.

## Report back

Finish with a short summary: hostname, `bw` version, which items were pulled (names + paths),
which smoke tests passed / were skipped, anything that failed with the exact error.
