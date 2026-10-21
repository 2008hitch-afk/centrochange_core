#!/usr/bin/env python3
"""Fail-closed source and candidate-image checks for the #148 overlay.

The manifest records the exact bytes approved for the image. This checker is
stdlib-only and does not access Docker, a Site, secrets, or the network.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
APP = Path('app/centrochange_core/centrochange_core')
DEST = Path('apps/centrochange_core/centrochange_core')
MANIFEST = Path('infra/premium-single-stack-payload.json')
BASE_IMAGE = 'centrochange-single:issue75-form-affordance-r2'
BASE_IMAGE_ID = 'sha256:6d6f9d2e65d0b16974e6b04aeaaf6d1210f071448ace5276689ebc9652bc2f7b'
BASE_APP_REVISION = 'e2fd728ecf6acdb0e0ab26379820df6905dd5521'
PYTHON = (
    'catalog.py', 'scoped_api.py', 'operations/profiles.py',
    'finance/payments.py', 'finance/documents.py',
)
WEB = ('www/premium.html', 'www/premium.py',
       'www/premium-primo-incontro.html', 'www/premium_primo_incontro.py')
BASE_FILES = ('hooks.py', 'security/audit.py', 'security/guards.py',
              'security/lifecycle.py', 'security/permissions.py',
              'scheduling/booking.py', 'finance/guards.py',
              'operations/workspace.py')
PINS = {'frappe': '16.50.0', 'erpnext': '16.50.0',
        'healthcare': '16.6.1', 'builder': '1.35.1'}
NPM_PINS = {'react': '19.3.1', 'react-dom': '19.3.1',
            'vite': '8.3.5', '@playwright/test': '1.58.2'}
METHODS = {
    'catalog.records', 'catalog.detail', 'catalog.service_save',
    'catalog.service_create', 'catalog.item_save',
    'catalog.appointment_type_save', 'catalog.appointment_type_create',
    'catalog.price_save', 'catalog.price_create',
    'catalog.package_template_save', 'catalog.package_template_create',
    'operations.profiles.patients', 'operations.profiles.patient_detail',
    'operations.profiles.patient_save', 'operations.profiles.practitioners',
    'operations.profiles.practitioner_detail',
    'operations.profiles.practitioner_save',
    'finance.payments.records', 'finance.payments.detail',
    'finance.documents.preview',
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline_hashes(root):
    result = {}
    for name in BASE_FILES:
        content = subprocess.check_output(
            ['git', 'show', f'{BASE_APP_REVISION}:{APP / name}'], cwd=root)
        result[name] = hashlib.sha256(content).hexdigest()
    return result


def payload_files(root):
    assets = sorted((root / APP / 'public/premium').glob('*'))
    require(assets and all(p.is_file() for p in assets), 'Premium assets missing or nested')
    return [APP / name for name in (*PYTHON, *WEB)] + [p.relative_to(root) for p in assets]


def manifest_from_source(root):
    files = payload_files(root)
    require(all((root / p).is_file() for p in files), 'Required overlay file missing')
    return {'schema': 1, 'base_image': BASE_IMAGE,
            'base_image_id': BASE_IMAGE_ID,
            'base_application_revision': BASE_APP_REVISION,
            'upstream_versions': PINS,
            'base_dependency_files': baseline_hashes(root),
            'files': {str(p.relative_to(APP)): digest(root / p) for p in files}}


def check_contract(root, manifest):
    require(manifest['schema'] == 1 and manifest['upstream_versions'] == PINS and
            manifest['base_image'] == BASE_IMAGE and manifest['base_image_id'] == BASE_IMAGE_ID and
            manifest['base_application_revision'] == BASE_APP_REVISION, 'Manifest pins changed')
    expected = manifest_from_source(root)
    require(manifest['files'] == expected['files'], 'Source/manifest hash drift')
    require(manifest['base_dependency_files'] == expected['base_dependency_files'],
            'Pinned backend dependency hash drift')
    dockerfile = (root / 'infra/Dockerfile.premium-single-stack').read_text()
    require(f'FROM {BASE_IMAGE}' in dockerfile and BASE_APP_REVISION in dockerfile,
            'Dockerfile base image/revision drift')
    copies = [line for line in dockerfile.splitlines() if line.startswith('COPY ')]
    require(len(copies) == len(PYTHON) + len(WEB) + 3,
            'Dockerfile includes an unexpected or missing COPY')
    for name in (*PYTHON, *WEB):
        source = str(APP / name)
        destination = str(DEST / name)
        require(f'COPY --chown=frappe:frappe {source} {destination}' in dockerfile,
                f'Dockerfile does not copy {name}')
    require('COPY --chown=frappe:frappe ' + str(APP / 'public/premium/') in dockerfile,
            'Dockerfile does not copy React assets')
    for name in ('premium-single-stack-payload.json', 'premium_single_stack_package.py'):
        require(f'COPY --chown=frappe:frappe infra/{name} infra/{name}' in dockerfile,
                f'Dockerfile does not copy verifier {name}')
    require('premium_single_stack_package.py --image' in dockerfile,
            'Dockerfile does not run image verifier')
    require('bench build --force' in dockerfile, 'Pinned Bench asset build missing')
    html = (root / APP / 'www/premium.html').read_text()
    require('/assets/centrochange_core/premium/app.js' in html and
            '/assets/centrochange_core/premium/app.css' in html and
            'csrf-token' in html, 'Frappe React shell/CSRF missing')
    js = (root / APP / 'public/premium/app.js').read_text()
    require(all(method.removeprefix('operations.').removeprefix('finance.') in js for method in METHODS),
            'Compiled React entry lacks scoped archive methods')
    require('Archivi' in js and 'centrochange_core' in js,
            'Compiled React entry lacks Frappe navigation/API wiring')
    lock = json.loads((root / 'frontend/premium/package-lock.json').read_text())
    require(all(lock['packages']['node_modules/' + name]['version'] == version
                for name, version in NPM_PINS.items()), 'Frontend lockfile pin drift')
    for method in METHODS:
        module, function = method.rsplit('.', 1)
        file = root / APP / (module.replace('.', '/') + '.py')
        verb = 'POST' if function.endswith(('_save', '_create')) else 'GET'
        pattern = (r"@frappe\.whitelist\(methods=\['" + verb +
                   r"'\]\)\s+def " + re.escape(function) + r'\(')
        require(file.is_file() and re.search(pattern, file.read_text(), re.M),
                f'Python endpoint missing: {method}')


def check_image(bench, manifest):
    for name, expected in manifest['base_dependency_files'].items():
        file = bench / DEST / name
        require(file.is_file() and digest(file) == expected,
                f'Pinned backend dependency drift: {name}')
    for name, expected in manifest['files'].items():
        file = bench / DEST / name
        require(file.is_file() and digest(file) == expected, f'Image payload missing/drifted: {name}')
    # Editable Bench apps must resolve to the overlaid source, not stale wheel code.
    for module in ('centrochange_core', 'centrochange_core.catalog',
                   'centrochange_core.scoped_api', 'centrochange_core.operations.profiles',
                   'centrochange_core.finance.payments', 'centrochange_core.finance.documents'):
        imported = importlib.import_module(module)
        require(Path(imported.__file__).resolve().is_relative_to((bench / DEST).resolve()),
                f'Imported module is outside candidate app: {module}')
    for name, version in PINS.items():
        file = bench / 'apps' / name / name / '__init__.py'
        require(file.is_file(), f'Pinned app missing: {name}')
        match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]+)', file.read_text(), re.M)
        require(match and match.group(1) == version,
                f'Pinned app version mismatch: {name}')
    hooks = (bench / DEST / 'hooks.py').read_text()
    require('before_request' in hooks and 'permission_query_conditions' in hooks,
            'Pinned backend security hooks absent')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-manifest', action='store_true')
    parser.add_argument('--source', action='store_true')
    parser.add_argument('--image', type=Path, metavar='BENCH_ROOT')
    args = parser.parse_args()
    require(sum(bool(x) for x in (args.write_manifest, args.source, args.image)) == 1,
            'Select exactly one mode')
    if args.write_manifest:
        (ROOT / MANIFEST).write_text(json.dumps(manifest_from_source(ROOT), indent=2, sort_keys=True) + '\n')
        return
    manifest = json.loads((ROOT / MANIFEST).read_text())
    if args.source:
        check_contract(ROOT, manifest)
        print('PASS premium single-stack source payload')
    else:
        check_image(args.image.resolve(), manifest)
        print('PASS premium single-stack candidate image payload')


if __name__ == '__main__':
    try:
        main()
    except (KeyError, OSError, RuntimeError) as exc:
        print(f'FAIL premium single-stack package: {exc}', file=sys.stderr)
        sys.exit(1)
