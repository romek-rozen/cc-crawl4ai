# Installation

This manual covers the Claude Code marketplace lifecycle and the separate Python/browser runtime lifecycle. Installing the plugin does not install Crawl4AI, Trafilatura, or a browser. Uninstall behavior depends on runtime location and whether Claude Code is told to preserve the plugin's persistent data.

## Prerequisites

1. Claude Code with plugin and marketplace support.
2. Python 3.10+ with `python -m venv` available.
3. Network access to GitHub, the configured Python package index, browser downloads, and target sites.
4. Approximately **2 GB of free disk space** for two virtual environments, package caches, and browser binaries.
5. Any OS packages required by Crawl4AI/Playwright on the host.

## Expected installation time and downloads

Plan for roughly **5–15 minutes** on a typical machine. The exact duration depends on internet speed, proximity and performance of the Python package index, existing pip/Playwright caches, CPU and disk speed, and whether compatible browser binaries are already present.

The first installation may download **more than 500 MB**. Crawl4AI has a substantial Python dependency tree, and Playwright may install Chromium, a headless shell, and FFmpeg. Slow connections can therefore take longer than 15 minutes. Do not interrupt the process merely because a large package or browser archive spends several minutes downloading.

The installer prints live stages such as:

```text
[crawl4ai] [1/7] Creating the isolated Crawl4AI environment (elapsed: 0s)
[crawl4ai] [3/7] Installing pinned Crawl4AI dependencies; this is usually the longest package step (elapsed: 4s)
[crawl4ai] [7/7] Installing and verifying browser dependencies; Chromium downloads can take several minutes (elapsed: 95s)
```

Package manager and browser download output is also streamed to the terminal. At completion, the installer reports total elapsed time and whether browser setup was verified.

The plugin installs exactly:

- `crawl4ai==0.9.2`
- `trafilatura==2.2.0`

They use separate virtual environments because their transitive dependencies, notably `lxml`, can conflict. Do not combine the environments.

## Install from the marketplace

Run inside an interactive Claude Code session:

```text
/plugin marketplace add romek-rozen/cc-crawl4ai
/plugin install cc-crawl4ai@romek-plugins
```

The repository's marketplace identifier is `romek-plugins`; the plugin identifier is `cc-crawl4ai`. Both commands default to Claude Code's `user` settings scope. Claude Code also supports `project` (shared project settings) and `local` (personal settings for this project):

```text
/plugin marketplace add romek-rozen/cc-crawl4ai --scope project
/plugin install cc-crawl4ai@romek-plugins --scope project
```

Use the same marketplace/plugin settings scope throughout update and removal. These Claude Code scopes control where the marketplace/plugin is declared; they are not the runner runtime scopes described below.

If Claude Code asks, run:

```text
/reload-plugins
```

Then ask the install skill to download the runtime:

```text
/cc-crawl4ai:crawl4ai-install
```

The skill requests confirmation before downloads and normally runs:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/crawl4ai" install \
  --scope custom \
  --directory "${CLAUDE_PLUGIN_DATA}" \
  --project-root "${CLAUDE_PROJECT_DIR}"
```

This is intentionally the persistent plugin data directory, not the versioned plugin cache.

## Runtime scopes

The CLI has three install scopes. They are separate from Claude Code's marketplace/settings scopes.

| CLI scope | Selected root | When to use it |
| --- | --- | --- |
| `user` (default) | `${CLAUDE_PLUGIN_DATA}` when set, otherwise `~/.claude/crawl4ai` | Shared fallback for direct CLI use. |
| `project` | `<project>/.crawl4ai/runtime` | Runtime isolated to one project. |
| `custom` | Absolute/expanded `--directory` | Plugin data or an administrator-selected location. |

Examples from a repository checkout:

```bash
# Project runtime
python3 plugins/cc-crawl4ai/bin/crawl4ai install \
  --scope project --project-root "$PWD"

# Explicit runtime
python3 plugins/cc-crawl4ai/bin/crawl4ai install \
  --scope custom --directory "$HOME/.local/share/cc-crawl4ai" \
  --project-root "$PWD"

# Select another Python interpreter
python3 plugins/cc-crawl4ai/bin/crawl4ai install \
  --scope project --project-root "$PWD" --python /usr/bin/python3.11
```

`custom` without `--directory` is an error. The CLI expands `~` and resolves the destination. An install creates or updates:

```text
<runtime-root>/
├── .venv/                    Crawl4AI environment
├── .trafilatura-venv/        Trafilatura environment
├── .runtime-state.json       paths, versions, pin hashes, timestamp, fingerprint
└── .browser-ready.json       verification time and matching runtime fingerprint
```

An attempted install removes old state/verification markers first. Therefore a failed, interrupted, skipped, or partial upgrade cannot leave a stale “verified” marker.

## Browser setup

After probing `crwl --help` and `trafilatura --version`, the installer runs the managed environment's `crawl4ai-setup` from the runtime root. The default browser timeout is 1,800 seconds:

```bash
python3 plugins/cc-crawl4ai/bin/crawl4ai install \
  --scope project --project-root "$PWD" --browser-timeout 3600
```

To install Python packages without attempting browser setup:

```bash
python3 plugins/cc-crawl4ai/bin/crawl4ai install \
  --scope project --project-root "$PWD" --skip-browser
