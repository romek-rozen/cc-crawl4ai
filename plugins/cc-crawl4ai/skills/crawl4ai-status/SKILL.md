---
name: crawl4ai-status
description: Check Crawl4AI, Trafilatura, and browser setup status for this plugin.
disable-model-invocation: true
allowed-tools: Bash
---

Run:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" status --project-root "${CLAUDE_PROJECT_DIR}" --runtime-root "${CLAUDE_PLUGIN_DATA}"
```

Report the detected executable paths and preserve the distinction between browser `verified` and `unverified`.
