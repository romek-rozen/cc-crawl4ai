# Crawl4AI for Claude Code

`cc-crawl4ai` is a native Claude Code plugin for crawling with [Crawl4AI](https://github.com/unclecode/crawl4ai) and compact local extraction with [Trafilatura](https://trafilatura.readthedocs.io/). It provides namespaced skills, specialized agents, and a bundled Python runner. It does **not** use MCP.

Its main purpose is to save agent context tokens: pages are rendered and stripped of navigation and boilerplate before Claude reads them, while large results remain in artifacts. In a measured test on [Claude Code's features overview](https://code.claude.com/docs/en/features-overview), compact Trafilatura text reduced the saved content from 8,269 to 2,805 tokens—a **66.1% reduction**. See the [full benchmark and methodology](https://github.com/romek-rozen/cc-crawl4ai#why-spend-fewer-agent-tokens-on-web-pages).

This README stays with marketplace-installed copies. The canonical, versioned manuals are:

- [Installation and marketplace lifecycle](https://github.com/romek-rozen/cc-crawl4ai/blob/main/docs/INSTALLATION.md)
- [Usage and extraction examples](https://github.com/romek-rozen/cc-crawl4ai/blob/main/docs/USAGE.md)
- [Complete CLI reference](https://github.com/romek-rozen/cc-crawl4ai/blob/main/docs/CLI_REFERENCE.md)
- [Troubleshooting](https://github.com/romek-rozen/cc-crawl4ai/blob/main/docs/TROUBLESHOOTING.md)
- [Security and privacy](https://github.com/romek-rozen/cc-crawl4ai/blob/main/docs/SECURITY.md)
- [Development and releases](https://github.com/romek-rozen/cc-crawl4ai/blob/main/docs/DEVELOPMENT.md)

## Requirements

- Claude Code with plugin/marketplace support
- Python 3.10+ with `venv`
- Network access and Crawl4AI browser/OS dependencies
- A Crawl4AI-supported provider only for question and LLM extraction modes

Plugin `0.1.2` pins Crawl4AI `0.9.2` and Trafilatura `2.2.0` in separate virtual environments.

## Install

Inside Claude Code:

```text
/plugin marketplace add romek-rozen/cc-crawl4ai
/plugin install cc-crawl4ai@romek-plugins
/reload-plugins
/cc-crawl4ai:crawl4ai-install
```

The install workflow requests confirmation before downloading. It normally uses persistent `${CLAUDE_PLUGIN_DATA}` and reports Python package readiness separately from browser verification. Check both tools and the complete browser pipeline with:

```text
/cc-crawl4ai:crawl4ai-status
/cc-crawl4ai:crawl4ai-test
```

## Use

Ask Claude naturally:

```text
Read https://example.com as compact Markdown.
Find the passages about refresh tokens at https://example.com/docs.
Crawl https://docs.example.com breadth-first, no more than 10 pages.
Extract product names and prices from https://shop.example.com as JSON.
```

Or invoke the main skill:

```text
/cc-crawl4ai:crawl4ai https://example.com
```

Available skills:

```text
/cc-crawl4ai:crawl4ai
/cc-crawl4ai:crawl4ai-install
/cc-crawl4ai:crawl4ai-status
/cc-crawl4ai:crawl4ai-test
/cc-crawl4ai:crawl4ai-clear-cache
```

Specialized agents:

```text
cc-crawl4ai:crawl4ai-scrape
cc-crawl4ai:crawl4ai-crawl
cc-crawl4ai:crawl4ai-extract
```

The usual compact-page command is:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://example.com" \
  --project-root "${CLAUDE_PROJECT_DIR}" \
  --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --extractor trafilatura --output-format markdown
```

Run `"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl --help` for the installed CLI's exact options.

## Artifacts and safety

Default artifacts are project-local:

```text
${CLAUDE_PROJECT_DIR}/.crawl4ai/outputs/<domain>/<format>/
```

Trafilatura stores extracted Markdown/text and sibling raw HTML. The runner prints paths rather than full page content; agents read only the relevant artifact. Cache clearing removes only project `.crawl4ai/cache` and `.crawl4ai/robots`, preserving outputs and runtime.

The runner validates incompatible modes, requires bounded deep crawls, invokes subprocesses without a shell, bounds diagnostics, and handles timeouts/interruption. Crawling still processes untrusted content and this plugin is not an SSRF or prompt-injection sandbox. Protect raw HTML/output, do not place secrets in prompts/arguments, and review the canonical [security manual](https://github.com/romek-rozen/cc-crawl4ai/blob/main/docs/SECURITY.md).

## License

MIT © Roman Rozenberger
