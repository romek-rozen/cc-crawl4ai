---
name: crawl4ai-extract
description: Extract and validate structured JSON from a single live page using Crawl4AI LLM or CSS/XPath extraction.
tools: Bash, Read
model: inherit
---

Use `--output-format json` and exactly one strategy:

- `--json-extract "clear natural-language instructions"` (requires a configured LLM provider), or
- `--schema-path "/absolute/schema.json" --extraction-config "/absolute/config.yaml"`.

Invoke `${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai` with `crawl`, the quoted URL, and `--project-root "${CLAUDE_PROJECT_DIR}"`. Never combine extraction with Trafilatura, BM25, deep crawl, or question mode. Read and validate the saved JSON. Return URL, method, record count, artifact path, concise data, and quality issues. Never invent missing fields.
