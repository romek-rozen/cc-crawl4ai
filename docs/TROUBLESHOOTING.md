# Troubleshooting

Start with the non-network status probe:

```text
/cc-crawl4ai:crawl4ai-status
```

Or from a checkout/runtime:

```bash
python3 plugins/cc-crawl4ai/bin/crawl4ai status \
  --project-root "$PWD" --runtime-root "$PWD/.crawl4ai/runtime"
echo "$?"
```

Interpret the three independent lines: Crawl4AI, Trafilatura, and Browser. A path existing on disk is not enough; status executes each tool.

## Plugin or skill is not visible

Symptoms:

- `/cc-crawl4ai:crawl4ai` is unknown.
- Namespaced agents do not appear.
- Marketplace updates are not reflected.

Actions:

```text
/plugin marketplace update romek-plugins
/plugin update cc-crawl4ai@romek-plugins
/reload-plugins
```

Confirm that the installed identifier is `cc-crawl4ai@romek-plugins`. If installation never completed:

```text
/plugin marketplace add romek-rozen/cc-crawl4ai
/plugin install cc-crawl4ai@romek-plugins
```

Marketplace installs are cached; editing a checkout does not edit an installed copy. For local development, start Claude Code with `claude --plugin-dir ./plugins/cc-crawl4ai`.

## `Crawl4AI is not installed`

Run:

```text
/cc-crawl4ai:crawl4ai-install
/cc-crawl4ai:crawl4ai-status
```

For a custom/manual runtime, remember that `--runtime-root` is the directory containing `.venv` and `.trafilatura-venv`, not either venv itself:

```bash
python3 plugins/cc-crawl4ai/bin/crawl4ai status \
  --project-root "$PWD" --runtime-root /path/to/runtime-root
```

Or configure both direct environments:

```bash
export CRAWL4AI_VENV=/path/to/crawl4ai-venv
export TRAFILATURA_VENV=/path/to/trafilatura-venv
```

`CRAWL4AI_VENV` has first priority. A stale value can mask a healthy managed runtime; unset it and `TRAFILATURA_VENV` when troubleshooting discovery.

## `Trafilatura is not installed`

The runner can use Crawl4AI without Trafilatura, but compact/text extraction cannot. Rerun the installer so it creates the separate `.trafilatura-venv`, or point `TRAFILATURA_VENV` at a venv containing the `trafilatura` executable.

Do not install Trafilatura into the Crawl4AI environment as a workaround; separate environments are intentional.

## Status says an executable is `broken`

Status found a path but its bounded `--help`/`--version` probe exited nonzero or failed. Reinstall the selected runtime, checking which path status printed. Common causes are:

- venv moved after creation;
- interpreter removed/upgraded in place;
- incomplete pip install;
- stale `CRAWL4AI_VENV`, `CRAWL4AI_RUNTIME`, or `CLAUDE_PLUGIN_DATA`;
- platform loader or shared-library failure.

Use the exact printed executable for diagnosis:

```bash
/path/to/runtime/.venv/bin/crwl --help
/path/to/runtime/.trafilatura-venv/bin/trafilatura --version
```

On Windows, executables live under `Scripts` rather than `bin`.

## Browser is `unverified`

Exit code `2` from install/status means both Python tools can be usable while browser readiness is not established. This occurs after:

- `--skip-browser`;
- missing `crawl4ai-setup`;
- browser setup returning nonzero;
- a runtime upgrade/changed executable identity;
- a stale, invalid, or absent `.browser-ready.json`;
- status finding only tools on `PATH`, with no managed root to hold verification.

Rerun installation without `--skip-browser`, then smoke-test:

```text
/cc-crawl4ai:crawl4ai-install
/cc-crawl4ai:crawl4ai-test
```

Some Linux hosts need system packages that Python/pip cannot supply. Follow the setup guidance for pinned Crawl4AI `0.9.2` and the host distribution. Do not manually create `.browser-ready.json`; it is fingerprinted to executable paths and package versions.

## Browser setup times out

The default setup timeout is 1,800 seconds. From the direct CLI, increase it:

```bash
python3 plugins/cc-crawl4ai/bin/crawl4ai install \
  --scope project --project-root "$PWD" --browser-timeout 3600
```

A thrown timeout exits `1`; a completed setup command that reports failure leaves packages installed but returns `2`. In either case, old verification was invalidated before installation began.

## Smoke test fails

The test requires:

- both executables;
- browser readiness sufficient to crawl `https://example.com`;
- DNS/TLS/outbound HTTPS;
- Crawl4AI JSON containing non-empty `html`;
- Trafilatura returning non-empty Markdown.

Retry with a larger per-process timeout:

```bash
python3 plugins/cc-crawl4ai/bin/crawl4ai test \
  --project-root "$PWD" --runtime-root /path/to/runtime --timeout 180
```

