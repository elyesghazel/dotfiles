#!/usr/bin/env fish
#
# Make a second Claude profile (CLAUDE_CONFIG_DIR) use this profile's config.
#
# T3's "Claude Isaac" instance runs with CLAUDE_CONFIG_DIR=~/.claude-isaac so
# usage is billed to Isaac's account. Login, claude.ai connectors and synced
# claude.ai skills stay his; everything else is linked or copied from ~/.claude:
#
#   - CLAUDE.md, settings.json, commands/, bin/, mcp/  -> symlinks
#   - each personal skill                              -> symlink in skills/
#   - user-scope mcpServers from ~/.claude.json        -> copied into its .claude.json
#
# MCP servers have to be copied because .claude.json also holds the account.
# Idempotent; run by claude-profile-share.timer.
#
#   fish ~/.claude/bin/claude-profile-share.fish [profile-dir]

set -l src $HOME/.claude
set -l dst $HOME/.claude-isaac
test (count $argv) -gt 0; and set dst $argv[1]

if not test -f $dst/.claude.json
    echo "error: $dst/.claude.json missing — log in to that profile first."
    exit 1
end

function _link -a from to
    if test -L $to; and test (readlink $to) = $from
        return
    end
    # Claude rewrites settings.json atomically, which turns the link back into a
    # file. Keep that copy so a permission granted in the other profile isn't lost.
    if test -e $to; and not test -L $to
        mv $to $to.bak.(date +%Y%m%d-%H%M%S)
    end
    ln -sfn $from $to
    echo "  link $to"
end

for item in CLAUDE.md settings.json commands bin mcp
    test -e $src/$item; and _link (realpath $src/$item) $dst/$item
end

mkdir -p $dst/skills
for skill in $src/skills/*/
    set -l name (basename $skill)
    # synced/ is claude.ai's own skill sync, per account.
    test $name = synced; and continue
    _link (realpath $skill) $dst/skills/$name
end
for link in $dst/skills/*
    if test -L $link; and not test -e $link
        rm $link
        echo "  drop $link"
    end
end

python3 -c '
import json, os, sys, tempfile
src, dst = sys.argv[1], sys.argv[2]
servers = json.load(open(src)).get("mcpServers", {})
data = json.load(open(dst))
if data.get("mcpServers") == servers:
    sys.exit(0)
data["mcpServers"] = servers
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dst))
with os.fdopen(fd, "w") as f:
    json.dump(data, f, indent=2)
os.chmod(tmp, 0o600)
os.replace(tmp, dst)
print("  mcp  " + ", ".join(servers))
' $HOME/.claude.json $dst/.claude.json
