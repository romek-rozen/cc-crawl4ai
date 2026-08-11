---
name: crawl4ai-install
description: Install or update Crawl4AI, Trafilatura, and browser dependencies in isolated Python virtual environments.
argument-hint: "[user|project|custom <directory>]"
disable-model-invocation: true
allowed-tools: Bash
---

# Install Crawl4AI runtime

Before asking for confirmation, clearly tell the user:

- installation normally takes about **5–15 minutes**, depending on internet speed, the Python package cache, and the computer;
- downloads may exceed **500 MB** because Crawl4AI dependencies and Chromium binaries are included;
- approximately **2 GB of free disk space** is recommended;
- Python 3.10+, `venv`, network access, and supported OS libraries are required;
- the terminal may appear busy for several minutes during large package or browser downloads.

Ask for confirmation before downloading anything. Then select one command:

```bash
# Persistent plugin data, shared across projects (recommended)
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" install --scope custom --directory "${CLAUDE_PLUGIN_DATA}" --project-root "${CLAUDE_PROJECT_DIR}"

# Current project only
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" install --scope project --project-root "${CLAUDE_PROJECT_DIR}"

# Explicit directory
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" install --scope custom --directory "/absolute/path" --project-root "${CLAUDE_PROJECT_DIR}"
```

Run the selected command directly so its `[step/total]` progress messages remain visible; do not hide all output behind `tail` or claim that a quiet step is stalled. The installer prints elapsed time and announces each environment, dependency, verification, and browser stage.

The installer creates separate `.venv` and `.trafilatura-venv` environments to avoid dependency conflicts. It runs `crawl4ai-setup` when available. Do not claim browser readiness unless the command confirms it. Exit code 2 means Python packages installed but browser setup was not verified. `--skip-browser` intentionally skips browser installation and must be reported as such.
