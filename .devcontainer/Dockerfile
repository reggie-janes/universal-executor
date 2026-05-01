FROM mcr.microsoft.com/devcontainers/python:3.14

# Install Node.js (required for Context7 MCP)
USER root
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Switch to user 'dev'
RUN useradd -ms /bin/bash dev
USER dev

WORKDIR /home/dev

# Install Claude Code
RUN curl -v -fsSL https://claude.ai/install.sh | bash
ENV PATH="/home/dev/.local/bin:${PATH}"

# Install Context7 MCP server locally (avoids npx fetch on each invocation)
ENV NPM_CONFIG_PREFIX=/home/dev/.npm-global
ENV PATH="/home/dev/.npm-global/bin:${PATH}"
RUN mkdir -p /home/dev/.npm-global \
    && npm install -g @upstash/context7-mcp
