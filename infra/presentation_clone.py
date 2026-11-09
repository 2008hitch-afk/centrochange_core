"""GitHub Actions only: fresh isolated Frappe/MariaDB presentation-load acceptance."""
import os
import subprocess
import sys
import test_audit09_isolated_clone as clone

if os.environ.get("GITHUB_ACTIONS") != "true" or not os.environ.get("RUNNER_TEMP"):
    raise RuntimeError("Presentation clone is CI-only.")
if os.environ.get("CC_CLONE_IMAGE") != "cc205-ci:local":
    raise RuntimeError("Must test the exact candidate image.")

clone.NET_NAME = "cc205-ci-net"
clone.SITES_VOLUME = "cc205-ci-sites"
clone.DB_CONTAINER = "cc205-ci-db"
clone.REDIS_CONTAINER = "cc205-ci-redis"
clone.BACKEND_CONTAINER = "cc205-ci-backend"
clone.FRONTEND_CONTAINER = "cc205-ci-frontend"

def bench(*args):
    return clone.run_cmd(["docker", "exec", clone.BACKEND_CONTAINER,
        "bench", "--site", clone.CLONE_SITE, *args])

try:
    clone.setup_clone(skip_uat_seed=True)
    bench("set-config", "cc_presentation_seed", "1")
    bench("set-config", "cc_presentation_intake", "1")
    bench("set-config", "cc_presentation_site", clone.CLONE_SITE)
    bench("set-config", "mute_emails", "1")
    bench("set-config", "cc_presentation_backup_sha256", "a" * 64)
    print(bench("execute", "centrochange_core.uat.presentation_acceptance.prepare"))
    print(bench("execute", "centrochange_core.uat.presentation_acceptance.run"))
    print(bench("execute", "centrochange_core.uat.presentation_seed.inspect"))
    # This CI clone has one additional patient created by presentation_acceptance.
    # Explicit flags prevent the destructive booking acceptance on shared sites.
    bench("set-config", "cc_director_clone_test", "1")
    bench("set-config", "cc_director_clone_ci", "1")
    from pathlib import Path
    director_test = Path(__file__).with_name('director_clone_acceptance.py').read_text()
    print(clone.run_cmd(["docker", "exec", "-i", "-w", "/home/frappe/frappe-bench",
                         clone.BACKEND_CONTAINER, "/home/frappe/frappe-bench/env/bin/python", "-"],
                        input_str=director_test))
finally:
    clone.cleanup()
