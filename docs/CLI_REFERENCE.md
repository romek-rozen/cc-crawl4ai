# CLI reference

The bundled executable is `plugins/cc-crawl4ai/bin/crawl4ai`. It is a Python entry point used by the plugin's skills and agents; it is not the upstream `crwl` CLI.

```text
crawl4ai [--version] {crawl,install,status,test,clear-cache} ...
```

From a loaded plugin:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" --version
```

From a checkout:

```bash
python3 plugins/cc-crawl4ai/bin/crawl4ai --help
```

Current runner version: `0.1.2`.

## Common path resolution

`--project-root` resolves to, in order:

1. the explicit argument;
2. `CLAUDE_PROJECT_DIR`;
3. the current working directory.

A crawl requires the resolved project to be an existing directory. Child processes run with that project as their working directory, except `crawl4ai-setup`, which runs from the selected runtime root.

Runtime lookup for crawl/status/test:

1. `CRAWL4AI_VENV` (and optional `TRAFILATURA_VENV`);
2. `--runtime-root`;
3. `CRAWL4AI_RUNTIME`;
4. `CLAUDE_PLUGIN_DATA`;
5. `<project>/.crawl4ai/runtime`;
6. `~/.claude/crawl4ai`;
7. `crwl`/`trafilatura` on `PATH`.

Managed roots contain `.venv/` and `.trafilatura-venv/`. Duplicate candidate roots are removed after expansion/resolution.

## `crawl`

```text
crawl4ai crawl URL [options]
```

`URL` must be an absolute `http://` or `https://` URL with a host.

### General crawl options

| Option | Default | Meaning |
| --- | --- | --- |
| `--output-format FORMAT` | `markdown` | `markdown`, `markdown-fit`, `md`, `md-fit`, `json`, `all`, or `text`. Aliases are forwarded upstream. |
| `--output-file PATH` | generated path | Absolute destination, or a path resolved under the project. Existing paths are not overwritten. |
| `--timeout SECONDS` | `60` | Timeout for each crawl/extraction subprocess; integer from 1 through 86,400. |
| `--project-root PATH` | env/current directory | Project/cwd and base for relative artifacts. |
| `--runtime-root PATH` | runtime search | Parent containing managed virtual environments. |
| `--bypass-cache` | false | Pass upstream cache bypass instead of injecting enabled cache mode. |
| `--browser-config STRING` | none | Upstream direct browser parameters (`crwl -b`), normally comma-separated `key=value` pairs. |
| `--crawler-config STRING` | none | Upstream direct crawler parameters (`crwl -c`). `cache_mode=enabled` is appended unless already present. |

The wrapper option names are historical: `--browser-config` and `--crawler-config` accept direct parameter strings, not Crawl4AI `-B`/`-C` config-file paths. In the current implementation, selecting `--bypass-cache` forwards only the upstream bypass flag on the crawler-config branch; a supplied `--crawler-config` is not forwarded in that combination.

### Trafilatura options

| Option | Default | Meaning |
| --- | --- | --- |
| `--extractor trafilatura` | none | Crawl one page as complete JSON, then extract its raw HTML. |
| `--include-links` | false | Pass Trafilatura `--links`; Markdown only. |
| `--include-formatting` | automatic | Explicitly retain formatting. Markdown already retains it when neither boolean form is given. |
| `--no-include-formatting` | false | Disable automatic Markdown formatting. |
| `--include-images` | false | Ask Trafilatura for images and append missing Crawl4AI image references. |
| `--no-tables` | false | Pass `--no-tables` and skip restoration from Crawl4AI Markdown. |

Trafilatura formats: `markdown`, alias `md`, or `text`. `text` rejects links and positive formatting. It saves extracted output plus sibling `.raw.html`.

### BM25 options

| Option | Default | Meaning |
| --- | --- | --- |
| `--bm25-query QUERY` | none | Enable local post-crawl structural-chunk filtering; blank queries are invalid. |
| `--bm25-threshold FLOAT` | `1.0` | Minimum score; must be non-negative. |

BM25 accepts Markdown/aliases/fitted Markdown or Trafilatura text. It reports `retained/total` chunk counts.

### Deep-crawl options

| Option | Default | Meaning |
| --- | --- | --- |
| `--deep-crawl STRATEGY` | none | `bfs`, `dfs`, or `best-first`. |
| `--max-pages INTEGER` | none | Required positive bound whenever deep crawling is selected. |

Deep crawling accepts Markdown, fitted Markdown, or `all` only. The runner requests structured upstream `all` JSON for every deep crawl, deduplicates page records by Crawl4AI 0.9.2 normalized URL (fragments removed; trailing slashes preserved), and serializes the requested format. `--max-pages` caps records returned by upstream before deduplication, so the saved unique count can be lower when the upstream batch contains duplicates. The runner reports that count truthfully and does not crawl extra pages to fill the cap.

### Question and extraction options

| Option | Default | Meaning |
| --- | --- | --- |
| `--question TEXT` | none | Forward a single-page natural-language question as upstream `-q`. |
| `--json-extract TEXT` | none | Forward LLM structured-extraction instructions as upstream `-j`. |
| `--schema-path PATH` | none | Extraction schema forwarded as upstream `-s`. |
| `--extraction-config PATH` | none | Strategy configuration forwarded as upstream `-e`. |

`--schema-path` and `--extraction-config` must appear together. LLM extraction and schema/config extraction are mutually exclusive. `--output-format json` requires exactly one of those complete strategies.

### Mode compatibility

