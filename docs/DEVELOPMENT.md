# Development

## Repository layout

```text
.
├── .claude-plugin/marketplace.json       romek-plugins marketplace catalog
├── .github/FUNDING.yml
├── docs/                                 canonical public manuals
├── package.json                          private validation metadata/scripts
└── plugins/cc-crawl4ai/                  self-contained installable plugin
    ├── .claude-plugin/plugin.json         plugin manifest
    ├── agents/                            three specialized agent prompts
    ├── bin/crawl4ai                       standalone Python runner
    ├── requirements/                      exact runtime pins
    ├── skills/                            main and management skills
    └── tests/test_cli.py                  unittest suite
```

The marketplace source is the relative directory `./plugins/cc-crawl4ai`. Claude Code caches/installs that directory as the plugin, so installed plugin behavior must not depend on root `docs/`, root `package.json`, test fixtures, or other repository-only files. The plugin README links to canonical manuals on GitHub with absolute URLs for that reason.

There is no build step, npm-published package, MCP server, daemon, or generated client.

## Architecture

### Claude layer

- `skills/crawl4ai/SKILL.md` routes normal crawl/extraction requests and constrains valid combinations.
- Four management skills install, probe, smoke-test, or clear cache. Their frontmatter disables automatic model invocation.
- Three agents specialize in compact scraping, bounded deep crawling, and structured extraction. Their only tools are Bash and Read.
- Claude Code resolves `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, and `${CLAUDE_PROJECT_DIR}` at runtime.

### Runner layer

`bin/crawl4ai` uses only the Python standard library. Its responsibilities are:

1. parse and validate the wrapper contract;
2. locate/install pinned external tools;
3. allocate normalized output paths;
4. launch subprocesses with argv arrays and explicit working directories;
5. spool and bound diagnostics;
6. post-process optional Trafilatura, images/tables, and BM25 content;
7. track runtime/browser identity.

### Runtime layer

- Crawl4AI runs as its `crwl` executable in `.venv`.
- Trafilatura runs in `.trafilatura-venv` and receives raw HTML on stdin.
- Browser installation/verification is delegated to `crawl4ai-setup` from the pinned Crawl4AI environment.
- The local BM25 implementation uses no network, provider, or third-party Python module.

## Local setup

A runtime is not needed for unit tests:

```bash
git clone https://github.com/romek-rozen/cc-crawl4ai.git
cd cc-crawl4ai
python3 --version
npm test
```

`npm test` is an alias for:

```bash
python3 -m unittest discover -s plugins/cc-crawl4ai/tests -v
```

To create a project-local real runtime:

```bash
python3 plugins/cc-crawl4ai/bin/crawl4ai install \
  --scope project --project-root "$PWD"
python3 plugins/cc-crawl4ai/bin/crawl4ai status \
  --project-root "$PWD" --runtime-root "$PWD/.crawl4ai/runtime"
python3 plugins/cc-crawl4ai/bin/crawl4ai test \
  --project-root "$PWD" --runtime-root "$PWD/.crawl4ai/runtime"
```

These commands download code/browser assets and the smoke test accesses `example.com`. The root `.gitignore` excludes `.crawl4ai/`.

## Load the plugin locally

Use Claude Code's development flag from the repository root:

```bash
claude --plugin-dir ./plugins/cc-crawl4ai
```

Try each component by its namespace, inspect `/agents`, and reload after edits:

```text
/cc-crawl4ai:crawl4ai https://example.com
/cc-crawl4ai:crawl4ai-status
/reload-plugins
```

A local plugin with the same name takes precedence for that session over a marketplace installation. Local loading does not make root-only files available inside a marketplace-installed plugin, so keep all runtime requirements under `plugins/cc-crawl4ai/`.

## Validation

Required repository checks:

```bash
# Parse both manifests, then run unit tests
npm run validate

# Equivalent focused checks
npm run validate:json
npm test

