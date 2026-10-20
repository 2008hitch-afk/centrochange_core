#!/usr/bin/env python3
"""One future Owner-gated Italian localization update; dry-run is read-only.

Inherits the verified encrypted backup, six-service update, essential security
checks and single rollback from #75. This file does not authorize execution.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent
PARENT = REPO / 'infra/issue75_native_ux_install.py'
PARENT_SHA = '5c4a6fa24b1ee74b7e399b63304b492bfc69dfd56211ebd4ed4ceaf5a24ce50f'
if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA:
    raise SystemExit('verified parent executor drift')
spec = importlib.util.spec_from_file_location('issue75_verified_gate', PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
gate = parent.gate
gate.__file__ = str(HERE)
gate.BASE_SOURCE = 'cc763958c234c9cbcc8cb46ce9f57533e47410ba'
gate.SOURCE = '0e6299d8a5507cc5d7dde46336870c0cd6667718'
gate.BASE_IMAGE = 'sha256:17380aa9aed4ee287d8c46ed1d851fe94ef42aa6586f3b9f379e0b8aff3f3602'
gate.BASE_TAG = 'centrochange-single:issue75-native-cc76395'
gate.IMAGE = 'centrochange-single:issue134-it-0e6299d'
gate.OVERLAY = REPO / 'infra/compose.issue134_italian.yaml'
gate.ACTIVE_OVERLAY_SHA = '21b1cfddfa233746fa803ee4a611d04b2ab1962cd92cd23410d2af6711a00e9e'
gate.RUN_ROOT = gate.STATE / 'issue134-italian-install-runs'
gate.DEPENDENCY_SHA = {**gate.DEPENDENCY_SHA,
    'infra/issue75_native_ux_install.py': PARENT_SHA,
    'infra/compose.issue134_italian.yaml': '8da3285db7b15e01dadb878a0a2fc0d72bd21ee11669ee39e036117bd269cb1f',
    'infra/browser/issue134_locale_sweep.cjs': '174989fde3758284ce94353b12807ad82f9988c5a90db6e2828d30b49f04516a',
    'infra/tests/test_issue134_locale.cjs': 'c87eb1088fc545063ac50c2ff6debceb4e492781e8f1c3fb14c2605d9e7e3c60',
    'infra/tests/test_issue134_translation_catalog.py': '7813f15dedf3a3fa4c314d175d88a8d818344b3f6345fbf9133fcdad44ce03f6',
}

def validate_owner_gate(path, executor_sha, *, recovery=False):
    gate.require(path.is_file() and path.stat().st_mode & 0o077 == 0,
                 'private Owner gate missing or unsafe')
    value = json.loads(path.read_text())
    required = {'issue','candidate','executor_sha256','authorize',
                'window_start_utc','operation_deadline_utc','recovery_deadline_utc'}
    gate.require(set(value) == required and value['issue'] == 134
                 and value['candidate'] == gate.SOURCE
                 and value['executor_sha256'] == executor_sha
                 and value['authorize'] == 'ISSUE134_ONE_CUMULATIVE_DEV_UPDATE',
                 'Owner gate identity mismatch')
    def parse(key):
        parsed = datetime.fromisoformat(value[key].replace('Z','+00:00'))
        gate.require(parsed.tzinfo is not None,'Owner gate timezone missing')
        return parsed.astimezone(timezone.utc)
    start,end,recover = map(parse,('window_start_utc','operation_deadline_utc','recovery_deadline_utc'))
    now = datetime.now(timezone.utc)
    gate.require(start <= now < (recover if recovery else end), 'Owner window expired')
    gate.require(timedelta(0) < end-start <= timedelta(hours=4)
                 and timedelta(0) < recover-end <= timedelta(hours=1),
                 'Owner window exceeds 4h plus 1h recovery')
    return {'operation_end':end,'recovery_end':recover}

gate.validate_owner_gate = validate_owner_gate

_source_probe = gate.source_probe
_restore_services = gate.restore_services

def refresh_translation_cache(module, expected=None):
    """Only after image activation/recovery; Frappe v16.50 caches CSV by language."""
    source = '''import frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
from frappe.translate import clear_cache,get_all_translations
clear_cache()
actual=get_all_translations("it").get("Occupation")
assert actual == EXPECTED, "Italian catalog did not match the active image"
frappe.db.rollback()
frappe.destroy()
print("CC_ITALIAN_CACHE=PASS")
'''.replace('EXPECTED', repr(expected))
    output = module.backend_python(source)
    gate.require('CC_ITALIAN_CACHE=PASS' in output, 'Italian translation cache refresh failed')

def source_probe(module, paths):
    result = _source_probe(module, paths)
    refresh_translation_cache(module, 'Professione')
    return result

def restore_services(*args, **kwargs):
    result = _restore_services(*args, **kwargs)
    # A rollback must not retain translations cached from the candidate image.
    # The original image may have no Occupation translation, so verify cache
    # invalidation without assuming a translated value.
    module = gate.old_probe()
    source = '''import frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
from frappe.translate import clear_cache
clear_cache()
frappe.db.rollback()
frappe.destroy()
print("CC_ITALIAN_ROLLBACK_CACHE=PASS")
'''
    gate.require('CC_ITALIAN_ROLLBACK_CACHE=PASS' in module.backend_python(source),
                 'rollback translation cache refresh failed')
    return result

gate.source_probe = source_probe
gate.restore_services = restore_services

if __name__ == '__main__':
    raise SystemExit(gate.main())
