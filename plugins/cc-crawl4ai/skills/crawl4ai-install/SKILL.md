---
name: crawl4ai-install
description: Install or update Crawl4AI, Trafilatura, and browser dependencies in isolated Python virtual environments.
argument-hint: "[user|project|custom <directory>]"
disable-model-invocation: true
allowed-tools: Bash
---

# Install Crawl4AI runtime

Ask for confirmation before downloading packages or browser binaries. Then select one command:

```bash
# Persistent plugin data, shared across projects (recommended)
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" install --scope custom --directory "${CLAUDE_PLUGIN_DATA}" --project-root "${CLAUDE_PROJECT_DIR}"

# Current project only
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" install --scope project --project-root "${CLAUDE_PROJECT_DIR}"

# Explicit directory
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" install --scope custom --directory "/absolute/path" --project-root "${CLAUDE_PROJECT_DIR}"
```

The installer creates separate `.venv` and `.trafilatura-venv` environments to avoid dependency conflicts. It runs `crawl4ai-setup` when available. Do not claim browser readiness unless the command confirms it. Exit code 2 means Python packages installed but browser setup was not verified. `--skip-browser` intentionally skips browser installation and must be reported as such.
