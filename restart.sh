#!/bin/bash
# Atajo rápido para reiniciar servicios
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

case "${1:-}" in
  "" )
    # Default: asegurar que los cambios locales se apliquen (build + restart)
    exec "$SCRIPT_DIR/update.sh" --local --non-interactive
    ;;
  update|--update|local-update|--local-update)
    exec "$SCRIPT_DIR/update.sh" --local --non-interactive
    ;;
  quick|--quick)
    shift
    exec "$SCRIPT_DIR/scripts/utils/restart-services.sh" all
    ;;
  status|s|backend|back|b|frontend|front|f|all|a)
    exec "$SCRIPT_DIR/scripts/utils/restart-services.sh" "$@"
    ;;
  *)
    echo "Uso: $0 [quick|update|backend|frontend|all|status]"
    echo "  (sin argumentos) = update local (build + restart)"
    exit 1
    ;;
esac