| Combination | Accepted? |
| --- | --- |
| Trafilatura + BM25 | Yes, single-page Markdown/text. |
| Regular Markdown + BM25 | Yes. |
| Trafilatura + deep/question/JSON extraction | No. |
| BM25 + deep/question/JSON extraction | No. |
| Deep + question/JSON extraction | No. |
| Question + structured extraction | No. |
| `json` without extraction | No. |
| `text` without Trafilatura | No. |
| Trafilatura flags without Trafilatura | No. |
| Deep crawl without positive `--max-pages` | No. |

All wrapper compatibility checks run before runtime resolution or network access.

### Generated artifact names

Unless `--output-file` is provided:

```text
<project>/.crawl4ai/outputs/<normalized-domain>/<folder>/
  <YYYY-MM-DD-HH-MM-SS>-<url-path-and-query-slug>.<extension>
```

| Mode/format | Folder | Extension |
| --- | --- | --- |
| Trafilatura | `trafilatura` | `.md` or `.txt` |
| `markdown` / `md` | `markdown` | `.md` |
| `markdown-fit` / `md-fit` | `markdown-fit` | `.md` |
| `json` | `json` | `.json` |
| `all` | `all` | `.json` |

Trafilatura raw HTML uses `<output-stem>.raw.html`. If the selected output already exists, the runner adds a short deterministic hash and, if necessary, a counter. An explicit output file keeps its supplied extension.

## `install`

```text
crawl4ai install [options]
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--scope {user,project,custom}` | `user` | Select runtime root policy. |
| `--directory PATH` | none | Required and used only for `custom`. |
| `--project-root PATH` | env/current directory | Existing project used as installation working directory. |
| `--python EXECUTABLE` | current interpreter | Interpreter used to create both venvs. |
| `--skip-browser` | false | Skip `crawl4ai-setup` and return partial status `2`. |
| `--browser-timeout SECONDS` | `1800` | Timeout for `crawl4ai-setup`. |

Root selection:

- `project`: `<project>/.crawl4ai/runtime`
- `custom`: expanded/resolved `--directory`
- `user`: `${CLAUDE_PLUGIN_DATA}` when present, otherwise `~/.claude/crawl4ai`

The installer creates/upgrades pip, installs exact requirement files into separate venvs, probes both executables, records runtime state, then runs browser setup unless skipped. It is also the update mechanism for a managed runtime.

## `status`

```text
crawl4ai status [--project-root PATH] [--runtime-root PATH]
```

Prints runner version, probed executable status/path, browser verification, and project. Probes use `crwl --help` and `trafilatura --version`, each bounded to 10 seconds. Browser verification is accepted only when `.browser-ready.json` matches the current executable paths and installed package versions by fingerprint.

## `test`

```text
crawl4ai test [--project-root PATH] [--runtime-root PATH] [--timeout SECONDS]
```

Default timeout: `60` seconds per subprocess. Requires both tools and accesses `https://example.com`. It runs Crawl4AI with complete JSON and enabled cache, checks for non-empty HTML, pipes that HTML to Trafilatura Markdown, and prints up to the first 500 extracted characters. For a detected managed root, success writes runtime state and browser verification.

## `clear-cache`

```text
crawl4ai clear-cache [--project-root PATH] [--runtime-root PATH]
```

Recursively removes only:

```text
<project>/.crawl4ai/cache
<project>/.crawl4ai/robots
```

`--runtime-root` is accepted by the shared management parser but is not used by this command. Outputs and project runtimes are preserved.

## Environment variables

| Variable | Use |
| --- | --- |
| `CLAUDE_PROJECT_DIR` | Default project root supplied by Claude Code. |
| `CLAUDE_PLUGIN_ROOT` | Used by skill commands to locate this executable; the CLI itself derives its own plugin root from its file path. |
| `CLAUDE_PLUGIN_DATA` | Preferred persistent managed runtime root. |
| `CRAWL4AI_RUNTIME` | Additional managed runtime root override. |
| `CRAWL4AI_VENV` | Direct Crawl4AI virtual environment override with first priority. |
| `TRAFILATURA_VENV` | Direct Trafilatura venv paired with `CRAWL4AI_VENV`. |
| `CRAWL4_AI_BASE_DIRECTORY` | Preserved if already set; otherwise subprocesses receive the project (or setup runtime) as base. |

Subprocesses also receive a venv-adjusted `PATH`/`VIRTUAL_ENV` and UTF-8/unbuffered Python settings.

## Exit codes

| Code | Commands | Meaning |
| --- | --- | --- |
| `0` | all | Requested operation completed; for install/status this includes current browser verification. |
| `1` | all | Runner validation, missing/broken tool, subprocess, filesystem, JSON, or crawl/extraction error. `status` uses it when either Python tool is missing/broken. |
| `2` | `install`, `status`, parser | Install has usable Python packages but unverified browser; status has both tools ready but unverified browser; argparse also uses 2 for malformed CLI syntax. |
| `130` | runtime operations | Interrupt handled and active child terminated. |

An upstream child exit is converted to runner exit `1`; its bounded diagnostics include the original child code. Timeout errors also become `1`. Diagnostics are limited to 64 KiB (and part of crawl stdout to 4 KiB on failures).

## Process behavior

- Programs are launched as argv arrays with no shell.
- Crawl output is spooled through temporary files rather than accumulated in unbounded memory.
- On POSIX, each child starts a new process group and timeout/interruption terminates that group; after five seconds a timed-out group is killed.
- On Windows, the direct child is terminated/killed.
- Output paths are made absolute and parent directories are created before crawling.
