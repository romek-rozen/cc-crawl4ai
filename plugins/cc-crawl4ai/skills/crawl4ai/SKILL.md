---
name: crawl4ai
description: Crawl, scrape, question, or extract structured data from live websites with Crawl4AI and optional Trafilatura. Use for fresh web content, multi-page crawls, compact page reading, and JSON extraction.
argument-hint: "<URL> [what to crawl or extract]"
allowed-tools: Bash, Read
---

# Crawl4AI

Use the bundled non-MCP CLI. Every invocation must use the resolved plugin and project placeholders:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "URL" --project-root "${CLAUDE_PROJECT_DIR}" --runtime-root "${CLAUDE_PLUGIN_DATA}" [options]
```

Quote every argument. Never concatenate user input into a shell fragment. The CLI validates parameters and invokes subprocesses without a shell.

## Choose a mode

### Compact single-page scrape (preferred for reading)

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://example.com" \
  --project-root "${CLAUDE_PROJECT_DIR}" --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --extractor trafilatura --output-format markdown
```

Trafilatura supports only a single page and `markdown`, `md`, or `text`. Markdown formatting and tables are retained by default. Add `--include-links`, `--include-images`, `--no-tables`, or `--no-include-formatting` only when requested. It saves both extracted content and sibling `.raw.html`.

For query-focused content, add:

```text
--bm25-query "specific search terms" --bm25-threshold 1.0
```

BM25 runs after Trafilatura when both are selected. A higher threshold returns fewer structural chunks.

### Regular single-page Crawl4AI output

Use `--output-format markdown` (default), `markdown-fit`, or `all`. `md` and `md-fit` are aliases. `--question "..."` asks Crawl4AI a natural-language question and may require a configured provider.

### Bounded multi-page crawl

Always set a traversal and explicit page cap:

```text
--deep-crawl bfs --max-pages 10
```

- `bfs`: broad discovery.
- `dfs`: follow branches deeply.
- `best-first`: prioritize relevant pages.
- Use Markdown, Markdown-fit, or all output.
- Do not combine deep crawl with Trafilatura, BM25, question mode, or JSON extraction.

### Structured JSON extraction

Use `--output-format json` and exactly one extraction strategy:

- LLM: `--json-extract "Extract product name and price"` (requires Crawl4AI LLM provider configuration).
- Deterministic CSS/XPath: `--schema-path "/absolute/schema.json" --extraction-config "/absolute/config.yaml"`.

Do not request JSON without an extraction strategy.

## Other options

- `--browser-config "key=value,..."`
- `--crawler-config "key=value,..."`; cache mode is added automatically unless specified.
- `--bypass-cache` only when freshness matters.
- `--output-file "path"`; relative paths resolve under the project and become absolute before execution.
- `--timeout 120`; default is 60 seconds.

The full CLI contract is available with:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl --help
```

## Artifact contract

Default artifacts are written under:

```text
${CLAUDE_PROJECT_DIR}/.crawl4ai/outputs/<domain>/<format>/
```

The command prints paths, not full page contents. Use `Read` on the relevant extracted artifact only after crawling. Read raw HTML only for debugging. Report the source URL, options used, artifact paths, and concise findings. Never guess page content.

If the runtime is missing, invoke or recommend `/cc-crawl4ai:crawl4ai-install`. Use `/cc-crawl4ai:crawl4ai-status` for diagnostics.
