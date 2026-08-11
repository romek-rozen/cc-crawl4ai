---
name: crawl4ai-clear-cache
description: Remove project-local Crawl4AI cache and robots data without deleting outputs or installed runtimes.
disable-model-invocation: true
allowed-tools: Bash
---

Confirm the destructive cache removal, then run:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" clear-cache --project-root "${CLAUDE_PROJECT_DIR}"
```

This removes only `.crawl4ai/cache` and `.crawl4ai/robots`. It preserves `.crawl4ai/outputs` and `.crawl4ai/runtime`.
