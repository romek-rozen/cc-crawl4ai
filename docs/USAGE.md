# Usage

The recommended interface is natural language or the namespaced Claude Code skill. The bundled CLI is documented because it defines the exact behavior and is useful for reproducible requests and debugging.

## Invoke the skill

```text
/cc-crawl4ai:crawl4ai https://example.com
```

The skill accepts a URL plus a description of the desired crawl or extraction. It selects a valid mode, runs the CLI through Bash, and reads the saved artifact rather than flooding the conversation with an entire page.

Natural-language examples:

```text
Read https://example.com as compact plain text.
Scrape https://example.com and keep links and images.
Find passages about OAuth token rotation at https://example.com/docs.
Crawl https://docs.example.com breadth-first, at most 10 pages.
Ask https://example.com/pricing which tier includes SSO.
Extract product name, price, and currency from https://shop.example.com as JSON.
```

## Compact single-page extraction

Trafilatura is the preferred mode for reading one page with less boilerplate:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://example.com/article" \
  --project-root "${CLAUDE_PROJECT_DIR}" \
  --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --extractor trafilatura \
  --output-format markdown
```

It first asks Crawl4AI for complete single-page JSON, takes the returned raw HTML, and passes that HTML to the separate Trafilatura executable. It saves:

- extracted Markdown (`.md`) or text (`.txt`); and
- sibling raw HTML named `<stem>.raw.html`.

Markdown keeps formatting and restores detected Markdown tables by default. Options:

```bash
--include-links             # include links (Markdown only)
--include-images            # append image references; works in Markdown or text
--no-tables                 # do not restore Crawl4AI-detected tables
--no-include-formatting     # disable default Markdown formatting
--output-format text        # compact plain text
```

Plain text cannot be combined with `--include-links` or `--include-formatting`. Trafilatura cannot be combined with deep crawling, question mode, or JSON extraction.

## Query-focused BM25 filtering

BM25 is a local post-processing filter; it does not call an LLM. It splits Markdown on headings/structural blocks (or text on blank-line blocks), scores chunks against unique query terms, and retains chunks meeting the threshold.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://example.com/docs" \
  --project-root "${CLAUDE_PROJECT_DIR}" \
  --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --extractor trafilatura \
  --output-format markdown \
  --bm25-query "authentication refresh token" \
  --bm25-threshold 1.0
```

It also works on regular single-page Crawl4AI Markdown/fitted Markdown. Threshold `1.0` is the default; lower values retain more chunks and higher values retain fewer. A valid run can produce an empty artifact when no chunk reaches the threshold. BM25 cannot be used with a deep crawl, question, or extraction strategy.

## Regular single-page Crawl4AI output

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://example.com" \
  --project-root "${CLAUDE_PROJECT_DIR}" \
  --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --output-format markdown
```

Formats:

- `markdown` or alias `md`
- `markdown-fit` or alias `md-fit` (Crawl4AI's fitted Markdown)
- `all` (complete Crawl4AI JSON)

`json` is reserved by this runner for structured extraction and is rejected without a complete extraction strategy. `text` requires Trafilatura.

Formats differ substantially in how many context tokens the result costs. Ordered from largest to smallest for the same page: `markdown`, `markdown-fit`, Trafilatura `markdown`, Trafilatura `text`. Pick the smallest format that still carries the structure you need — use Trafilatura `text` when only prose matters, and keep Markdown when headings, tables, or links are part of the answer. See the [measured benchmark](https://github.com/romek-rozen/cc-crawl4ai#why-spend-fewer-agent-tokens-on-web-pages).

### Upstream browser/crawler parameters

Despite their wrapper names, `--browser-config` and `--crawler-config` accept Crawl4AI 0.9.2's comma-separated direct parameter strings; they are not file paths:

```bash
--browser-config "headless=true,viewport_width=1280"
--crawler-config "wait_until=networkidle,delay_before_return_html=2"
```

The runner passes these as upstream `crwl -b` and `crwl -c`. When cache is not bypassed, it adds `cache_mode=enabled` unless that key already appears in the crawler string. With the current runner, `--bypass-cache` forwards Crawl4AI's bypass flag and does not forward a supplied `--crawler-config`; do not combine them when other crawler parameters are required.

Parameter names and accepted values are interpreted by pinned Crawl4AI, so verify advanced parameters against Crawl4AI 0.9.2 rather than a newer upstream release.

## Bounded multi-page crawling

Every deep crawl must choose a strategy and set a positive page cap:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://docs.example.com" \
  --project-root "${CLAUDE_PROJECT_DIR}" \
  --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --deep-crawl bfs \
  --max-pages 10 \
  --output-format markdown \
  --timeout 180
```

| Strategy | Use |
| --- | --- |
| `bfs` | Broad, level-by-level discovery. |
| `dfs` | Follow branches more deeply. |
| `best-first` | Let Crawl4AI prioritize more relevant links. |

