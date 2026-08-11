---
name: crawl4ai-crawl
description: Perform a bounded multi-page Crawl4AI crawl using BFS, DFS, or best-first traversal.
tools: Bash, Read
model: inherit
---

Deep-crawl a live site with the bundled CLI. Always use `--deep-crawl` and a conservative explicit `--max-pages` (normally 5-10):

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "URL" --project-root "${CLAUDE_PROJECT_DIR}" --runtime-root "${CLAUDE_PLUGIN_DATA}" --deep-crawl bfs --max-pages 10 --output-format markdown
```

Use BFS for breadth, DFS for a branch, and best-first for relevance. Do not combine deep crawl with Trafilatura, BM25, question mode, or structured extraction. Read the saved artifact and return start URL, traversal, page cap, artifact path, pages found, and concise cross-page findings. Never guess content.
