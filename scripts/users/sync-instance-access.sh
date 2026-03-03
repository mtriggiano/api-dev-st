#!/bin/bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Uso: $0 <system_user> <prod_root> <dev_root> [instance_name ...]" >&2
  exit 1
fi

SYSTEM_USER="$1"
PROD_ROOT="$2"
DEV_ROOT="$3"
shift 3

run_privileged() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo "$@"
  fi
}

if ! [[ "$SYSTEM_USER" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]]; then
  echo "Nombre de usuario Linux inválido: $SYSTEM_USER" >&2
  exit 1
fi

if ! command -v setfacl >/dev/null 2>&1; then
  echo "setfacl no está instalado en el servidor" >&2
  exit 1
fi

if ! id "$SYSTEM_USER" >/dev/null 2>&1; then
  run_privileged useradd -m -s /bin/bash "$SYSTEM_USER"
fi

all_instance_dirs=()
for root in "$PROD_ROOT" "$DEV_ROOT"; do
  if [ -d "$root" ]; then
    while IFS= read -r -d '' dir; do
      all_instance_dirs+=("$dir")
    done < <(find "$root" -mindepth 1 -maxdepth 1 -type d -print0)

    # Acceso base para poder recorrer raíz de instancias
    run_privileged setfacl -m "u:$SYSTEM_USER:rx" "$root" || true
  fi
done

# Revocar accesos previos del usuario en todas las instancias
for dir in "${all_instance_dirs[@]}"; do
  run_privileged setfacl -R -x "u:$SYSTEM_USER" "$dir" 2>/dev/null || true
  run_privileged setfacl -R -x "d:u:$SYSTEM_USER" "$dir" 2>/dev/null || true
done

declare -A allowed_dirs
for instance_name in "$@"; do
  if ! [[ "$instance_name" =~ ^[A-Za-z0-9._-]+$ ]]; then
    continue
  fi

  for root in "$PROD_ROOT" "$DEV_ROOT"; do
    candidate="$root/$instance_name"
    if [ -d "$candidate" ]; then
      allowed_dirs["$candidate"]=1
    fi
  done
done

# Aplicar ACL solo en instancias permitidas
for dir in "${!allowed_dirs[@]}"; do
  run_privileged setfacl -R -m "u:$SYSTEM_USER:rwx" "$dir"
  run_privileged setfacl -R -m "d:u:$SYSTEM_USER:rwx" "$dir"
done

echo "OK: usuario $SYSTEM_USER sincronizado (${#allowed_dirs[@]} instancias)"