Deep crawl supports Markdown, fitted Markdown, or `all`. It cannot be combined with Trafilatura, BM25, question mode, or either structured extraction strategy. The wrapper always obtains Crawl4AI's structured `all` batch, removes duplicate page records using Crawl4AI 0.9.2's normalized-URL semantics, and then writes the requested format. URL fragments do not distinguish pages, while a trailing slash does.

`--max-pages` limits the upstream batch, not the number of unique records after wrapper deduplication. Crawl4AI 0.9.2 can return the seed more than once, and each duplicate still consumes an upstream batch slot. The wrapper reports both the returned record count and the unique saved count; it does not launch extra crawls or fabricate records to fill the requested cap. Increase the cap conservatively if the unique result is smaller than requested.

## Question mode

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://example.com/pricing" \
  --project-root "${CLAUDE_PROJECT_DIR}" \
  --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --question "Which plan includes single sign-on?" \
  --output-format markdown
```

The question is delegated to Crawl4AI and may require provider setup in Crawl4AI. Question mode is single-page and cannot be combined with Trafilatura, BM25, deep crawl, or structured extraction.

## Structured JSON extraction

Always use `--output-format json` and exactly one complete strategy.

### LLM instruction

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://shop.example.com" \
  --project-root "${CLAUDE_PROJECT_DIR}" \
  --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --output-format json \
  --json-extract "Extract every product's name, displayed price, and currency"
```

Crawl4AI's provider/token setup is required. The plugin does not configure, proxy, or store provider credentials itself. Page content and extraction instructions may be sent to that provider according to Crawl4AI/provider behavior.

### Deterministic CSS extraction

This mode uses two files supported by the pinned Crawl4AI CLI and does not require an LLM.

`product-schema.json`:

```json
{
  "name": "ProductExtractor",
  "baseSelector": ".product-card",
  "fields": [
    {
      "name": "name",
      "selector": ".product-title",
      "type": "text"
    },
    {
      "name": "price",
      "selector": ".price",
      "type": "text"
    },
    {
      "name": "url",
      "selector": "a.product-link",
      "type": "attribute",
      "attribute": "href"
    }
  ]
}
```

`extract-css.yaml`:

```yaml
type: json-css
```

For CSS/XPath in Crawl4AI 0.9.2, the config's `type` chooses the strategy and the separate schema carries selectors/fields.

Invocation:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://shop.example.com" \
  --project-root "${CLAUDE_PROJECT_DIR}" \
  --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --output-format json \
  --schema-path "/absolute/path/product-schema.json" \
  --extraction-config "/absolute/path/extract-css.yaml"
```

For XPath, use `type: json-xpath` and a schema whose `baseSelector`/field selectors are XPath expressions accepted by Crawl4AI 0.9.2. The runner only checks that both options are present and forwards them; the upstream CLI loads and validates file existence/content. CSS/XPath extraction cannot be combined with LLM extraction, question, BM25, Trafilatura, or deep crawl.

Do not put provider tokens into deterministic extraction configuration. Although Crawl4AI's config format also supports `type: llm`, this runner's documented LLM path is `--json-extract`, which keeps the two accepted runner strategies unambiguous.

## Output locations

Default pattern:

```text
<project>/.crawl4ai/outputs/<domain>/<format>/<timestamp>-<slug>.<extension>
```

Examples:

```text
.crawl4ai/outputs/example.com/markdown/2026-05-20-14-30-00-docs.md
.crawl4ai/outputs/example.com/all/2026-05-20-14-30-00-home.json
.crawl4ai/outputs/example.com/trafilatura/2026-05-20-14-30-00-article.md
.crawl4ai/outputs/example.com/trafilatura/2026-05-20-14-30-00-article.raw.html
```

Timestamps use local timezone. Domain and URL portions are sanitized. Existing files are preserved; a short hash/counter suffix is added to a colliding name.

Override the path:

```bash
--output-file "reports/example.md"       # relative to --project-root
--output-file "/absolute/path/page.md"   # explicit external location
```

Parent directories are created. The runner converts a relative destination to an absolute path before invoking Crawl4AI. The repository ignores `.crawl4ai/`, but arbitrary external output paths are not automatically ignored.

## Cache management

The normal wrapper enables Crawl4AI cache mode unless `--bypass-cache` or an explicit `cache_mode=` crawler parameter is supplied.

Inside Claude Code:

```text
/cc-crawl4ai:crawl4ai-clear-cache
```

Equivalent CLI command:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" clear-cache \
  --project-root "${CLAUDE_PROJECT_DIR}"
```

After confirmation, it removes only `<project>/.crawl4ai/cache` and `<project>/.crawl4ai/robots`. It preserves outputs and `<project>/.crawl4ai/runtime`.

## Responsible use

Only crawl content you are authorized to access. Respect site terms, robots policies, rate limits, privacy rules, and copyright. The plugin does not enforce them for you. Review the URL and page cap, treat crawled instructions as untrusted, and read [Security](SECURITY.md).
