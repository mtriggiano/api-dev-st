#!/bin/bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Uso: $0 <system_user> [--clear]" >&2
  exit 1
fi

SYSTEM_USER="$1"
CLEAR_MODE="${2:-}"

run_privileged() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo -n "$@"
  fi
}

if ! [[ "$SYSTEM_USER" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]]; then
  echo "Nombre de usuario Linux inválido: $SYSTEM_USER" >&2
  exit 1
fi

PUBLIC_KEY=""
if [[ "$CLEAR_MODE" != "--clear" ]]; then
  if ! IFS= read -r PUBLIC_KEY; then
    echo "No se recibió clave SSH" >&2
    exit 1
  fi

  PUBLIC_KEY="$(echo "$PUBLIC_KEY" | sed 's/[[:space:]]*$//')"
  if [[ -z "$PUBLIC_KEY" ]]; then
    echo "Clave SSH vacía" >&2
    exit 1
  fi

  if [[ "$PUBLIC_KEY" != ssh-ed25519\ * && "$PUBLIC_KEY" != ssh-rsa\ * && "$PUBLIC_KEY" != ecdsa-sha2-* ]]; then
    echo "Formato de clave SSH inválido" >&2
    exit 1
  fi
fi

if ! id "$SYSTEM_USER" >/dev/null 2>&1; then
  run_privileged /usr/sbin/useradd -m -s /bin/bash "$SYSTEM_USER"
fi

USER_HOME="$(getent passwd "$SYSTEM_USER" | cut -d: -f6)"
if [[ -z "$USER_HOME" ]]; then
  echo "No se pudo determinar HOME de $SYSTEM_USER" >&2
  exit 1
fi

SSH_DIR="$USER_HOME/.ssh"
AUTHORIZED_KEYS="$SSH_DIR/authorized_keys"

run_privileged /usr/bin/mkdir -p "$SSH_DIR"
run_privileged /usr/bin/chown "$SYSTEM_USER:$SYSTEM_USER" "$SSH_DIR"
run_privileged /usr/bin/chmod 700 "$SSH_DIR"

if [[ "$CLEAR_MODE" == "--clear" ]]; then
  run_privileged /usr/bin/tee "$AUTHORIZED_KEYS" >/dev/null <<'EOF'
EOF
else
  printf '%s\n' "$PUBLIC_KEY" | run_privileged /usr/bin/tee "$AUTHORIZED_KEYS" >/dev/null
fi
run_privileged /usr/bin/chown "$SYSTEM_USER:$SYSTEM_USER" "$AUTHORIZED_KEYS"
run_privileged /usr/bin/chmod 600 "$AUTHORIZED_KEYS"

if [[ "$CLEAR_MODE" == "--clear" ]]; then
  echo "OK: clave SSH revocada para $SYSTEM_USER"
else
  echo "OK: clave SSH configurada para $SYSTEM_USER"
fi