```

This returns exit code `2`, not success `0`, because package readiness and browser readiness are deliberately distinct. It does not prove that a browser crawl can run.

## Verify the runtime

Inside Claude Code:

```text
/cc-crawl4ai:crawl4ai-status
/cc-crawl4ai:crawl4ai-test
```

Or from a checkout:

```bash
python3 plugins/cc-crawl4ai/bin/crawl4ai status \
  --project-root "$PWD" --runtime-root "$PWD/.crawl4ai/runtime"

python3 plugins/cc-crawl4ai/bin/crawl4ai test \
  --project-root "$PWD" --runtime-root "$PWD/.crawl4ai/runtime" --timeout 60
```

`status` executes bounded health probes rather than trusting file existence. `test` accesses `https://example.com`, requires both tools, passes Crawl4AI's returned HTML to Trafilatura, and records current runtime/browser identity after success.

## Runtime discovery precedence

For crawl/status/test, `CRAWL4AI_VENV` has special first priority. If it contains a working `crwl`, the plugin uses it and uses `TRAFILATURA_VENV` only when that environment contains Trafilatura. Otherwise managed runtime roots are searched in this order:

1. `--runtime-root`
2. `CRAWL4AI_RUNTIME`
3. `CLAUDE_PLUGIN_DATA`
4. `<project>/.crawl4ai/runtime`
5. `~/.claude/crawl4ai`
6. executables named `crwl` and `trafilatura` on `PATH`

A managed root contains `.venv` and `.trafilatura-venv`; `--runtime-root` names their parent, not either virtual environment itself.

Manual environment example:

```bash
export CRAWL4AI_VENV="$HOME/venvs/crawl4ai"
export TRAFILATURA_VENV="$HOME/venvs/trafilatura"
python3 plugins/cc-crawl4ai/bin/crawl4ai status --project-root "$PWD"
```

## Update

Refresh the marketplace catalog, then update the installed plugin:

```text
/plugin marketplace update romek-plugins
/plugin update cc-crawl4ai@romek-plugins
/reload-plugins
```

Claude Code may refresh marketplaces automatically, but these commands force the check. If the plugin was installed at `project` or `local` scope, pass that same `--scope` to `/plugin update`. The runtime under `${CLAUDE_PLUGIN_DATA}` survives a plugin update. Run the install skill again whenever the plugin's pinned requirements change; it upgrades the two environments and re-verifies the browser.

```text
/cc-crawl4ai:crawl4ai-install
/cc-crawl4ai:crawl4ai-status
/cc-crawl4ai:crawl4ai-test
```

## Uninstall

First record the runtime path with the status skill if you may need it again. Then remove the plugin at the same Claude Code settings scope where it was installed (default: `user`):

```text
/plugin uninstall cc-crawl4ai@romek-plugins
```

Current Claude Code removes the plugin's persistent data directory by default. Because the recommended runtime lives in `${CLAUDE_PLUGIN_DATA}`, default uninstall can remove that runtime. Preserve it for later reinstall with the supported terminal command:

```bash
claude plugin uninstall cc-crawl4ai@romek-plugins --scope user --keep-data
```

Use `--scope project` or `--scope local` when applicable. Project-scoped runner roots (`<project>/.crawl4ai/runtime`), custom roots outside `${CLAUDE_PLUGIN_DATA}`, `~/.claude/crawl4ai`, project outputs, and explicit external artifacts are outside plugin uninstallation and remain until manually removed.

If no other plugin from this marketplace is needed, optionally remove its registration. Omitting `--scope` removes the declaration from every editable Claude Code scope; supply a scope to remove only that declaration:

```text
/plugin marketplace remove romek-plugins
```

After uninstalling, remove only retained roots you intentionally created:

```bash
# Examples — destructive; choose only the applicable path
rm -rf -- "$PROJECT/.crawl4ai/runtime"
rm -rf -- "$HOME/.claude/crawl4ai"
rm -rf -- "/the/custom/runtime-root"
```

Project artifacts remain under `<project>/.crawl4ai/outputs`. Claude Code owns `${CLAUDE_PLUGIN_DATA}`; inspect it before deletion and use `--keep-data` if it must survive plugin uninstall.

## Exit codes during installation

| Code | Meaning |
| --- | --- |
| `0` | Both Python tools installed/probed and browser setup verified. |
| `1` | Installation or probe failed, required setup was broken, or arguments/path were invalid. |
| `2` | Python tools are usable but browser readiness is unverified (`--skip-browser`, missing setup executable, or setup failure). |
| `130` | Interrupted after the runner handled Ctrl+C/termination and stopped the active child. |

Argparse usage errors also use `2`; distinguish them from the install command's documented partial state by the usage/error text.

## Compatibility and platform notes

- Requirements comments and tests bind plugin `0.1.1` to Crawl4AI `0.9.2` and Trafilatura `2.2.0`.
- The repository does not publish an npm package. Node/npm are needed only for repository convenience scripts.
- Browser availability depends on upstream Crawl4AI setup and host OS packages. A Python-only installation is not browser-ready.
- POSIX systems receive process-group termination on timeout/interruption. Windows uses direct process termination; POSIX-specific tests are skipped there.
- No minimum Claude Code version is enforced in the manifest. Use a current release that supports plugins, marketplaces, namespaced skills/agents, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PROJECT_DIR}`, and `${CLAUDE_PLUGIN_DATA}`.
- LLM extraction/provider compatibility is owned by pinned Crawl4AI and the provider configuration, not by this plugin.

See [Troubleshooting](TROUBLESHOOTING.md) if a probe or browser setup is not ready.
