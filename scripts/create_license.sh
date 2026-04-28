#!/usr/bin/env bash
set -e
SERVER=${SERVER:-http://127.0.0.1:8000}
USER=${ADMIN_USERNAME:-admin}
PASS=${ADMIN_PASSWORD:-admin123456}
TOKEN=$(curl -s "$SERVER/api/v1/admin/login" -H 'Content-Type: application/json' -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")
curl -s "$SERVER/api/v1/admin/licenses" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"count":1,"productCode":"default","plan":"standard","maxDevices":1,"expireDays":365,"note":"manual"}' | python3 -m json.tool
