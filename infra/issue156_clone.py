"""CI-only fresh Frappe/MariaDB test, isolated from all existing environments."""
import os
import subprocess
import sys
import test_audit09_isolated_clone as clone

if os.environ.get('GITHUB_ACTIONS') != 'true' or not os.environ.get('RUNNER_TEMP'):
    raise RuntimeError('Run only on an ephemeral GitHub Actions runner')
if os.environ.get('CC_CLONE_IMAGE') != 'cc156-ci:local':
    raise RuntimeError('Candidate image required')
clone.NET_NAME = 'cc156-ci-net'
clone.SITES_VOLUME = 'cc156-ci-sites'
clone.DB_CONTAINER = 'cc156-ci-db'
clone.REDIS_CONTAINER = 'cc156-ci-redis'
clone.BACKEND_CONTAINER = 'cc156-ci-backend'
clone.FRONTEND_CONTAINER = 'cc156-ci-frontend'
try:
    clone.setup_clone()
    print(clone.run_cmd(['docker','exec',clone.BACKEND_CONTAINER,'bench','--site',clone.CLONE_SITE,
        'execute','centrochange_core.finance.operational_receipts_acceptance.run']))
    print(clone.run_cmd(['docker','exec',clone.BACKEND_CONTAINER,'bench','--site',clone.CLONE_SITE,
        'execute','centrochange_core.finance.operational_receipts_acceptance.concurrent']))
    subprocess.run([sys.executable, str(clone.ROOT_DIR / 'infra/issue156_http.py')], check=True)
finally:
    clone.cleanup()
