#!/bin/bash

echo "post-start.sh"

if [ -n "$GIT_USER_NAME_OVERRIDE" ]; then
    git config --global user.name "$GIT_USER_NAME_OVERRIDE"
    echo "Git user.name set to $GIT_USER_NAME_OVERRIDE"
fi

if [ -n "$GIT_USER_EMAIL_OVERRIDE" ]; then
    git config --global user.email "$GIT_USER_EMAIL_OVERRIDE"
    echo "Git user.email set to $GIT_USER_EMAIL_OVERRIDE"
fi

# Keep the Linux uv venv separate from any Windows venv that may share this folder.
# Windows side keeps the default `.venv` so end-users need no extra setup.
if ! grep -q 'UV_PROJECT_ENVIRONMENT' ~/.bashrc; then
    echo 'export UV_PROJECT_ENVIRONMENT=.venv-linux' >> ~/.bashrc
fi
export UV_PROJECT_ENVIRONMENT=.venv-linux
