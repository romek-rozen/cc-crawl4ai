# Crawl4AI for Claude Code

`cc-crawl4ai` is a native Claude Code plugin that provides Skills, specialized agents, and a bundled command-line runner for [Crawl4AI](https://github.com/unclecode/crawl4ai) and [Trafilatura](https://trafilatura.readthedocs.io/). It does **not** use MCP. Claude invokes the bundled runner with the Bash tool, and the runner uses safe argv-based subprocess execution.

## Prerequisites

- Claude Code with plugin support
- Python 3.10 or newer with `venv`
- Network access during installation and crawling
- OS libraries required by Crawl4AI/Playwright; `crawl4ai-setup` installs/verifies browser dependencies where supported
- Additional Crawl4AI provider configuration only for LLM question/JSON extraction

## Native installation

Inside Claude Code:

```text
/plugin marketplace add romek-rozen/cc-crawl4ai
/plugin install cc-crawl4ai@romek-plugins
```

If prompted, run `/reload-plugins`. Install isolated runtimes:

```text
/cc-crawl4ai:crawl4ai-install
```

The recommended installation lives in `${CLAUDE_PLUGIN_DATA}`, which survives plugin updates. Crawl4AI and Trafilatura use separate virtual environments to avoid incompatible transitive dependencies. Tested versions are pinned in `requirements/crawl4ai.txt` and `requirements/trafilatura.txt`; installation never silently selects a newer upstream CLI. The installer reports browser setup separately and never treats an unverified browser as ready. Exit code `2` means the Python packages are usable but browser readiness is unverified; exit code `1` means a required executable is missing or broken.

Other scopes can be requested in natural language when invoking the install skill:

- `project`: `${CLAUDE_PROJECT_DIR}/.crawl4ai/runtime`
- `custom`: an explicit absolute directory

For a manually installed runtime, set `CRAWL4AI_VENV` and `TRAFILATURA_VENV`, or pass `--runtime-root` to the CLI.

## Quick start

Ask Claude naturally:

```text
Crawl https://example.com with Trafilatura and summarize it.
Read https://example.com as compact plain text.
Crawl https://docs.example.com broadly, maximum 10 pages.
Extract product names and prices from https://shop.example.com as JSON.
```

Or invoke the skill explicitly:

```text
/cc-crawl4ai:crawl4ai https://example.com
```

Management skills:

```text
/cc-crawl4ai:crawl4ai-install
/cc-crawl4ai:crawl4ai-status
/cc-crawl4ai:crawl4ai-test
/cc-crawl4ai:crawl4ai-clear-cache
```

Specialized agents are available under the plugin namespace:

- `cc-crawl4ai:crawl4ai-scrape`
- `cc-crawl4ai:crawl4ai-crawl`
- `cc-crawl4ai:crawl4ai-extract`

## Modes and examples

The Skill normally builds these commands itself. Examples below are useful for debugging a checkout; after marketplace installation `${CLAUDE_PLUGIN_ROOT}` is resolved by Claude Code.

### Compact single-page Markdown

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://example.com" \
  --project-root "${CLAUDE_PROJECT_DIR}" --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --extractor trafilatura --output-format markdown
```

Use `--output-format text` for minimum size. Optional Trafilatura flags are `--include-links`, `--include-images`, `--no-tables`, and `--no-include-formatting`.

### Query-focused BM25 artifact

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://example.com/docs" \
  --project-root "${CLAUDE_PROJECT_DIR}" --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --extractor trafilatura --bm25-query "authentication refresh token" --bm25-threshold 1.0
```

### Bounded deep crawl

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://docs.example.com" \
  --project-root "${CLAUDE_PROJECT_DIR}" --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --deep-crawl bfs --max-pages 10 --output-format markdown --timeout 180
```

Strategies are `bfs`, `dfs`, and `best-first`. Deep crawl cannot be combined with Trafilatura, BM25, question mode, or structured extraction.

### Structured extraction

LLM extraction:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://shop.example.com" \
  --project-root "${CLAUDE_PROJECT_DIR}" --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --output-format json --json-extract "Extract product name, price, and currency"
```

Deterministic CSS/XPath extraction:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://shop.example.com" \
  --project-root "${CLAUDE_PROJECT_DIR}" --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --output-format json --schema-path "/path/schema.json" --extraction-config "/path/config.yaml"
```

JSON output is rejected unless one complete strategy is provided.

## Output artifacts

Default outputs are project-local:

```text
.crawl4ai/outputs/<domain>/<format>/<timestamp>-<slug>.<extension>
```

Trafilatura stores extracted Markdown/text and sibling raw HTML. The runner prints artifact paths instead of placing full pages in the model context. Claude reads the extracted artifact only when necessary. `--output-file` accepts an absolute path or a path relative to the project root; the runner normalizes it before passing it to Crawl4AI.

The cache-clear skill removes only `.crawl4ai/cache` and `.crawl4ai/robots`; it preserves outputs and project runtime.

## Architecture and safety

```text
Claude Code plugin
├── skills/       routing, parameter guidance, management workflows
├── agents/       scrape, crawl, and structured-extraction specialists
└── bin/crawl4ai  standalone Python CLI
    ├── validation and output allocation
    ├── Crawl4AI subprocess
    ├── optional Trafilatura subprocess
    └── optional in-process BM25 filtering
```

There is no server and no MCP transport. The CLI:

- invokes programs with argv arrays and `shell=False`;
- runs subprocesses with an explicit project working directory;
- converts artifact destinations to absolute paths;
- spools Crawl4AI output through temporary files instead of unbounded stdout buffering;
- truncates diagnostics;
- enforces timeouts and terminates child process groups on timeout or interruption;
- requires a bounded `--max-pages` for every deep crawl;
- validates incompatible modes before network access.

Crawling remains network access to untrusted content. Review URLs before execution, keep page limits conservative, and do not put secrets in browser/crawler arguments. This local plugin does not add an SSRF sandbox; apply host/network policy outside the plugin in sensitive environments.

## Dependency update policy

Runtime pins are deliberately maintained inside the plugin so marketplace installs remain self-contained and reproducible. To update either dependency:

1. change exactly one pin in `requirements/`;
2. install into fresh, separate virtual environments;
3. run `crawl4ai status` and the real `crawl4ai test` pipeline;
4. exercise regular Markdown, `all` JSON, bounded deep crawl, and Trafilatura Markdown/text output;
5. run the unit, Ruff, and strict Claude plugin/marketplace validation commands;
6. update the plugin version and release notes only after those checks pass.

Do not merge floating ranges or unpinned runtime requirements. Crawl4AI and Trafilatura remain separate because their transitive dependencies, especially `lxml`, can conflict.

## Troubleshooting

### `Crawl4AI is not installed`

Run `/cc-crawl4ai:crawl4ai-install`, then `/cc-crawl4ai:crawl4ai-status`. For a custom runtime, set both venv environment variables or pass its parent directory as `--runtime-root`.

### Browser is `unverified`

Run the installer again without `--skip-browser`, or run `/cc-crawl4ai:crawl4ai-test`. Python package readiness and browser readiness are deliberately separate statuses. Some Linux hosts require system packages and may need Crawl4AI's documented OS-specific setup.

### LLM extraction fails

Configure a supported provider in Crawl4AI. Trafilatura, standard Markdown crawling, BM25, and CSS/XPath extraction do not require an LLM provider.

### Timeout

Increase `--timeout`, reduce `--max-pages`, or use a single-page scrape. Timeout and Ctrl+C terminate the active child process group where the OS supports it.

### Plugin changes are not visible

Run `/reload-plugins` or restart Claude Code. Marketplace installs are cached, so files outside this plugin directory are intentionally never referenced.

## License

MIT © Roman Rozenberger