# Claude Code plugin and marketplace validation
claude plugin validate plugins/cc-crawl4ai
claude plugin validate .
```

When Ruff is installed, also run:

```bash
ruff check plugins/cc-crawl4ai/bin/crawl4ai plugins/cc-crawl4ai/tests
```

The unittest suite covers mode validation, exact pins, safe argv handling, artifact allocation, cache preservation, runtime probes/fingerprints, partial browser setup, Trafilatura processing, BM25 filtering, and POSIX child-process-group timeout cleanup. Tests marked POSIX-specific are skipped on Windows.

Before changing docs, compare claims against:

```bash
python3 plugins/cc-crawl4ai/bin/crawl4ai --help
python3 plugins/cc-crawl4ai/bin/crawl4ai crawl --help
python3 plugins/cc-crawl4ai/bin/crawl4ai install --help
```

## Change guidelines

- Keep edits narrow and preserve the self-contained plugin boundary.
- Quote every value in skill/agent shell examples; never interpolate user input into executable shell fragments.
- Keep subprocess calls as argv lists with no `shell=True`.
- Validate incompatible combinations before runtime lookup/network access.
- Require an explicit positive page cap for all deep crawls.
- Do not print full pages into the model context; save artifacts and report paths.
- Do not weaken the distinction between package readiness and browser verification.
- Update tests whenever CLI behavior, runtime resolution, artifacts, or safety properties change.
- Do not add MCP or claim npm distribution without an explicit product decision and implementation.

## Dependency compatibility updates

The requirement files are exact pins by design. Update one dependency family at a time:

1. Change exactly one pin in `plugins/cc-crawl4ai/requirements/`.
2. Create fresh, separate Crawl4AI and Trafilatura environments; do not test only an in-place upgraded environment.
3. Run `status` and the real `test` pipeline.
4. Exercise at least:
   - regular Markdown;
   - complete `all` JSON;
   - bounded BFS/DFS/best-first behavior as applicable;
   - Trafilatura Markdown and text;
   - BM25 with and without Trafilatura;
   - LLM extraction if provider compatibility changed;
   - deterministic CSS/XPath extraction.
5. Confirm browser setup on supported hosts.
6. Run unit, Ruff, JSON, and both Claude validation commands.
7. Update version references and documentation only after compatibility is proven.

Trafilatura and Crawl4AI remain separate even if a particular version pair appears installable together; the isolation is an explicit compatibility boundary.

## Version synchronization

A release version currently appears in:

- `.claude-plugin/marketplace.json` (`plugins[].version`)
- `plugins/cc-crawl4ai/.claude-plugin/plugin.json`
- `plugins/cc-crawl4ai/bin/crawl4ai` (`VERSION`)
- root `package.json` (private repository metadata)
- compatibility comments in both requirement files
- documentation where the tested set is stated

Update all applicable locations together. The plugin name and marketplace name are stable public identifiers and must not be renamed as a routine version change.

## Release workflow

The repository currently has no checked-in CI/release workflow and no package publication step. Releases are marketplace source updates from GitHub:

1. Ensure the working tree contains only intended source/documentation changes.
2. Synchronize versions and exact compatibility comments.
3. Run all validation listed above plus the real runtime matrix for dependency changes.
4. Review `git diff --check`, documentation links, executable mode on `bin/crawl4ai`, and the relative marketplace source.
5. Commit the reviewed changes and create the maintainer's intended Git tag/GitHub release if one is being used.
6. Push only after review. Users then refresh `romek-plugins` and run `/plugin update cc-crawl4ai@romek-plugins`.
7. If runtime pins changed, release notes must tell users to rerun `/cc-crawl4ai:crawl4ai-install` and smoke-test.

Do not describe `npm publish`: `package.json` is explicitly `private: true`. Do not add generated files or local `.crawl4ai` artifacts to a release.

## Documentation maintenance

Root `README.md` is the public landing page and `docs/` is canonical. `plugins/cc-crawl4ai/README.md` should remain useful when someone inspects the installed plugin, but detailed duplicated contracts should link back to the canonical GitHub manuals. Verify relative links from repository Markdown and absolute plugin links before release.
