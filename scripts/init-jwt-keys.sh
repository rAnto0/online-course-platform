#!/usr/bin/env bash
set -euo pipefail

bits=2048
force=0
regenerated=0

usage() {
  cat <<'USAGE'
Usage: scripts/init-jwt-keys.sh [--force] [--bits N]

Generates RSA key pair for auth service and copies public key to course service.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      force=1
      shift
      ;;
    --bits)
      bits="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown аргумент: $1"
      usage
      exit 1
      ;;
  esac
done

if ! command -v openssl >/dev/null 2>&1; then
  echo "OpenSSL не найден. Установи openssl и повтори."
  exit 1
fi

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

auth_dir="$root_dir/microservices/auth/app/certs"
course_dir="$root_dir/microservices/course/app/core/certs"

private_key="$auth_dir/jwt-private.pem"
public_key="$auth_dir/jwt-public.pem"
course_public_key="$course_dir/jwt-public.pem"

mkdir -p "$auth_dir" "$course_dir"

if [[ -f "$private_key" || -f "$public_key" ]]; then
  if [[ "$force" -ne 1 ]]; then
    echo "Ключи уже существуют: $private_key или $public_key"
    echo "Ничего не делаю. Запусти с --force для пересоздания."
  else
    rm -f "$private_key" "$public_key"
    regenerated=1
  fi
fi

if [[ ! -f "$private_key" || ! -f "$public_key" ]]; then
  echo "Генерирую RSA ключи ($bits бит) для auth..."
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:"$bits" -out "$private_key"
  openssl rsa -in "$private_key" -pubout -out "$public_key"
  chmod 600 "$private_key"
  chmod 644 "$public_key"
  regenerated=1
fi

if [[ -f "$course_public_key" ]]; then
  if [[ "$force" -eq 1 || "$regenerated" -eq 1 ]]; then
    cp "$public_key" "$course_public_key"
    chmod 644 "$course_public_key"
    echo "Скопировал публичный ключ в course: $course_public_key"
  elif ! cmp -s "$public_key" "$course_public_key"; then
    cp "$public_key" "$course_public_key"
    chmod 644 "$course_public_key"
    echo "Публичный ключ в course обновлен: $course_public_key"
  else
    echo "Публичный ключ в course актуален: $course_public_key"
  fi
else
  cp "$public_key" "$course_public_key"
  chmod 644 "$course_public_key"
  echo "Скопировал публичный ключ в course: $course_public_key"
fi
