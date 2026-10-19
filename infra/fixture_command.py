"""Safely invoke a narrow set of synthetic fixture methods in a Frappe site.

Frappe 16.50's ``bench execute`` catches exceptions from the dotted method call
and retries the method string as a Python expression. That can mask the actual
fixture exception. This driver calls the method directly, rolls back on failure,
and returns the original traceback to this process for sanitization.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


BACKEND = "centrochange-dev-backend-1"
SITE = "centrochange.local"
BENCH_ROOT = "/home/frappe/frappe-bench"
RESULT_PREFIX = "CC_FIXTURE_RESULT="
ALLOWED_METHODS = frozenset({
    "centrochange_core.security.dev_acceptance.create_http",
    "centrochange_core.security.dev_acceptance.destroy_http",
    "centrochange_core.security.dev_acceptance.recover_http",
    "centrochange_core.security.dev_acceptance.pending_contacts",
    "centrochange_core.security.dev_acceptance.queue_notice_fixture",
    "centrochange_core.security.dev_acceptance.notice_fixture_status",
    "centrochange_core.security.lifecycle.set_membership",
    "centrochange_core.finance.incoming_acceptance.prepare_http",
    "centrochange_core.finance.receivables_acceptance.prepare_http",
    "centrochange_core.finance.receivables_acceptance.prepare_browser_invoice",
    "centrochange_core.finance.banking_acceptance.prepare_http",
})

_DRIVER = r'''import json, sys, traceback
import frappe
from frappe.utils.response import json_handler

request = json.loads(sys.stdin.read())
method = request["method"]
kwargs = request.get("kwargs") or {}
site = request["site"]
frappe_ready = False
try:
    frappe.init(site=site, sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()
    frappe_ready = True
    frappe.set_user("Administrator")
    if frappe.conf.get("cc_synthetic_dev") != 1:
        raise RuntimeError("Synthetic DEV guard is not enabled")
    result = frappe.get_attr(method)(**kwargs)
    frappe.db.commit()
    print("CC_FIXTURE_RESULT=" + json.dumps({"status": "PASS", "value": result}, default=json_handler))
except BaseException:
    diagnostic = traceback.format_exc()
    rollback_error = None
    if frappe_ready:
        try:
            frappe.db.rollback()
        except BaseException as error:
            rollback_error = type(error).__name__
    print("CC_FIXTURE_RESULT=" + json.dumps({
        "status": "ERROR", "diagnostic": diagnostic,
        "rollback_error_type": rollback_error,
    }))
    sys.exit(2)
finally:
    if frappe_ready:
        try:
            frappe.destroy()
        except BaseException:
            pass
'''


class FixtureCommandError(RuntimeError):
    """Sanitized fixture failure with original remote exception metadata."""

    def __init__(self, method: str, returncode: int, diagnostic: str,
                 diagnostic_path: Path | None = None):
        self.method = method
        self.returncode = returncode
        self.diagnostic = diagnostic
        self.diagnostic_path = diagnostic_path
        suffix = f"; diagnostic: {diagnostic_path}" if diagnostic_path else ""
        super().__init__(f"Synthetic fixture {method} failed (exit {returncode}): {diagnostic}{suffix}")


_SECRET_VALUE = re.compile(r"(?i)(\b(?:password|passwd|token|secret|api[_ -]?key|authorization|cookie|session)\b\s*[=:]\s*)([^\s,;]+)")
_SENSITIVE_ASSIGNMENT = re.compile(r"(?i)(\b(?:patient|customer|supplier|user|practitioner|account|bank[_ ]account|invoice|document|branch|uid|email|phone|iban|fiscal[_ ]code|tax[_ ]id)\b\s*[=:]\s*)([^\s,;]+)")
_AUTH_VALUE = re.compile(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+")
_URL_AUTH = re.compile(r"(?i)(https?://)[^/@\s:]+:[^/@\s]+@")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_QUOTED_DATA = re.compile(r"(?<!\\)(['\"])(?:\\.|(?!\1).)*?\1")


def sanitize_diagnostic(raw: str, *, max_chars: int = 6000) -> str:
    """Keep exception types, traceback locations and causes; redact values."""
    lines = raw.splitlines()
    selected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if (stripped.startswith(("Traceback ", "During handling of", "The above exception", "Direct cause",
                                 "Fixture helper exited without"))
                or re.match(r'^File "[^\"]+", line \d+, in ', stripped)
                or re.match(r"^[A-Za-z_][\w.]*\s*:", stripped)):
            selected.append(stripped)
    sanitized = []
    for line in selected:
        line = re.sub(r"/home/[^/\s]+/", "/home/[USER]/", line)
        line = _SECRET_VALUE.sub(r"\1[REDACTED]", line)
        line = _SENSITIVE_ASSIGNMENT.sub(r"\1[REDACTED_VALUE]", line)
        line = _AUTH_VALUE.sub(r"\1 [REDACTED]", line)
        line = _URL_AUTH.sub(r"\1[REDACTED]@", line)
        line = _EMAIL.sub("[REDACTED_EMAIL]", line)
        # Quoted values in validation messages can contain names, document IDs,
        # or account labels. Preserve the message shape, not the underlying data.
        if ":" in line and not line.startswith(("Traceback ", "During handling", "The above exception", "Direct cause")):
            key, message = line.split(":", 1)
            message = _QUOTED_DATA.sub("[REDACTED_VALUE]", message)
            line = key + ":" + message
        sanitized.append(line)
    value = "\n".join(sanitized) or "No traceback text captured"
    if len(value) > max_chars:
        value = value[:max_chars] + "\n[TRUNCATED]"
    return value


def _write_private(path: Path, method: str, content: str) -> Path:
    path = path.resolve()
    repository = Path(__file__).resolve().parents[1]
    if path == repository or repository in path.parents:
        raise ValueError("Fixture diagnostics must remain outside the repository")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.stat().st_uid != os.geteuid():
        raise PermissionError("Fixture diagnostic directory is not owned by the runner")
    os.chmod(path, 0o700)
    digest = hashlib.sha256(method.encode()).hexdigest()[:12]
    target = path / f"fixture-{digest}-{time.time_ns()}.diagnostic.txt"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(target, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(content + "\n")
    os.chmod(target, 0o600)
    return target


def execute_fixture(method: str, kwargs: dict | None = None, *,
                    backend: str = BACKEND, site: str = SITE,
                    diagnostic_dir: str | Path | None = None):
    if method not in ALLOWED_METHODS:
        raise ValueError("Fixture method is not allowlisted")
    if backend != BACKEND and not backend.startswith("cc139-w5-isolated-"):
        raise ValueError("Fixture backend is outside the approved DEV or isolated project")
    if site != SITE:
        raise ValueError("Fixture site is outside the approved synthetic site")
    request = json.dumps({"method": method, "kwargs": kwargs or {}, "site": site})
    command = ["docker", "exec", "-i", "-e", "FRAPPE_STREAM_LOGGING=1", "-w", BENCH_ROOT,
               backend, "env/bin/python", "-c", _DRIVER]
    completed = subprocess.run(command, input=request, text=True, capture_output=True)
    envelope = None
    for line in reversed(completed.stdout.splitlines()):
        if line.startswith(RESULT_PREFIX):
            try:
                envelope = json.loads(line[len(RESULT_PREFIX):])
                break
            except json.JSONDecodeError:
                pass
    if completed.returncode or not envelope or envelope.get("status") != "PASS":
        raw = "\n".join(filter(None, [
            envelope.get("diagnostic", "") if envelope else "",
            completed.stderr,
            "Fixture helper exited without a structured Frappe diagnostic"
            if not envelope or envelope.get("status") != "ERROR" else "",
        ]))
        diagnostic = sanitize_diagnostic(raw)
        rollback_error = envelope.get("rollback_error_type") if envelope else None
        if rollback_error:
            diagnostic += f"\nFixture transaction rollback failed: {rollback_error}"
        diagnostic_path = _write_private(Path(diagnostic_dir), method, diagnostic) if diagnostic_dir else None
        raise FixtureCommandError(method, completed.returncode, diagnostic, diagnostic_path)
    return envelope.get("value")
