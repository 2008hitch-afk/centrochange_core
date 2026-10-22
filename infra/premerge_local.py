#!/usr/bin/env python3
"""Run the #150 offline pre-merge suite in a disposable Git worktree.

No Docker, Frappe Site, DEV URL, credentials or persistent test data are used.
"""

import argparse
import ast
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
ASSETS = "app/centrochange_core/centrochange_core/public/premium"


def command(args, cwd, *, env=None, timeout=900):
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True,
                          timeout=timeout, check=False)


def version(args):
    result = command(args, ROOT, timeout=15)
    return result.stdout.strip() if result.returncode == 0 else "NOT_VERIFIED"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD", help="Existing Git commit to verify")
    parser.add_argument("--report", type=Path, required=True,
                        help="New JSON report outside this repository")
    args = parser.parse_args()
    report_path = args.report.resolve()
    if report_path.is_relative_to(ROOT.resolve()) or report_path.exists():
        parser.error("report must be a new path outside the repository")
    if command(["git", "status", "--porcelain"], ROOT).stdout.strip():
        parser.error("source worktree must be clean")
    sha_result = command(["git", "rev-parse", "--verify", f"{args.ref}^{{commit}}"], ROOT)
    if sha_result.returncode:
        parser.error("ref is not an existing commit")
    sha = sha_result.stdout.strip()
    os.umask(0o077)
    report = {
        "schema": 1,
        "source_sha": sha,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "environment": "disposable local Git worktree; no DEV, Docker or live Frappe",
        "toolchain": {"python": sys.version.split()[0], "node": version(["node", "--version"]),
                      "npm": version(["npm", "--version"])},
        "checks": [],
        "not_tested": ["GitHub Actions CI", "Frappe live/API roles", "Site/DB migration rehearsal",
                       "Login live timeout/lockout/reset email"],
    }
    with tempfile.TemporaryDirectory(prefix="cc-premerge-local-") as temporary:
        checkout = Path(temporary) / "checkout"
        added = False
        try:
            created = command(["git", "worktree", "add", "--detach", str(checkout), sha], ROOT)
            if created.returncode:
                raise RuntimeError("cannot create isolated worktree")
            added = True
            frontend = checkout / "frontend/premium"
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", CI="1")
            for key in list(env):
                if key.startswith(("CC_LOGIN_", "CC_PREMIUM_LIVE_", "FRAPPE_")):
                    env.pop(key)

            def run(label, argv, cwd=checkout, *, dependency=True, playwright=False):
                if not dependency:
                    report["checks"].append({"name": label, "status": "SKIP_DEPENDENCY",
                                             "command": argv, "exit_code": None})
                    return False
                try:
                    result = command(argv, cwd, env=env, timeout=1200 if playwright else 900)
                    item = {"name": label, "status": "PASS" if result.returncode == 0 else "FAIL",
                            "command": argv, "exit_code": result.returncode}
                    if playwright:
                        try:
                            outcome = json.loads(result.stdout)
                            stats = outcome["stats"]
                            item["tests"] = {key: stats.get(key, 0) for key in
                                             ("expected", "unexpected", "flaky", "skipped")}
                            def failed_specs(suites):
                                for suite in suites:
                                    for spec in suite.get("specs", []):
                                        if not spec.get("ok", False):
                                            yield {"file": spec.get("file"), "title": spec.get("title")}
                                    yield from failed_specs(suite.get("suites", []))
                            item["failed_specs"] = list(failed_specs(outcome.get("suites", [])))
                        except (ValueError, KeyError):
                            item["tests"] = "NOT_VERIFIED"
                    elif label.startswith("Python unit"):
                        match = re.search(r"Ran (\d+) tests?", result.stderr)
                        item["tests_run"] = int(match.group(1)) if match else "NOT_VERIFIED"
                    report["checks"].append(item)
                    return result.returncode == 0
                except subprocess.TimeoutExpired:
                    report["checks"].append({"name": label, "status": "FAIL_TIMEOUT",
                                             "command": argv, "exit_code": None})
                    return False

            run("Full source manifest", [sys.executable, "infra/verify_full_single_stack.py", "--source"])
            run("Python unit regressions", [sys.executable, "-m", "unittest", "discover",
                                             "-s", "tests", "-p", "test_*.py", "-v"])
            run("Python unit hook composition", [sys.executable, "-m", "unittest", "discover",
                                               "-s", "infra", "-p", "test_before_request_hooks.py", "-v"])
            try:
                files = list((checkout / "app/centrochange_core").rglob("*.py"))
                for path in files:
                    ast.parse(path.read_text())
                report["checks"].append({"name": "Python AST", "status": "PASS",
                                         "files": len(files), "exit_code": 0})
            except (OSError, SyntaxError):
                report["checks"].append({"name": "Python AST", "status": "FAIL",
                                         "exit_code": 1})
            installed = run("npm ci pinned lockfile", ["npm", "ci", "--ignore-scripts",
                                                     "--no-audit", "--no-fund"], frontend)
            run("React typecheck", ["npm", "run", "typecheck"], frontend, dependency=installed)
            built = run("React build", ["npm", "run", "build"], frontend, dependency=installed)
            run("Built asset parity", ["git", "diff", "--exit-code", "--", ASSETS],
                dependency=built)
            run("Post-build manifest", [sys.executable, "infra/verify_full_single_stack.py", "--source"],
                dependency=built)
            for label, config in (("Playwright premium synthetic", "playwright.config.ts"),
                                  ("Playwright scoped API synthetic", "playwright.scoped.config.ts")):
                run(label, ["npx", "playwright", "test", f"--config={config}",
                            "--workers=2", "--reporter=json"], frontend,
                    dependency=installed and built, playwright=True)
            report["toolchain"]["playwright"] = version([str(frontend / "node_modules/.bin/playwright"),
                                                           "--version"]) if installed else "NOT_VERIFIED"
        finally:
            if added:
                removed = command(["git", "worktree", "remove", "--force", str(checkout)], ROOT)
                report["scratch_cleanup"] = "PASS" if removed.returncode == 0 else "FAIL"
            report["finished_utc"] = datetime.now(timezone.utc).isoformat()
            report["overall"] = "PASS" if (report["checks"] and
                            all(item["status"] == "PASS" for item in report["checks"]) and
                            report.get("scratch_cleanup") == "PASS") else "FAIL"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with report_path.open("x") as output:
                json.dump(report, output, indent=2, ensure_ascii=False)
                output.write("\n")
    print(f"{report['overall']} local premerge {sha} report={report_path}")
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
