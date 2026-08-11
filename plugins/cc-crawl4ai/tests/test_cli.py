from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

CLI = Path(__file__).parents[1] / "bin" / "crawl4ai"
loader = importlib.machinery.SourceFileLoader("crawl4ai_cli", str(CLI))
spec = importlib.util.spec_from_loader(loader.name, loader)
assert spec is not None
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)


class CliTests(unittest.TestCase):
    def parse(self, *args: str) -> argparse.Namespace:
        return module.build_parser().parse_args(list(args))

    def test_bm25_selects_relevant_structural_chunk(self) -> None:
        content = "# Intro\n\nGeneral words only.\n\n# Pricing\n\nEnterprise price is 99 dollars."
        filtered, matched, total = module.filter_bm25(content, "enterprise price", 0.1)
        self.assertEqual(total, 2)
        self.assertEqual(matched, 1)
        self.assertIn("Enterprise price", filtered)
        self.assertNotIn("General words", filtered)

    def test_image_references_resolve_relative_urls_and_deduplicate(self) -> None:
        content = module.append_image_references(
            "Body",
            [{"src": "/img/a.png", "alt": "Diagram"}, {"src": "/img/a.png"}],
            "https://example.com/docs/page",
            "markdown",
        )
        self.assertEqual(content.count("https://example.com/img/a.png"), 1)
        self.assertIn("![Diagram]", content)

    def test_missing_markdown_table_is_restored(self) -> None:
        crawl_markdown = "| Name | Price |\n| --- | --- |\n| A | 10 |"
        restored = module.append_markdown_tables(
            "Product list", crawl_markdown, "markdown"
        )
        self.assertIn("| Name | Price |", restored)
        self.assertIn("| A | 10 |", restored)

    def test_artifact_path_is_project_absolute_and_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp).resolve()
            path = module._artifact_path(
                project, "https://www.Example.com/a/b?q=x", "markdown", None
            )
            self.assertTrue(path.is_absolute())
            self.assertTrue(
                str(path).startswith(
                    str(project / ".crawl4ai" / "outputs" / "example.com")
                )
            )
            self.assertEqual(path.suffix, ".md")

    def test_all_artifacts_use_json_for_regular_and_deep_crawl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp).resolve()
            regular = module._artifact_path(project, "https://example.com", "all", None)
            args = self.parse(
                "crawl",
                "https://example.com",
                "--output-format",
                "all",
                "--deep-crawl",
                "bfs",
                "--max-pages",
                "2",
            )
            module._validate_crawl(args)
            deep = module._artifact_path(project, args.url, args.output_format, None)
            self.assertEqual(regular.suffix, ".json")
            self.assertEqual(deep.suffix, ".json")

    def test_build_args_keeps_values_as_individual_argv_items(self) -> None:
        args = self.parse(
            "crawl",
            "https://example.com",
            "--question",
            "x; echo unsafe",
            "--timeout",
            "5",
        )
        values = module._build_crwl_args(args, None)
        self.assertIn("x; echo unsafe", values)
        self.assertNotIn("echo", values)
        self.assertEqual(values[-1], "https://example.com")

    def test_validation_rejects_unbounded_deep_crawl(self) -> None:
        args = self.parse("crawl", "https://example.com", "--deep-crawl", "bfs")
        with self.assertRaises(module.CliError):
            module._validate_crawl(args)

    def test_validation_rejects_json_without_extractor(self) -> None:
        args = self.parse("crawl", "https://example.com", "--output-format", "json")
        with self.assertRaises(module.CliError):
            module._validate_crawl(args)

    def test_validation_rejects_text_without_trafilatura(self) -> None:
        args = self.parse("crawl", "https://example.com", "--output-format", "text")
        with self.assertRaises(module.CliError):
            module._validate_crawl(args)

    def test_validation_rejects_two_json_strategies(self) -> None:
        args = self.parse(
            "crawl",
            "https://example.com",
            "--output-format",
            "json",
            "--json-extract",
            "products",
            "--schema-path",
            "/tmp/schema.json",
            "--extraction-config",
            "/tmp/config.yaml",
        )
        with self.assertRaises(module.CliError):
            module._validate_crawl(args)

    def test_validation_rejects_trafilatura_deep_crawl(self) -> None:
        args = self.parse(
            "crawl",
            "https://example.com",
            "--extractor",
            "trafilatura",
            "--deep-crawl",
            "bfs",
            "--max-pages",
            "2",
        )
        with self.assertRaises(module.CliError):
            module._validate_crawl(args)

    def test_subprocess_runner_does_not_use_shell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = "hello; touch SHOULD_NOT_EXIST"
            code, out, err = module._run(
                [sys.executable, "-c", "import sys; print(sys.argv[1])", payload],
                cwd=Path(tmp),
                timeout=5,
            )
            self.assertEqual((code, err), (0, b""))
            self.assertEqual(out.decode().strip(), payload)
            self.assertFalse((Path(tmp) / "SHOULD_NOT_EXIST").exists())

    @unittest.skipIf(os.name == "nt", "fake POSIX executable")
    def test_cli_crawl_uses_managed_runtime_and_absolute_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project, runtime = base / "project", base / "runtime"
            project.mkdir()
            binary = runtime / ".venv" / "bin" / "crwl"
            binary.parent.mkdir(parents=True)
            binary.write_text(
                "#!/usr/bin/env python3\n"
                "import pathlib, sys\n"
                "args=sys.argv[1:]\n"
                "target=pathlib.Path(args[args.index('-O')+1])\n"
                "target.write_text('# crawled', encoding='utf-8')\n",
                encoding="utf-8",
            )
            binary.chmod(0o755)
            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "crawl",
                    "https://example.com",
                    "--project-root",
                    str(project),
                    "--runtime-root",
                    str(runtime),
                    "--output-file",
                    "artifacts/page.md",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = project / "artifacts" / "page.md"
            self.assertEqual(expected.read_text(encoding="utf-8"), "# crawled")
            self.assertIn(str(expected), result.stdout)

    @unittest.skipIf(os.name == "nt", "fake POSIX executables")
    def test_skip_browser_is_partial_and_invalidates_old_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project, runtime = base / "project", base / "runtime"
            project.mkdir()
            (runtime / module.BROWSER_MARKER).parent.mkdir(parents=True)
            (runtime / module.BROWSER_MARKER).write_text("stale", encoding="utf-8")
            args = self.parse(
                "install",
                "--scope",
                "custom",
                "--directory",
                str(runtime),
                "--project-root",
                str(project),
                "--skip-browser",
            )
            crawl = runtime / ".venv" / "bin" / "crwl"
            traf = runtime / ".trafilatura-venv" / "bin" / "trafilatura"
            for executable in (crawl, traf):
                executable.parent.mkdir(parents=True, exist_ok=True)
                executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                executable.chmod(0o755)
            output = StringIO()
            with (
                patch.object(module, "_run_visible"),
                patch.object(module, "_probe_executable", return_value=(True, "ok")),
                patch.object(
                    module,
                    "_runtime_identity",
                    return_value={
                        "crwl": str(crawl),
                        "trafilatura": str(traf),
                        "crawl4ai": "0.9.2",
                        "trafilatura_version": "2.2.0",
                        "fingerprint": "new",
                    },
                ),
                redirect_stdout(output),
            ):
                result = module.cmd_install(args)
            self.assertEqual(result, 2)
            self.assertIn("NOT verified", output.getvalue())
            self.assertNotIn("Browser setup verified", output.getvalue())
            self.assertFalse((runtime / module.BROWSER_MARKER).exists())
            state = json.loads((runtime / module.RUNTIME_STATE).read_text())
            self.assertEqual(state["fingerprint"], "new")

    @unittest.skipIf(os.name == "nt", "fake POSIX executables")
    def test_browser_setup_uses_runtime_not_project_as_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project, runtime = base / "project", base / "runtime"
            project.mkdir()
            crawl = runtime / ".venv" / "bin" / "crwl"
            traf = runtime / ".trafilatura-venv" / "bin" / "trafilatura"
            setup = runtime / ".venv" / "bin" / "crawl4ai-setup"
            for executable in (crawl, traf, setup):
                executable.parent.mkdir(parents=True, exist_ok=True)
                executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                executable.chmod(0o755)
            args = self.parse(
                "install",
                "--scope",
                "custom",
                "--directory",
                str(runtime),
                "--project-root",
                str(project),
            )
            with (
                patch.object(module, "_run_visible"),
                patch.object(module, "_probe_executable", return_value=(True, "ok")),
                patch.object(
                    module, "_runtime_identity", return_value={"fingerprint": "current"}
                ),
                patch.object(module, "_run", return_value=(0, b"", b"")) as run,
                redirect_stdout(StringIO()),
            ):
                self.assertEqual(module.cmd_install(args), 0)
            setup_call = run.call_args
            self.assertEqual(setup_call.kwargs["cwd"].resolve(), runtime.resolve())
            self.assertEqual(
                Path(setup_call.kwargs["env"]["CRAWL4_AI_BASE_DIRECTORY"]).resolve(),
                runtime.resolve(),
            )
            self.assertFalse((project / "global.yml").exists())

    @unittest.skipIf(os.name == "nt", "fake POSIX executables")
    def test_status_probes_executables_and_rejects_stale_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project, runtime = base / "project", base / "runtime"
            project.mkdir()
            crawl = runtime / ".venv" / "bin" / "crwl"
            traf = runtime / ".trafilatura-venv" / "bin" / "trafilatura"
            for executable in (crawl, traf):
                executable.parent.mkdir(parents=True, exist_ok=True)
                executable.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
                executable.chmod(0o755)
            module._write_json_atomic(
                runtime / module.BROWSER_MARKER,
                {"verified_at": "yesterday", "runtime_fingerprint": "stale"},
            )
            args = self.parse(
                "status",
                "--project-root",
                str(project),
                "--runtime-root",
                str(runtime),
            )
            output = StringIO()
            with redirect_stdout(output):
                result = module.cmd_status(args)
            self.assertEqual(result, 1)
            self.assertIn("Crawl4AI: broken", output.getvalue())
            self.assertIn("Trafilatura: broken", output.getvalue())
            self.assertIn("Browser: unverified", output.getvalue())

            for executable in (crawl, traf):
                executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            with (
                patch.object(
                    module,
                    "_runtime_identity",
                    return_value={"fingerprint": "current"},
                ),
                redirect_stdout(output := StringIO()),
            ):
                result = module.cmd_status(args)
            self.assertEqual(result, 2)
            self.assertIn("Browser: unverified", output.getvalue())

    def test_browser_marker_requires_current_runtime_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module._write_json_atomic(
                root / module.BROWSER_MARKER,
                {"verified_at": "now", "runtime_fingerprint": "one"},
            )
            self.assertEqual(
                module._browser_verification(root, {"fingerprint": "one"}), "now"
            )
            self.assertIsNone(
                module._browser_verification(root, {"fingerprint": "two"})
            )

    def test_clear_cache_preserves_outputs_and_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            for directory in ("cache", "robots", "outputs", "runtime"):
                target = project / ".crawl4ai" / directory
                target.mkdir(parents=True)
                (target / "data").write_text("x", encoding="utf-8")
            args = self.parse("clear-cache", "--project-root", str(project))
            with redirect_stdout(StringIO()):
                self.assertEqual(module.cmd_clear_cache(args), 0)
            self.assertFalse((project / ".crawl4ai" / "cache").exists())
            self.assertFalse((project / ".crawl4ai" / "robots").exists())
            self.assertTrue((project / ".crawl4ai" / "outputs" / "data").exists())
            self.assertTrue((project / ".crawl4ai" / "runtime" / "data").exists())

    @unittest.skipIf(os.name == "nt", "fake POSIX executables")
    def test_smoke_test_records_current_browser_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project, runtime = base / "project", base / "runtime"
            project.mkdir()
            crawl = runtime / ".venv" / "bin" / "crwl"
            traf = runtime / ".trafilatura-venv" / "bin" / "trafilatura"
            crawl.parent.mkdir(parents=True)
            traf.parent.mkdir(parents=True)
            crawl.write_text(
                "#!/usr/bin/env python3\n"
                "import json\n"
                "print(json.dumps({'html': '<html><body>Hello</body></html>'}))\n",
                encoding="utf-8",
            )
            traf.write_text(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "data=sys.stdin.read()\n"
                "assert 'Hello' in data\n"
                "print('# Hello')\n",
                encoding="utf-8",
            )
            crawl.chmod(0o755)
            traf.chmod(0o755)
            args = self.parse(
                "test",
                "--project-root",
                str(project),
                "--runtime-root",
                str(runtime),
                "--timeout",
                "5",
            )
            with redirect_stdout(StringIO()):
                self.assertEqual(module.cmd_test(args), 0)
            identity = module._runtime_identity(crawl, traf, project)
            self.assertIsNotNone(module._browser_verification(runtime, identity))
            self.assertTrue((runtime / module.RUNTIME_STATE).is_file())

    @unittest.skipIf(os.name == "nt", "fake POSIX executable")
    def test_trafilatura_pipeline_writes_extract_and_raw_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            crawl_json = project / "crawl.json"
            crawl_json.write_text(
                json.dumps(
                    {
                        "html": "<html><body><h1>Hello</h1></body></html>",
                        "markdown": {"raw_markdown": "# Hello"},
                        "media": {"images": []},
                    }
                ),
                encoding="utf-8",
            )
            executable = project / "trafilatura"
            executable.write_text(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "html = sys.stdin.read()\n"
                "assert '<h1>Hello</h1>' in html\n"
                "print('# Extracted\\n\\nHello world')\n",
                encoding="utf-8",
            )
            executable.chmod(0o755)
            args = self.parse(
                "crawl",
                "https://example.com",
                "--extractor",
                "trafilatura",
                "--output-format",
                "markdown",
            )
            output = project / "result.md"
            extracted, raw, stats = module._extract_trafilatura(
                crawl_json, executable, args, project, output
            )
            self.assertEqual(stats, None)
            self.assertIn("# Extracted", extracted.read_text(encoding="utf-8"))
            self.assertIn("<h1>Hello</h1>", raw.read_text(encoding="utf-8"))

    @unittest.skipIf(os.name == "nt", "POSIX process-group behavior")
    def test_timeout_terminates_child_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pid_file = root / "child.pid"
            script = (
                "import pathlib, subprocess, sys, time\n"
                "child=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
                "pathlib.Path(sys.argv[1]).write_text(str(child.pid))\n"
                "time.sleep(60)\n"
            )
            with self.assertRaises(module.CliError):
                module._run(
                    [sys.executable, "-c", script, str(pid_file)],
                    cwd=root,
                    timeout=1,
                )
            child_pid = int(pid_file.read_text())
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                result = subprocess.run(
                    ["ps", "-p", str(child_pid), "-o", "stat="],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if not result.stdout.strip() or result.stdout.strip().startswith("Z"):
                    break
                time.sleep(0.05)
            else:
                self.fail(f"child process {child_pid} survived timeout cleanup")

    def test_requirements_are_exactly_pinned(self) -> None:
        expected = {
            "crawl4ai.txt": "crawl4ai==0.9.2",
            "trafilatura.txt": "trafilatura==2.2.0",
        }
        for filename, requirement in expected.items():
            lines = [
                line.strip()
                for line in (module.REQUIREMENTS_DIR / filename)
                .read_text()
                .splitlines()
                if line.strip() and not line.startswith("#")
            ]
            self.assertEqual(lines, [requirement])

    def test_cli_help(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI), "crawl", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--bm25-query", result.stdout)
        self.assertIn("--deep-crawl", result.stdout)


if __name__ == "__main__":
    unittest.main()
