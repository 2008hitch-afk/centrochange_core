#!/usr/bin/env python3
"""Owner-gated single DEV update for #134 invoice localization and PDF routing.

Default --dry-run is read-only. The inherited executor performs preflight,
encrypted full backup, six-service image update, integrity checks and one
rollback. This file does not itself authorize execution on the shared DEV.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent
PARENT = REPO / 'infra/issue134_italian_install.py'
PARENT_SHA = '17683dda3ac6397c5e68e9295b36862f2fe626bed0bcfa19add79a5e13f15033'
if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA:
    raise SystemExit('verified Italian installation executor drift')
spec = importlib.util.spec_from_file_location('issue134_verified_gate', PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
gate = parent.gate
gate.__file__ = str(HERE)
gate.BASE_SOURCE = '0e6299d8a5507cc5d7dde46336870c0cd6667718'
gate.SOURCE = '6fc6ecacd43fc486f747a99428757be2c6cdbb68'
gate.BASE_IMAGE = 'sha256:a681d9a22a8198cec60469564e4a3c919a1318d824a16e53010b33d4879719d5'
gate.BASE_TAG = 'centrochange-single:issue134-it-0e6299d'
gate.IMAGE = 'centrochange-single:issue134-final-6fc6eca'
gate.OVERLAY = REPO / 'infra/compose.issue134_final.yaml'
gate.FRONTEND_TEMPLATE = REPO / 'infra/issue134_frontend_pdf.conf.template'
gate.ACTIVE_OVERLAY_SHA = '8da3285db7b15e01dadb878a0a2fc0d72bd21ee11669ee39e036117bd269cb1f'
gate.RUN_ROOT = gate.STATE / 'issue134-final-install-runs'
gate.DEPENDENCY_SHA = {**gate.DEPENDENCY_SHA,
    'infra/issue134_italian_install.py': PARENT_SHA,
    'infra/compose.issue134_final.yaml': 'f077f95b93f792a8e726b2e7eea32fbea4bd950f2e629e9b604ac5fe2eab368d',
    'infra/issue134_frontend_pdf.conf.template': '04804a9674a97dbdca1a01003b39536030bb9d858447d5a0d32e4a19f8a4c116',
    'infra/tests/test_issue134_print_localization.py': 'afe1df2d47bcb2c38f04d6d5c85e5a161806e7603e07ef0ec889842b42eee554',
    'infra/tests/issue134_pdf_network_rehearsal.sh': '47a469065d56ed04724bee88c25659a3b84551f4c6a10ce0d854184e6e4fe05b',
    'infra/browser/issue134_documents_post.cjs': '95b27743f9dd1f83c4a668512d7f397b1a57f544c42e32c29e85a3d99d8d37b3',
    'infra/tests/test_issue134_final_install.py': 'aa2c8271f017ede578d2b7551e2c8da791ef12e3b5c5c018ceea0f588878977a',
}


def validate_owner_gate(path, executor_sha, *, recovery=False):
    gate.require(path.is_file() and path.stat().st_mode & 0o077 == 0,
                 'private final Owner gate missing or unsafe')
    value = json.loads(path.read_text())
    required = {'issue', 'candidate', 'executor_sha256', 'authorize',
                'window_start_utc', 'operation_deadline_utc', 'recovery_deadline_utc'}
    gate.require(set(value) == required and value['issue'] == 134
                 and value['candidate'] == gate.SOURCE
                 and value['executor_sha256'] == executor_sha
                 and value['authorize'] == 'ISSUE134_FINAL_ONE_CUMULATIVE_DEV_UPDATE',
                 'final Owner gate identity mismatch')
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
    return {'operation_end': end, 'recovery_end': recover}


gate.validate_owner_gate = validate_owner_gate

if __name__ == '__main__':
    raise SystemExit(gate.main())
