#!/usr/bin/env python3
"""Source/image parity for the complete #148 candidate; stdlib-only, read-only."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
APP = Path('app/centrochange_core')
BENCH_APP = Path('apps/centrochange_core')
MANIFEST = Path('infra/full-single-stack-manifest.json')
BASE_REV = '1f88207c6a71c4bf0252b912fe83313337cab16f'
BASE_IMAGE = 'frappe/erpnext:v16.50.0@sha256:833bceb57233908cbc949d7aa533942b18e54b329d846b933b66937c62b7e4ae'
VERSIONS = {'frappe': '16.50.0', 'erpnext': '16.50.0',
            'builder': '1.35.1', 'healthcare': '16.6.1'}
REFS = {'builder': '37e958bc4f801d06d0438c21b97b42c45c4eaa51',
        'healthcare': 'dda107b26e3a0fe1dbd65c7257371235de054a04'}
PREMIUM_ADDED = {
    'centrochange_core/catalog.py', 'centrochange_core/scoped_api.py',
    'centrochange_core/operations/profiles.py',
    'centrochange_core/uat/display.py',
    'centrochange_core/finance/payments.py',
    'centrochange_core/finance/documents.py',
    'centrochange_core/www/premium.py',
    'centrochange_core/www/premium.html',
    'centrochange_core/www/premium_primo_incontro.py',
    'centrochange_core/www/premium-primo-incontro.html',
    'centrochange_core/public/premium/app.js',
    'centrochange_core/public/premium/app.css',
    'centrochange_core/public/premium/public.js',
    'centrochange_core/public/premium/logo.webp',
    'centrochange_core/public/premium/style-BzDtaysS.js',
    'centrochange_core/public/css/login_v1.css',
    'centrochange_core/public/js/login_v1.js',
}
REVIEWED_BACKEND_DELTAS = {'centrochange_core/hooks.py',
                           'centrochange_core/security/permissions.py',
                           'centrochange_core/security/audit.py',
                           'centrochange_core/security/lifecycle.py',
                           'centrochange_core/operations/notes.py',
                           'centrochange_core/operations/packages.py',
                           'centrochange_core/finance/collections.py',
                           'centrochange_core/scheduling/booking.py',
                           'centrochange_core/operations/workspace.py',
                           'centrochange_core/operations/automation.py',
                           'centrochange_core/operations/reporting.py',
                           'centrochange_core/operations/lifecycle.py',
                           'centrochange_core/operations/dev_acceptance.py',
                           'centrochange_core/scheduling/availability.py',
                           'centrochange_core/finance/reporting.py',
                           'centrochange_core/operations/client_landing.py',
                           'centrochange_core/finance/reporting_acceptance.py',
                           'centrochange_core/security/dev_acceptance.py',
                           'centrochange_core/security/fixture_cleanup.py',
                           'centrochange_core/security/install.py',
                           'centrochange_core/operations/website_brand.py',
                           'centrochange_core/templates/cc_web_base.html',
                           'centrochange_core/translations/it.csv'}
ENDPOINT_MODULES = ('catalog', 'scoped_api', 'operations.profiles',
                    'finance.payments', 'finance.documents',
                    'finance.collections', 'scheduling.booking')


def require(value, message):
    if not value:
        raise RuntimeError(message)


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def hash_file(path):
    return hash_bytes(path.read_bytes())


def git(root, *arguments):
    return subprocess.check_output(['git', *arguments], cwd=root)


def source_manifest(root):
    baseline_names = [Path(item.decode()).relative_to(APP).as_posix() for item in
                      git(root, 'ls-tree', '-rz', '--name-only', BASE_REV, str(APP)).split(b'\0') if item]
    tracked_names = [Path(item.decode()).relative_to(APP).as_posix() for item in
                     git(root, 'ls-files', '-z', '--', str(APP)).split(b'\0') if item]
    require(set(tracked_names) - set(baseline_names) == PREMIUM_ADDED,
            'Unexpected or missing files relative to approved backend')
    require(not set(baseline_names) - set(tracked_names), 'Approved backend file removed')
    files = {}
    for name in tracked_names:
        path = APP / name
        data = (root / path).read_bytes()
        if name in baseline_names and name not in REVIEWED_BACKEND_DELTAS:
            approved = git(root, 'show', f'{BASE_REV}:{path}')
            require(data == approved, f'Approved backend drift: {name}')
        files[name] = hash_bytes(data)
    lock = root / 'frontend/premium/package-lock.json'
    package = json.loads(lock.read_text())
    require(package['packages']['node_modules/react']['version'] == '19.3.1' and
            package['packages']['node_modules/vite']['version'] == '8.3.5',
            'React package lock pin drift')
    return {'schema': 1, 'approved_backend_commit': BASE_REV,
            'reviewed_backend_deltas': sorted(REVIEWED_BACKEND_DELTAS), 'base_image': BASE_IMAGE,
            'upstream_versions': VERSIONS, 'upstream_refs': REFS,
            'frontend_lock_sha256': hash_file(lock), 'files': dict(sorted(files.items()))}


def check_source(root, manifest):
    require(manifest == source_manifest(root), 'Full source/manifest mismatch')
    dockerfile = (root / 'infra/Dockerfile.single-stack-full').read_text()
    require(BASE_IMAGE in dockerfile and 'COPY --chown=frappe:frappe app/centrochange_core/ apps/centrochange_core/' in dockerfile,
            'Full app image recipe missing/pin drift')
    require('FROM centrochange-single:' not in dockerfile and
            'npm ci --ignore-scripts' in dockerfile and
            'verify_full_single_stack.py --image' in dockerfile,
            'Recipe uses partial overlay or misses build verification')
    require(all(ref in dockerfile for ref in REFS.values()), 'Upstream commit pin drift')
    require('CC_SINGLE_FULL_IMAGE' in (root / 'infra/compose.single-stack-full.yaml').read_text(),
            'Canonical Compose image pin missing')
    compose = (root / 'infra/compose.single-stack-full.yaml').read_text()
    require('name: centrochange-dev' in compose and
            'bench new-site' not in compose and 'bench migrate' not in compose and
            'build:' not in compose and 'configurator:' not in compose,
            'Canonical Compose is not the existing single Site topology')
    require(compose.count('memswap_limit:') == 9 and
            'aliases: [centrochange.local]' in compose,
            'Canonical Compose lost DEV cgroup limits or Site network alias')
    html = (root / APP / 'centrochange_core/www/premium.html').read_text()
    js = (root / APP / 'centrochange_core/public/premium/app.js').read_text()
    require('csrf-token' in html and 'premium/app.js' in html and
            all(item in js for item in ('Archivi', 'catalog.records', 'payments.records', 'profiles.patients')),
            'Production React/Frappe wiring missing')
    login_base = (root / APP / 'centrochange_core/templates/cc_web_base.html').read_text()
    login_brand = (root / APP / 'centrochange_core/operations/website_brand.py').read_text()
    require('css/login_v1.css' in login_base and 'js/login_v1.js' in login_base and
            'premium/logo.webp' in login_brand,
            'Native Frappe Login candidate assets missing')


def check_image(bench, manifest, built=False):
    app = bench / BENCH_APP
    for name, expected in manifest['files'].items():
        path = app / name
        require(path.is_file() and hash_file(path) == expected, f'Image app file missing/drifted: {name}')
    for name, expected in VERSIONS.items():
        path = bench / 'apps' / name / name / '__init__.py'
        require(path.is_file(), f'Upstream app missing: {name}')
        match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]+)', path.read_text(), re.M)
        require(match and match.group(1) == expected, f'Upstream version mismatch: {name}')
    for name, expected in REFS.items():
        actual = subprocess.check_output(['git', '-C', str(bench / 'apps' / name), 'rev-parse', 'HEAD'], text=True).strip()
        require(actual == expected, f'Upstream commit mismatch: {name}')
    for module in ENDPOINT_MODULES:
        imported = importlib.import_module('centrochange_core.' + module)
        require(Path(imported.__file__).resolve().is_relative_to((app / 'centrochange_core').resolve()),
                f'API imported outside full app: {module}')
    hooks = (app / 'centrochange_core/hooks.py').read_text()
    require('before_request' in hooks and 'permission_query_conditions' in hooks and
            'has_permission' in hooks, 'Security hooks missing')
    apps = (bench / 'sites/apps.txt').read_text().splitlines()
    require(apps == ['frappe', 'erpnext', 'healthcare', 'builder', 'centrochange_core'],
            'Bench app registration mismatch')
    if built:
        assets = json.loads((bench / 'assets/assets.json').read_text())
        required = {'desk.bundle.js', 'erpnext.bundle.js', 'healthcare.bundle.js',
                    'login.bundle.css', 'frappe-web.bundle.js'}
        require(required <= assets.keys(), f'Frappe asset map incomplete: {sorted(required - assets.keys())}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-manifest', action='store_true')
    parser.add_argument('--source', action='store_true')
    parser.add_argument('--image', type=Path, metavar='BENCH_ROOT')
    parser.add_argument('--built', action='store_true')
    args = parser.parse_args()
    require(sum(bool(x) for x in (args.write_manifest, args.source, args.image)) == 1,
            'Select one verification mode')
    if args.write_manifest:
        (ROOT / MANIFEST).write_text(json.dumps(source_manifest(ROOT), indent=2, sort_keys=True) + '\n')
        return
    manifest_path = (Path('/opt/cc148/full-single-stack-manifest.json') if args.image else ROOT / MANIFEST)
    manifest = json.loads(manifest_path.read_text())
    if args.source:
        check_source(ROOT, manifest)
        print('PASS full single-stack source parity')
    else:
        check_image(args.image.resolve(), manifest, built=args.built)
        print('PASS full single-stack image parity')


if __name__ == '__main__':
    try:
        main()
    except (KeyError, OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'FAIL full single-stack: {exc}', file=sys.stderr)
        sys.exit(1)
