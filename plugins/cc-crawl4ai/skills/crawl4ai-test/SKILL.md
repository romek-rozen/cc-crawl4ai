---
name: crawl4ai-test
description: Smoke-test the complete Crawl4AI to Trafilatura pipeline against example.com.
disable-model-invocation: true
allowed-tools: Bash
---

This accesses `https://example.com`. Ask for confirmation if network execution was not already requested, then run:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" test --project-root "${CLAUDE_PROJECT_DIR}" --runtime-root "${CLAUDE_PLUGIN_DATA}" --timeout 60
```

Report the exact result. A successful test records browser readiness for the detected managed runtime.
