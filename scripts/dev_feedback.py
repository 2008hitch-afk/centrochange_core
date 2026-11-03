#!/usr/bin/env python3
"""Minimal, framework-neutral local preview and test runner for EMPV Goals.

This does NOT run an AI agent, perform a deployment, or authorize a release.
The coding agent drives the edit/test/fix loop using these repeatable commands.
"""
import argparse
import json
import os
import signal
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener


class FeedbackError(Exception):
    pass


def within(root, relative, label):
    if not isinstance(relative, str) or not relative.strip():
        raise FeedbackError(label + " must be a nonempty project-relative path")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise FeedbackError(label + " must stay inside the project")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise FeedbackError(label + " escapes the project via symlink")
    return resolved


def argv(value, label):
    if not isinstance(value, list) or not value or any(
        not isinstance(item, str) or not item.strip() or "\x00" in item for item in value
    ):
        raise FeedbackError(label + " must be a nonempty array of command arguments")
    return value


def config_load(root, config):
    path = within(root, config, "config")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FeedbackError("Missing/invalid config: " + str(exc)) from exc
    if not isinstance(data, dict):
        raise FeedbackError("config must be a JSON object")
    cwd = within(root, data.get("cwd"), "cwd")
    if not cwd.is_dir():
        raise FeedbackError("Working directory does not exist: " + str(cwd))
    preview = data.get("preview")
    if not isinstance(preview, dict):
        raise FeedbackError("preview configuration is required")
    command = argv(preview.get("command"), "preview.command")
    url = preview.get("ready_url")
    if not isinstance(url, str):
        raise FeedbackError("preview.ready_url is required")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise FeedbackError("Invalid preview.ready_url port") from exc
    if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost") or (
        port is None or parsed.username or parsed.password or parsed.fragment
    ):
        raise FeedbackError("preview.ready_url must use http://127.0.0.1:PORT/ or localhost; never public hosts")
    suites = data.get("suites")
    if not isinstance(suites, dict) or not suites:
        raise FeedbackError("suites must define at least one named test")
    for name, args in suites.items():
        if not isinstance(name, str) or not name or not name.replace("_", "").replace("-", "").isalnum():
            raise FeedbackError("Invalid suite name")
        argv(args, "suites." + name)
    return cwd, command, url, suites


def check_executable(command, cwd):
    executable = command[0]
    if executable.startswith(".") or "/" in executable or "\\" in executable:
        location = Path(executable)
        if not location.is_absolute():
            location = cwd / location
        if not location.is_file():
            raise FeedbackError("Executable not found: " + executable)
    elif shutil.which(executable) is None:
        raise FeedbackError("Executable not on PATH: " + executable)


class NoRedirect(HTTPRedirectHandler):
    """Do not follow localhost readiness redirects to external hosts."""
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def probe(url):
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(url, timeout=3) as response:
            return 200 <= response.status < 400
    except (URLError, HTTPError, TimeoutError, OSError):
        return False


def git_sha(root):
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def write_summary(root, suite, exit_code, started):
    report_dir = root / ".factory-runtime"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "kind": "LOCAL_TEST_EXECUTION", "suite": suite,
        "status": "PASS_LOCAL" if exit_code == 0 else "FAIL_LOCAL",
        "exit_code": exit_code, "commit_sha": git_sha(root),
        "started_utc": started,
        "ended_utc": datetime.now(timezone.utc).isoformat(),
        "warning": "Not independent review, LIVE Frappe UAT, Founder acceptance or deploy authorization."
    }
    (report_dir / ("last-" + suite + ".json")).write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def stop_process_tree(proc):
    """Best-effort process-group termination on POSIX, direct child on Windows."""
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    elif proc.poll() is None:
        proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif proc.poll() is None:
            proc.kill()
        proc.wait()


def run_test(root, cwd, suite, command, timeout):
    started = datetime.now(timezone.utc).isoformat()
    exit_code = 2
    check_executable(command, cwd)
    proc = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True,
                            start_new_session=(os.name == "posix"))
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        stop_process_tree(proc)
        stdout, stderr = proc.communicate()
        print("Test timed out; process tree termination attempted.", file=sys.stderr)
        exit_code = 124
    except KeyboardInterrupt:
        stop_process_tree(proc)
        stdout, stderr = proc.communicate()
        print("Test interrupted; process tree termination attempted.", file=sys.stderr)
        exit_code = 130
    sys.stdout.write(stdout or "")
    sys.stderr.write(stderr or "")
    report = write_summary(root, suite, exit_code, started)
    print(json.dumps(report, indent=2))
    return 0 if exit_code == 0 else 2


def preview_foreground(cwd, command, url):
    check_executable(command, cwd)
    if probe(url):
        raise FeedbackError("Preview is already reachable; reuse it rather than starting a second server")
    print("Starting LOCAL preview (Ctrl+C to stop); bind to loopback only.", flush=True)
    proc = subprocess.Popen(command, cwd=cwd,
                            start_new_session=(os.name == "posix"))
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    def stop_signal(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop_signal)
    try:
        return proc.wait()
    except KeyboardInterrupt:
        stop_process_tree(proc)
        return 130
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)


def main():
    parser = argparse.ArgumentParser(description="EMPV local development feedback; never deploys")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--config", default="factory/dev-feedback.json")
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("doctor", "preview", "check"):
        sub.add_parser(name)
    test = sub.add_parser("test")
    test.add_argument("--suite", required=True)
    test.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        if not root.is_dir():
            raise FeedbackError("Project root not found")
        cwd, command, url, suites = config_load(root, args.config)
        if args.action == "doctor":
            check_executable(command, cwd)
            for suite, argv_list in suites.items():
                check_executable(argv_list, cwd)
            print(json.dumps({"configured": True, "cwd": str(cwd), "ready_url": url,
                              "suites": sorted(suites), "scope": "LOCAL_ONLY"}, indent=2))
            return 0
        if args.action == "preview":
            return preview_foreground(cwd, command, url)
        if args.action == "check":
            ready = probe(url)
            print(json.dumps({"preview_ready": ready, "ready_url": url}))
            return 0 if ready else 2
        if args.suite not in suites:
            raise FeedbackError("Unknown suite; choose one of: " + ", ".join(sorted(suites)))
        if args.timeout < 1:
            raise FeedbackError("timeout must be positive")
        return run_test(root, cwd, args.suite, suites[args.suite], args.timeout)
    except (FeedbackError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