A successful package probe does not prove browser/network functionality; that is why status and test are separate.

## Crawl times out

The default crawl timeout is 60 seconds. Increase it and reduce work:

```bash
--timeout 180
--max-pages 5
```

Prefer a single-page Trafilatura scrape when a deep crawl is unnecessary. On POSIX, timeout and interruption terminate the child process group; on Windows, the runner terminates the direct process. Timeout errors exit `1`.

## URL or mode validation fails

Validation happens before network access. Frequent fixes:

- Include `https://` or `http://` and a host.
- Add an explicit positive `--max-pages` to every deep crawl.
- Use `--extractor trafilatura` for `--output-format text`.
- Use only Markdown/text with BM25.
- Do not combine deep crawl with Trafilatura, BM25, question, or extraction.
- Supply both `--schema-path` and `--extraction-config`.
- Supply exactly one JSON extraction strategy.
- Do not request `--output-format json` without extraction.

Argparse syntax errors and install/status partial readiness can both use exit code `2`; syntax errors print usage, whereas partial readiness prints explicit browser status.

## Advanced crawler parameters fail

The wrapper options:

```text
--browser-config
--crawler-config
```

accept comma-separated direct Crawl4AI parameters, not YAML/JSON file paths. For example:

```bash
--browser-config "headless=true,viewport_width=1280"
--crawler-config "delay_before_return_html=2,cache_mode=enabled"
```

They are interpreted by Crawl4AI `0.9.2`. Parameters copied from newer Crawl4AI documentation may not exist in the pinned version.

## LLM question or extraction fails

`--question` and `--json-extract` delegate provider use to Crawl4AI. Configure a provider/token supported by Crawl4AI `0.9.2` and verify its model/network access. The plugin does not provide a model credential or MCP proxy.

To avoid provider requirements, use:

- normal Markdown/`all` crawling;
- Trafilatura;
- local BM25;
- CSS/XPath schema extraction.

Never paste provider credentials into a skill prompt or shell argument. See [Security](SECURITY.md).

## CSS/XPath extraction fails

Check both paths are supplied and point to readable files. The config must have a supported pinned-CLI type:

```yaml
type: json-css
```

or:

```yaml
type: json-xpath
```

The schema selector syntax must match the type and actual page DOM. Dynamic pages may require valid browser/crawler parameters to wait for content. Validate the resulting JSON; a successful command does not guarantee selectors found all desired records.

## Trafilatura returns no content

When raw HTML exists but Trafilatura extracts nothing, the runner exits `1` and reports the saved sibling raw HTML. Inspect it only for debugging:

- the page may be a login/challenge/error shell;
- content may require additional wait/interaction configuration;
- the article may not contain extractable main text;
- access may have been blocked.

Raw HTML can contain sensitive values and untrusted scripts/text. Do not paste it wholesale into the conversation.

## Artifact is missing, empty, or not where expected

Default output is relative to the resolved project, not necessarily the shell's apparent repository:

```text
<project>/.crawl4ai/outputs/<domain>/<format>/...
```

Check the command's printed absolute path. `--project-root` overrides `CLAUDE_PROJECT_DIR`; an explicit relative `--output-file` resolves under that project. Existing paths receive a hash/counter suffix rather than being overwritten.

Possible empty BM25 output is not a crawl failure: it means no chunk met the threshold. Lower `--bm25-threshold` or broaden the query.

For a regular crawl, zero-size output is an error. Check available disk space, directory permissions, and bounded upstream diagnostics.

## Cache clearing did not remove everything

`clear-cache` intentionally removes only:

```text
<project>/.crawl4ai/cache
<project>/.crawl4ai/robots
```

It does not remove outputs, runtime environments, Crawl4AI-managed data outside those exact directories, or custom output paths. This narrow behavior prevents accidental loss. Remove other data manually only after identifying it and confirming backups/retention obligations.

## Installation leaves `global.yml` concerns

The installer runs `crawl4ai-setup` with the selected runtime root as both working directory and default `CRAWL4_AI_BASE_DIRECTORY`, specifically to avoid leaving Crawl4AI setup state in the consumer project. Regular crawl subprocesses use the project as their default base unless `CRAWL4_AI_BASE_DIRECTORY` is already set.

## Gather a useful issue report

Before opening a non-security issue, include:

- plugin version and Claude Code version;
- OS and Python version;
- the exact wrapper command with secrets removed;
- `status` output and exit code;
- error text (diagnostics are already bounded);
- whether the runtime is plugin-data, project, custom, direct venv, or `PATH`;
- whether the failure reproduces with `example.com`.

Do not attach raw HTML, cookies, provider tokens, private URLs, or sensitive artifacts. Report vulnerabilities privately as described in [Security](SECURITY.md).
