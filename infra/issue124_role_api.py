"""Direct HTTP permission smoke on the persistent synthetic single stack."""

import argparse
import http.cookiejar
import json
import urllib.error
import urllib.parse
import urllib.request

from uat_demo import execute


def request(opener, url, values=None):
    data = urllib.parse.urlencode(values).encode() if values else None
    try:
        with opener.open(urllib.request.Request(url, data=data), timeout=30) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()
    fixture = json.load(open(args.fixture))["fixture"]
    demo = execute("inspect")
    base = "http://127.0.0.1:8082"
    center = fixture["centers"][0]
    invoice = demo["invoices"]["Theta insoluto scaduto"]
    report = "/api/method/centrochange_core.finance.patient_reporting.patient_view?" + urllib.parse.urlencode(
        {"center": center, "start": "2026-09-28", "end": "2026-10-31"}
    )
    native = "/api/resource/Sales%20Invoice/" + urllib.parse.quote(invoice)
    result = {}
    for role in ("m", "a", "guest"):
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        if role != "guest":
            user = fixture["users"][role]
            assert request(opener, base + "/api/method/login", {"usr": user["name"], "pwd": user["password"]})[0] == 200
        report_status, report_body = request(opener, base + report)
        native_status, native_body = request(opener, base + native)
        if role == "m":
            assert report_status == native_status == 200
            assert json.loads(report_body).get("message") is not None
            assert json.loads(native_body).get("data") is not None
        else:
            assert report_status in (401, 403) and native_status in (401, 403)
            assert b'"message"' not in report_body or b'"message": null' in report_body
            assert b'"data"' not in native_body or b'"data": null' in native_body
        result[role] = {"scoped_report": report_status, "native_invoice": native_status}
    print(json.dumps({"status": "PASS", "direct_http": result, "mutations": "NONE"}))


if __name__ == "__main__":
    main()
