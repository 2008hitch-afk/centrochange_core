#!/usr/bin/env python3
"""Future single Owner-gated #134 localization update; default dry-run is read-only.

The verified parent retains four-part encrypted backup, six-service update,
integrity checks and one rollback. No previous Owner gate can authorize this
candidate. After image activation, invalidate only Frappe's shared hook and
translation caches so the pinned boot_session HH:mm hook becomes effective.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent
PARENT = REPO / 'infra/issue134_final_install.py'
PARENT_SHA = 'e361d77e8a29e6040726c746be0533bbf387611940fb05c104e0acf2af204676'
if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA:
    raise SystemExit('verified final print/PDF executor drift')
spec = importlib.util.spec_from_file_location('issue134_final_verified_gate', PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
gate = parent.gate
gate.__file__ = str(HERE)
gate.BASE_SOURCE = '1b7ffc465ff699de163f9536ab04d4dde4da54e3'
gate.SOURCE = 'e52a88a960a699b08cfad91d2b86e2fbfdcfb6ec'
gate.BASE_IMAGE = 'sha256:d7315cb85d3d51ed6510b9d0f6f1b9b2be639cb2d637f67a57790136f5e55257'
gate.BASE_TAG = 'centrochange-single:issue134-final-1b7ffc4'
gate.IMAGE = 'centrochange-single:issue134-cumulative'
gate.OVERLAY = REPO / 'infra/compose.issue134_cumulative.yaml'
gate.ACTIVE_OVERLAY_SHA = 'e144cbc8005e6d6944059e0016efdcfb9de08b366f6db3877677a8ef9fb26c03'
gate.RUN_ROOT = gate.STATE / 'issue134-cumulative-install-runs'
gate.DEPENDENCY_SHA = {**gate.DEPENDENCY_SHA,
    'infra/issue134_final_install.py': PARENT_SHA,
    'infra/compose.issue134_cumulative.yaml':
        '1eb642e2634312cbd53d033fbe4490bed34b1235e470b644f1ae5283aad2ce41',
    'infra/tests/test_issue134_print_localization.py':
        '07301688b6ba652cafa73ad959d708d9639650772716a986f64d192c016cf7b3',
    'infra/tests/test_issue134_translation_catalog.py':
        '1cc66a3931ffcb9ca6edfe446c0db135b673afb91a9c7b602fe1c88dab58093f',
    'infra/tests/test_issue134_locale_presentation.py':
        'a712b54df3e4d9be1da802831393ddd72b2f2737cfb53bde279e75ca1ddd4e4f',
    'infra/tests/test_client_demo_list.cjs':
        'b1c82cbdc1487eeac94eaf051e99efbd075d62583e3b24faa3e7106cd5603482',
    'infra/browser/issue134_documents_post.cjs':
        'b8058b8f67e75797dca225ad78f9a8fa440093124fa76d1c2fe77bfdd3bb09fd',
}


def validate_owner_gate(path, executor_sha, *, recovery=False):
    gate.require(path.is_file() and path.stat().st_mode & 0o077 == 0,
                 'private cumulative Owner gate missing or unsafe')
    value = json.loads(path.read_text())
    required = {'issue', 'candidate', 'executor_sha256', 'authorize',
                'window_start_utc', 'operation_deadline_utc', 'recovery_deadline_utc'}
    gate.require(set(value) == required and value['issue'] == 134
                 and value['candidate'] == gate.SOURCE
                 and value['executor_sha256'] == executor_sha
                 and value['authorize'] == 'ISSUE134_CUMULATIVE_ONE_FINAL_DEV_UPDATE',
                 'cumulative Owner gate identity mismatch')
    def parse(key):
        result = datetime.fromisoformat(value[key].replace('Z', '+00:00'))
        gate.require(result.tzinfo is not None, 'Owner gate timezone missing')
        return result.astimezone(timezone.utc)
    start, end, recover = map(parse, ('window_start_utc', 'operation_deadline_utc',
                                      'recovery_deadline_utc'))
    now = datetime.now(timezone.utc)
    gate.require(start <= now < (recover if recovery else end), 'Owner window expired')
    gate.require(timedelta(0) < end - start <= timedelta(hours=4)
                 and timedelta(0) < recover - end <= timedelta(hours=1),
                 'Owner window exceeds 4h plus 1h recovery')
    return {'operation_end':end, 'recovery_end':recover}


def refresh_hook_cache(module, *, verify_candidate):
    source = '''import frappe
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.client_cache.delete_value("app_hooks")
from frappe.translate import clear_cache
clear_cache()
hooks=frappe.get_hooks("boot_session")
if VERIFY:
    assert "centrochange_core.operations.website_brand.client_time_format" in hooks, "HH:mm client boot hook unavailable"
frappe.db.rollback()
frappe.destroy()
print("CC_LOCALE_HOOK_CACHE=PASS")
'''.replace('VERIFY', 'True' if verify_candidate else 'False')
    gate.require('CC_LOCALE_HOOK_CACHE=PASS' in module.backend_python(source),
                 'Frappe locale hook cache invalidation failed')


_source_probe = gate.source_probe
_restore_services = gate.restore_services


def source_probe(module, paths):
    result = _source_probe(module, paths)
    refresh_hook_cache(module, verify_candidate=True)
    return result


def restore_services(*args, **kwargs):
    result = _restore_services(*args, **kwargs)
    refresh_hook_cache(gate.old_probe(), verify_candidate=False)
    return result


gate.validate_owner_gate = validate_owner_gate
gate.source_probe = source_probe
gate.restore_services = restore_services

if __name__ == '__main__':
    raise SystemExit(gate.main())
