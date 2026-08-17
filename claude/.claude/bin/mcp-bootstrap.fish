#!/usr/bin/env fish
#
# Recreate user-scope MCP servers on a new machine.
#
# MCP servers live in ~/.claude.json, which also holds oauth tokens, userID,
# machineID and per-project history — so that file is gitignored and can never
# be synced. This script is the versioned source of truth instead: the server
# definitions are tracked here, the secrets are not.
#
#   1. cp ~/.claude/secrets.fish.example ~/.claude/secrets.fish
#   2. fill in the real values (secrets.fish is gitignored)
#   3. fish ~/.claude/bin/mcp-bootstrap.fish
#
# Idempotent: existing servers of the same name are replaced.

set -l secrets ~/.claude/secrets.fish

if not test -f $secrets
    echo "error: $secrets not found."
    echo "       cp ~/.claude/secrets.fish.example $secrets and fill it in."
    exit 1
end

source $secrets

function _mcp_add
    set -l name $argv[1]
    claude mcp remove --scope user $name >/dev/null 2>&1
    if claude mcp add --scope user $argv
        echo "  ok   $name"
    else
        echo "  FAIL $name"
    end
end

echo "==> Registering user-scope MCP servers"

# --- excalidraw: self-hosted bridge, reachable over the tailnet only ---------
if set -q EXCALIDRAW_MCP_URL; and set -q EXCALIDRAW_MCP_TOKEN
    _mcp_add excalidraw -t http $EXCALIDRAW_MCP_URL \
        --header "Authorization: Bearer $EXCALIDRAW_MCP_TOKEN"
else
    echo "  skip excalidraw (EXCALIDRAW_MCP_URL / EXCALIDRAW_MCP_TOKEN unset)"
end

# --- markitdown: local stdio server, no secrets -----------------------------
if command -q markitdown-mcp
    _mcp_add markitdown -t stdio markitdown-mcp
else
    echo "  skip markitdown (markitdown-mcp not on PATH — uv tool install markitdown-mcp)"
end

echo
echo "==> Result"
claude mcp list
