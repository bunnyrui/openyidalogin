#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVER_KEYS="$ROOT/license-server/keys"
CLIENT_KEYS="$ROOT/electron-client/keys"
mkdir -p "$SERVER_KEYS" "$CLIENT_KEYS"
openssl genrsa -out "$SERVER_KEYS/private.pem" 2048
openssl rsa -in "$SERVER_KEYS/private.pem" -pubout -out "$SERVER_KEYS/public.pem"
cp "$SERVER_KEYS/public.pem" "$CLIENT_KEYS/public.pem"
echo "OK: 已生成 RS256 密钥"
echo "服务端私钥: $SERVER_KEYS/private.pem"
echo "服务端公钥: $SERVER_KEYS/public.pem"
echo "客户端公钥: $CLIENT_KEYS/public.pem"
echo "注意：private.pem 只能保存在服务端，不能发给客户。"
