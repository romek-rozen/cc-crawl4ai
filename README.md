# cc-crawl4ai

[![GitHub release](https://img.shields.io/badge/version-0.1.1-blue)](https://github.com/romek-rozen/cc-crawl4ai)
[![GitHub license](https://img.shields.io/github/license/romek-rozen/cc-crawl4ai)](LICENSE)
[![Built with Crawl4AI](https://img.shields.io/badge/Built%20with-Crawl4AI-blue)](https://github.com/unclecode/crawl4ai)
[![Built with Trafilatura](https://img.shields.io/badge/Built%20with-Trafilatura-orange)](https://github.com/adbar/trafilatura)
[![Built for Claude Code](https://img.shields.io/badge/Built%20for-Claude%20Code-D97757)](https://github.com/anthropics/claude-code)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-EA4AAA?logo=githubsponsors)](https://github.com/sponsors/romek-rozen)

A native [Claude Code](https://github.com/anthropics/claude-code) plugin for crawling live websites with [Crawl4AI](https://github.com/unclecode/crawl4ai) and extracting compact Markdown or text with [Trafilatura](https://trafilatura.readthedocs.io/).

`cc-crawl4ai` gives Claude Code one crawling skill, four runtime-management skills, three specialized agents, and a bundled Python command-line runner. It is deliberately **not an MCP server**: Claude invokes a local executable through Bash, and the executable launches pinned Crawl4AI and Trafilatura tools without a shell.

## What it does

- Reads one page into compact Trafilatura Markdown or plain text.
- Saves regular Crawl4AI Markdown, fitted Markdown, JSON, or complete output.
- Performs bounded BFS, DFS, or best-first multi-page crawls.
- Filters single-page Markdown/text into query-relevant structural chunks with local BM25 scoring.
- Extracts structured JSON through Crawl4AI's LLM or deterministic CSS/XPath strategies.
- Keeps large results in project-local artifacts instead of injecting full pages into the conversation.
- Installs Crawl4AI and Trafilatura in separate, pinned virtual environments.

## Requirements

- Claude Code with plugin and marketplace support.
- Python 3.10 or newer, including the standard-library `venv` module.
- Network access to install Python packages/browser binaries and to crawl target sites.
- Platform libraries required by Crawl4AI and its browser runtime.
- About **2 GB of free disk space** for isolated environments and browser binaries.
- A separately configured Crawl4AI LLM provider only for question mode and LLM JSON extraction.

The pinned compatibility set for plugin `0.1.1` is Crawl4AI `0.9.2` and Trafilatura `2.2.0`. The runner handles POSIX and Windows virtual-environment layouts/process termination, but its process-group tests are POSIX-only and browser availability still depends on upstream host support. See [Installation](docs/INSTALLATION.md#compatibility-and-platform-notes).

## Install

Run these commands **inside Claude Code**:

```text
/plugin marketplace add romek-rozen/cc-crawl4ai
/plugin install cc-crawl4ai@romek-plugins
```

If requested, run `/reload-plugins`. Then install the isolated Python and browser runtime:

```text
/cc-crawl4ai:crawl4ai-install
```

The install skill asks before downloading dependencies. A first installation normally takes **5–15 minutes**, depending on internet speed and local caches, and may download **more than 500 MB** of packages and Chromium binaries. The installer displays numbered stages and elapsed time throughout the process. Its recommended runtime is persistent `${CLAUDE_PLUGIN_DATA}`, so updating the plugin does not discard it.

Check the installation:

```text
/cc-crawl4ai:crawl4ai-status
/cc-crawl4ai:crawl4ai-test
```

The test accesses `https://example.com` and verifies the complete Crawl4AI → Trafilatura pipeline.

For project/custom scopes, update and removal instructions, and exit-code details, read **[Installation](docs/INSTALLATION.md)**.

## Quick start

Ask Claude naturally:

```text
Read https://example.com as compact Markdown and summarize it.
Crawl https://docs.example.com broadly, with a limit of 10 pages.
Find the sections about refresh tokens at https://example.com/docs.
Extract product names and prices from https://shop.example.com as JSON.
```

Or invoke the main skill directly:

```text
/cc-crawl4ai:crawl4ai https://example.com
```

The default compact-page command produced by the skill is equivalent to:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" crawl "https://example.com" \
  --project-root "${CLAUDE_PROJECT_DIR}" \
  --runtime-root "${CLAUDE_PLUGIN_DATA}" \
  --extractor trafilatura \
  --output-format markdown
```

`${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, and `${CLAUDE_PROJECT_DIR}` are Claude Code runtime placeholders. The shell example is mainly for debugging a loaded plugin; use a real path when running the bundled CLI directly from a checkout.

## Skills and agents

| Component | Purpose |
| --- | --- |
| `/cc-crawl4ai:crawl4ai` | Route a crawl, scrape, question, BM25 filter, or extraction request. |
| `/cc-crawl4ai:crawl4ai-install` | Install or update pinned Python runtimes and browser dependencies. |
| `/cc-crawl4ai:crawl4ai-status` | Probe both executables and report browser verification separately. |
| `/cc-crawl4ai:crawl4ai-test` | Smoke-test the real pipeline against `example.com`. |
| `/cc-crawl4ai:crawl4ai-clear-cache` | Remove only project `.crawl4ai/cache` and `.crawl4ai/robots`. |
| `cc-crawl4ai:crawl4ai-scrape` | Specialized one-page Trafilatura agent. |
| `cc-crawl4ai:crawl4ai-crawl` | Specialized bounded deep-crawl agent. |
| `cc-crawl4ai:crawl4ai-extract` | Specialized structured-JSON extraction agent. |

Management skills cannot be invoked automatically by the model. Install and test workflows request confirmation before network downloads/access, and cache clearing requests confirmation before deletion.

## Modes at a glance

| Goal | Required options | Important constraints |
| --- | --- | --- |
| Compact page | `--extractor trafilatura` | One page; Markdown/`md`/text only. |
| Local relevance filter | `--bm25-query "terms"` | One page; Markdown or text; no question/extraction/deep crawl. |
| Deep crawl | `--deep-crawl bfs --max-pages 10` | Explicit positive page cap required; Markdown, fitted Markdown, or `all`. |
| LLM JSON | `--output-format json --json-extract "instruction"` | Requires Crawl4AI provider configuration. |
| CSS/XPath JSON | `--output-format json --schema-path ... --extraction-config ...` | Both files required; no LLM required. |
| Question | `--question "..."` | Single page; may require a configured provider. |

See **[Usage](docs/USAGE.md)** for complete examples and extraction configuration, and **[CLI reference](docs/CLI_REFERENCE.md)** for every option, incompatibility, runtime lookup rule, artifact path, and exit code.

## Artifacts

By default, output is stored beneath the active project:

```text
.crawl4ai/outputs/<domain>/<format>/<local-timestamp>-<url-slug>.<extension>
```

Trafilatura uses the `trafilatura/` format directory and also saves sibling `*.raw.html`. Existing names are never overwritten: the runner adds a deterministic suffix when necessary. An explicit relative `--output-file` is resolved under the project root; an absolute path is accepted as-is.

The runner prints saved paths. Claude's skill/agents then read only the relevant artifact. Outputs, raw HTML, runtime state, and upstream crawler caches can contain sensitive information; protect the project and runtime directories accordingly.

## Architecture

```text
Claude Code
└── cc-crawl4ai plugin
    ├── skills/                 routing and managed workflows
    ├── agents/                 scrape, deep-crawl, extraction specialists
    └── bin/crawl4ai            validation and orchestration
        ├── crwl subprocess     Crawl4AI 0.9.2
        ├── trafilatura process Trafilatura 2.2.0 (optional)
        └── local BM25 filter   no external model (optional)
```

There is no resident service, npm runtime package, or MCP transport. `package.json` is private repository metadata and validation convenience only.

## Documentation

- [Installation and marketplace lifecycle](docs/INSTALLATION.md)
- [Usage and examples](docs/USAGE.md)
- [CLI reference](docs/CLI_REFERENCE.md)
- [Development, architecture, and releases](docs/DEVELOPMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Security and privacy](docs/SECURITY.md)
- [Plugin-local README](plugins/cc-crawl4ai/README.md)

## Development

```bash
npm test
npm run validate
claude plugin validate plugins/cc-crawl4ai
claude plugin validate .
```

See [Development](docs/DEVELOPMENT.md) for local loading, version synchronization, dependency compatibility testing, and the manual marketplace release workflow.

## Security

Crawling is network access to untrusted content. This plugin validates modes and URLs, uses argv-based subprocess execution with `shell=False`, bounds diagnostics, and terminates child process groups on timeouts where supported. It does **not** provide an SSRF sandbox, robots-policy enforcement, authorization to scrape, prompt-injection isolation, or secret redaction. Read [Security](docs/SECURITY.md) before using it in sensitive networks.

Please report vulnerabilities privately as described in that manual rather than opening a public issue.

## Support

If this project helps you, you can support its development through [GitHub Sponsors](https://github.com/sponsors/romek-rozen) or [Patreon](https://www.patreon.com/RomanRozenberger). Funding links are also configured in [`.github/FUNDING.yml`](.github/FUNDING.yml).

## License

[MIT](LICENSE) © Roman Rozenberger
