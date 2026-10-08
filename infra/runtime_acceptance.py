"""Read-only runtime acceptance plus rolled-back synthetic smoke; no secrets in output."""

import argparse
import hashlib
import http.cookiejar
import json
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True).strip()


def execute(expression):
    return json.loads(docker("exec", "centrochange-dev-backend-1", "bench", "--site",
                             "centrochange.local", "execute", expression))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--snapshot", required=True)
    args = parser.parse_args()
    config = dict(line.split("=", 1) for line in Path(args.env_file).read_text().splitlines()
                  if line and not line.startswith("#"))
    assert config["SITE_NAME"] == "centrochange.local"
    base = "http://127.0.0.1:" + config["HTTP_PORT"]
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def get(path):
        with opener.open(base + path, timeout=30) as response:
            assert response.status == 200
            return response.read()

    assert json.loads(get("/api/method/ping"))["message"] == "pong"
    get("/login")
    request = urllib.request.Request(base + "/api/method/login", data=urllib.parse.urlencode(
        {"usr": "Administrator", "pwd": config["ADMIN_PASSWORD"]}).encode())
    with opener.open(request, timeout=30) as response:
        assert json.load(response)["message"] == "Logged In"
    assert json.loads(get("/api/method/frappe.auth.get_logged_user"))["message"] == "Administrator"
    get("/app")
    try:
        get("/api/method/centrochange_core.dev_bootstrap.smoke")
    except urllib.error.HTTPError as error:
        assert error.code == 403
    else:
        raise AssertionError("DEV smoke must not be exposed through RPC")
    manifest = json.loads(docker("exec", "centrochange-dev-backend-1", "cat", "sites/assets/assets.json"))
    for key in ["desk.bundle.js", "erpnext.bundle.js", "healthcare.bundle.js", "login.bundle.css"]:
        assert len(get(manifest[key])) > 100
    for app in ["builder", "healthcare"]:
        files = json.loads(docker("exec", "centrochange-dev-backend-1", "env/bin/python", "-c",
            "import pathlib,json; print(json.dumps([str(p).split('/public/',1)[1] for p in "
            f"pathlib.Path('apps/{app}/{app}/public/frontend/assets').glob('*.js')]))"))
        assert files
        assert len(get("/assets/" + app + "/" + files[0])) > 100
    with socket.create_connection(("127.0.0.1", int(config["HTTP_PORT"])), timeout=10) as connection:
        connection.sendall(b"GET /socket.io/?EIO=4&transport=websocket HTTP/1.1\r\n"
            b"Host: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
            b"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n")
        assert b"101 Switching Protocols" in connection.recv(4096)
    assert execute("frappe.db.get_single_value('System Settings','enable_scheduler')") == 1
    doctor = docker("exec", "centrochange-dev-backend-1", "bench", "doctor")
    assert "Workers online: 2" in doctor and "disabled" not in doctor.lower()
    for queue in ["short", "long"]:
        job_id = "wp00-acceptance-" + queue
        execute(f"{{'id':frappe.enqueue('frappe.utils.now', queue='{queue}',job_id='{job_id}').id}}")
        for attempt in range(20):
            status = execute("{'status':__import__('frappe.utils.background_jobs',fromlist=['get_job'])"
                             f".get_job('{job_id}').get_status()}}")["status"]
            if status == "finished":
                break
            time.sleep(1)
        assert status == "finished", (queue, status)
    assert execute("centrochange_core.dev_bootstrap.smoke")["appointment"]
    for mutation in ["frappe.set_user('Guest')", "frappe.conf.update({'cc_synthetic_dev':0})"]:
        denied = subprocess.run(["docker", "exec", "centrochange-dev-backend-1", "bench", "--site",
            "centrochange.local", "execute", "(" + mutation +
            ", __import__('centrochange_core.dev_bootstrap',fromlist=['setup']).setup())[1]"],
            capture_output=True, text=True)
        assert denied.returncode != 0
        assert "Synthetic bootstrap requires" in denied.stdout + denied.stderr
    counts = execute("{dt:frappe.db.count(dt) for dt in "
                     "['Patient','Healthcare Practitioner','Patient Appointment']}")
    assert counts == dict.fromkeys(counts, 0)
    baseline = execute("{'apps':frappe.get_installed_apps(), 'setup':frappe.is_setup_complete(),"
        "'company':frappe.db.get_value('Company','Centro Change SYNTHETIC DEV',"
        "['country','default_currency'],as_dict=True), 'schema':frappe.get_all('DocType',"
        "fields=['name','module'],order_by='name'), 'synthetic_counts':"
        "{dt:frappe.db.count(dt) for dt in ['Patient','Healthcare Practitioner','Patient Appointment']}}")
    Path(args.snapshot).write_text(json.dumps(baseline, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"result": "PASS", "http_login_desk": True, "assets": True,
        "websocket_upgrade": True, "workers": True, "scheduler_enabled": True,
        "native_smoke_cleanup": True, "bootstrap_negative_guards": True, "baseline_sha256": hashlib.sha256(
            json.dumps(baseline, sort_keys=True).encode()).hexdigest()}))


if __name__ == "__main__":
    main()
