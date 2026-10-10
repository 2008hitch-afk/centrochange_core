#!/bin/sh
# Mission C isolated lab only: PID1 remains inert until the host verifies its
# exact cgroup RAM/swap cap and writes the service-specific release file.
set -eu

kind="$1"
shift
case "$kind" in
  frappe) original=/usr/local/bin/entrypoint.sh ;;
  database|redis) original=docker-entrypoint.sh ;;
  *) exit 73 ;;
esac

while [ ! -f /cc-bootstrap/release ]; do
  sleep 0.05
done

# Defense in depth inside the private cgroup namespace. The host gate remains
# authoritative, because this view alone cannot establish the ancestor chain.
if [ ! -r /sys/fs/cgroup/memory.max ] || [ ! -r /sys/fs/cgroup/memory.swap.max ]; then
  exit 74
fi
case "$(cat /sys/fs/cgroup/memory.max)" in
  max|'' ) exit 75 ;;
esac
if [ "$(cat /sys/fs/cgroup/memory.swap.max)" != 0 ]; then
  exit 76
fi
exec "$original" "$@"
