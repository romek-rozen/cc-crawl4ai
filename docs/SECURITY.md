# Security and privacy

## Reporting a vulnerability

Please do not disclose exploitable vulnerabilities in a public issue. Use the repository's **Security → Report a vulnerability** option if GitHub presents it. If private vulnerability reporting is unavailable, contact the maintainer through the contact methods on [Roman Rozenberger's GitHub profile](https://github.com/romek-rozen) to establish a private channel before sending sensitive details.

Include the affected plugin/runner version, platform, reproduction, impact, and suggested mitigation. Remove real credentials, private page content, and customer data.

## Security boundary

`cc-crawl4ai` is local orchestration around pinned command-line tools. It adds validation and safer process handling, but it is **not a sandbox**.

It does not provide:

- an SSRF or network-egress boundary;
- DNS/IP allowlisting or redirect enforcement;
- robots.txt, terms-of-service, rate-limit, or authorization enforcement;
- prompt-injection detection/isolation;
- browser process sandbox guarantees beyond upstream behavior;
- secret detection/redaction;
- encrypted artifact storage;
- an anonymity service;
- an MCP security boundary.

Deploy host/container/firewall policy outside the plugin when those controls are required.

## Data flow

### Standard Crawl4AI

```text
requested URL → local Crawl4AI/browser → project artifact
```

The target and any redirects receive normal network/browser information governed by Crawl4AI configuration: source IP, headers, user agent, cookies/profile state if configured, and requested URLs. This plugin does not add telemetry.

### Trafilatura

```text
URL → Crawl4AI raw HTML → local Trafilatura stdin
                         ├→ extracted .md/.txt
                         └→ sibling .raw.html
```

Trafilatura processing is local. The raw HTML artifact is intentionally retained for debugging and can be more sensitive than extracted text.

### BM25

BM25 filtering is implemented in the runner with the Python standard library and is local. Query text and page chunks are not sent to a model by the filter itself.

### LLM question/extraction

Question mode and `--json-extract` delegate to Crawl4AI. Depending on its configured provider, page content, schema/instructions, and metadata may leave the machine and be subject to the provider's logging/retention policies. The plugin does not proxy or anonymize that transfer.

CSS/XPath extraction is local when the extraction configuration selects `json-css` or `json-xpath`. The runner forwards schema/config files to Crawl4AI and does not audit their content; review them before use. Pinned Crawl4AI also supports LLM extraction config files, which can contain provider settings and are not equivalent to deterministic local extraction.

## Local data and retention

Default project data includes:

```text
.crawl4ai/outputs/              final crawl/extraction artifacts
.crawl4ai/outputs/**/*.raw.html Trafilatura raw HTML
.crawl4ai/cache/                cache targeted by clear-cache
.crawl4ai/robots/               robots data targeted by clear-cache
.crawl4ai/runtime/              optional project runtime and state
```

Crawl4AI may create additional base-directory data according to its pinned implementation/configuration. Managed runtime roots include executable paths, installed versions, timestamps, and fingerprints in `.runtime-state.json`/`.browser-ready.json`.

The root `.gitignore` ignores directories named `.crawl4ai`, reducing accidental commits in this repository. It does not protect:

- explicit outputs outside `.crawl4ai`;
- copied/pasted content;
- shell history or process listings;
- backups, indexing, endpoint telemetry, or filesystem snapshots;
- artifacts in other repositories that use different ignore rules.

Apply least-privilege filesystem permissions, retention limits, encryption, and secure deletion appropriate to the data. `crawl4ai-clear-cache` deletes only `.crawl4ai/cache` and `.crawl4ai/robots`; it deliberately preserves outputs and runtimes.

## Untrusted web content and prompt injection

A crawled page is attacker-controlled input. It may contain instructions that try to make Claude reveal secrets, run commands, change files, follow links, or ignore the user's goal. Extraction to Markdown/text does not make those instructions trustworthy.

Recommended controls:

1. Treat artifacts as data, not authority.
2. Ask Claude to summarize/extract only the intended facts and ignore page instructions.
3. Review destination URLs and keep deep crawls narrowly bounded.
4. Do not grant unrelated tools or secrets to a crawling session.
5. Require human review before acting on crawled commands, code, links, or credentials.
6. Separate sensitive administrative work from browsing untrusted sites.

The plugin's agents are limited to Bash and Read, but those tools still have the permissions granted by the Claude Code session and host.

## Network risks and SSRF

The wrapper accepts any absolute HTTP(S) URL with a host. It does not reject:

- localhost or loopback;
- private/link-local network addresses;
- cloud metadata/services;
- internal DNS names;
- alternate ports;
- public URLs that redirect internally.

In a sensitive network, enforce egress and DNS policy at the container/VM/firewall/proxy layer. Do not rely on the initial URL string. Consider running crawling in an isolated, low-privilege environment with no access to internal services or credentials.

## Authentication and secrets

- Do not put tokens, passwords, cookies, signed URLs, or private data in skill prompts.
- Do not pass secrets in `--browser-config`, `--crawler-config`, `--question`, or extraction instructions. Command-line arguments may be visible to other local processes and logs.
- Subprocesses inherit the runner's environment. Launch Claude Code with only credentials the crawl actually needs.
- Provider credentials are managed by Crawl4AI/provider configuration, not this plugin. Follow upstream storage guidance and prefer environment/secret managers over checked-in config.
- Deterministic extraction schema/config files should not contain provider tokens.
- Review browser profiles/cookie use carefully. This wrapper does not expose upstream profile management directly, but advanced configuration can still affect browser state.

Never include secrets in bug reports or raw artifacts.

## Process-execution safeguards

The runner:

- validates URL scheme/host and incompatible modes before crawling;
- requires positive bounded page counts for deep crawl;
- launches subprocesses with argv arrays and `shell=False` behavior;
- quotes arguments in all bundled skill/agent examples;
- uses an explicit child working directory and absolute output destinations;
- spools output through temporary files;
- bounds reported diagnostics;
- enforces timeouts;
- creates a process group and terminates it on POSIX timeout/interruption;
- preserves an accurate distinction between package and browser readiness.

These controls reduce command-injection, runaway-output, and orphan-process risk. They do not validate the semantics of Crawl4AI's browser/crawler parameter strings or schema/config files. Those are trusted local configuration interpreted by pinned upstream code.

## Output path considerations

An explicit absolute `--output-file` can write anywhere the user can write. A relative path is normalized under the project, but the runner does not impose a sandbox or resolve policy against symlink traversal. Parent directories are created, and existing destinations are not overwritten; a suffixed file is selected instead.

Use only reviewed destinations. Avoid shared directories, repositories where content might be committed, and locations served automatically by a web server.

## Dependency and installation risk

Installation downloads and executes code from the configured Python package index and browser sources used by Crawl4AI setup. Exact top-level pins improve reproducibility but do not eliminate transitive dependency or supply-chain risk. Two isolated venvs reduce dependency conflicts; they are not security sandboxes.

For controlled environments:

- mirror/scan dependencies and browser assets;
- restrict package indexes and verify provenance according to organizational policy;
- test new pins in fresh environments;
- run with a low-privilege account;
- avoid installation in production projects;
- retain the exact plugin version and runtime-state metadata for incident analysis.

## Responsible crawling

Users are responsible for legal authority and compliance with site terms, copyright, privacy law, robots policies, and rate limits. Use conservative page caps and timeouts. Do not use the plugin to bypass authentication, access controls, anti-bot measures, or data-use restrictions.

## Security review checklist

Before a sensitive crawl:

- [ ] Target/redirect egress is externally restricted.
- [ ] URL and page cap are reviewed.
- [ ] Claude Code runs with least privilege and minimal environment secrets.
- [ ] No provider is used unless external data transfer is approved.
- [ ] Output path, retention, and access permissions are approved.
- [ ] Crawled content will be treated as untrusted/prompt-injectable.
- [ ] Runtime pins and browser verification status are known.
- [ ] The site and data use are authorized.
