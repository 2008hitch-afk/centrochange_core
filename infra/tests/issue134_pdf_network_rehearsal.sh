#!/usr/bin/env bash
# Isolated print-asset topology rehearsal. No DEV container, Site or volume is mounted.
set -euo pipefail
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
image=centrochange-single:issue134-it-0e6299d
expected=sha256:a681d9a22a8198cec60469564e4a3c919a1318d824a16e53010b33d4879719d5
[[ $(docker image inspect "$image" --format '{{.Id}}') == "$expected" ]]
network="cc-issue134-pdf-$RANDOM-$$"
frontend="${network}-front"
cleanup() {
  if [[ ${test_passed:-0} != 1 ]]; then docker logs "$frontend" 2>&1 | tail -20 >&2 || true; fi
  docker rm -f "$frontend" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
}
trap cleanup EXIT
docker network create --internal "$network" >/dev/null
docker run -d --name "$frontend" --network "$network" \
  --network-alias centrochange.local --read-only --memory 256m --memory-swap 256m \
  --tmpfs /etc/nginx/conf.d:mode=0777 --tmpfs /var/cache/nginx:mode=0777 \
  --tmpfs /var/lib/nginx:mode=0777 --tmpfs /run:mode=0777 --tmpfs /tmp:mode=1777 \
  -v "$repo_dir/infra/issue134_frontend_pdf.conf.template:/home/frappe/cc-pdf-template:ro" \
  -e BACKEND=127.0.0.1:8000 -e SOCKETIO=127.0.0.1:9000 \
  -e NGINX_LISTEN_PORT=8080 -e FRAPPE_SITE_NAME_HEADER=centrochange.local \
  -e UPSTREAM_REAL_IP_ADDRESS=127.0.0.1 -e UPSTREAM_REAL_IP_HEADER=X-Forwarded-For \
  -e UPSTREAM_REAL_IP_RECURSIVE=off -e CLIENT_MAX_BODY_SIZE=50m \
  -e PROXY_READ_TIMEOUT=120 \
  -e 'CC_ENV_KEYS=$BACKEND $SOCKETIO $NGINX_LISTEN_PORT $FRAPPE_SITE_NAME_HEADER $UPSTREAM_REAL_IP_ADDRESS $UPSTREAM_REAL_IP_HEADER $UPSTREAM_REAL_IP_RECURSIVE $CLIENT_MAX_BODY_SIZE $PROXY_READ_TIMEOUT' \
  --entrypoint sh "$image" -c \
  'envsubst "$CC_ENV_KEYS" < /home/frappe/cc-pdf-template > /etc/nginx/conf.d/frappe.conf && nginx -t && exec nginx -g "daemon off;"' >/dev/null

# Use the real pinned wkhtmltopdf binary. The HTML requests one local CSS
# asset through each of the three internal listeners; missing assets make the
# renderer fail. No host port is published and no shared project network exists.
docker run --rm --network "$network" --read-only --memory 256m --memory-swap 256m \
  --tmpfs /tmp:mode=1777 --entrypoint sh "$image" -c '
  set -eu
  asset=$(find /home/frappe/frappe-bench/sites/assets/frappe/dist/css -maxdepth 1 -name "desk.bundle.*.css" | head -1)
  asset=${asset#*/sites}
  for port in 80 8080 8082; do
    count=0
    until env/bin/python -c "import sys,urllib.request; r=urllib.request.urlopen(sys.argv[1],timeout=2); assert r.status == 200 and r.read(32)" "http://centrochange.local:$port$asset" >/dev/null 2>&1; do
      count=$((count+1)); [ "$count" -lt 15 ] || exit 1; sleep 1
    done
  done
  printf "%s\n" "<html><head><link rel=stylesheet href=http://centrochange.local:80$asset><link rel=stylesheet href=http://centrochange.local:8082$asset></head><body>Fattura di prova</body></html>" |
    wkhtmltopdf --quiet - /tmp/cc-issue134-test.pdf
  head -c 5 /tmp/cc-issue134-test.pdf | grep -q "%PDF-"
  echo PDF_NETWORK_REHEARSAL_PASS
  '
test_passed=1
