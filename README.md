# cc-crawl4ai

A native, non-MCP Claude Code plugin for crawling websites with [Crawl4AI](https://github.com/unclecode/crawl4ai) and extracting compact content with [Trafilatura](https://trafilatura.readthedocs.io/).

## Install in Claude Code

```text
/plugin marketplace add romek-rozen/cc-crawl4ai
/plugin install cc-crawl4ai@romek-plugins
```

Run `/reload-plugins` if Claude Code requests it. Then install the Python/browser runtime:

```text
/cc-crawl4ai:crawl4ai-install
```

See [`plugins/cc-crawl4ai/README.md`](plugins/cc-crawl4ai/README.md) for usage, architecture, security, and troubleshooting.

## Development

```bash
python3 -m unittest discover -s plugins/cc-crawl4ai/tests -v
claude plugin validate plugins/cc-crawl4ai
claude plugin validate .
```

The repository is both the `romek-plugins` marketplace and the source of `cc-crawl4ai`. The marketplace uses the relative source `./plugins/cc-crawl4ai`, so every file needed after installation is contained in that directory.

## License

MIT © Roman Rozenberger
