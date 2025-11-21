#!/bin/bash
# Atajo rápido para reiniciar servicios
exec "$(dirname "$0")/scripts/utils/restart-services.sh" "$@"
