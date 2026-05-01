#!/bin/bash

echo "post-create.sh"

git config --global --add safe.directory "${CONTAINER_WORKSPACE_FOLDER}"

# Register Context7 MCP with Claude Code (idempotent)
if ! claude mcp get context7 >/dev/null 2>&1; then
    claude mcp add context7 -- context7-mcp
fi
