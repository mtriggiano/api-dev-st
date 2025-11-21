#!/bin/bash

# 🔄 Script para reiniciar Backend y Frontend de API-DEV
# Uso: ./restart-services.sh [backend|frontend|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para reiniciar el backend
restart_backend() {
    echo -e "${BLUE}🔄 Reiniciando Backend...${NC}"
    
    # Buscar el PID del proceso master de gunicorn
    BACKEND_PID=$(ps aux | grep "gunicorn.*api-dev.*wsgi:app" | grep -v grep | awk 'NR==1{print $2}')
    
    if [ -z "$BACKEND_PID" ]; then
        echo -e "${RED}❌ Backend no está corriendo${NC}"
        echo -e "${YELLOW}💡 Iniciando backend...${NC}"
        cd "$PROJECT_ROOT/backend"
        nohup venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 \
            --timeout 600 \
            --max-requests 1000 \
            --max-requests-jitter 50 \
            --limit-request-line 8190 \
            --limit-request-field_size 8190 \
            --access-logfile "$PROJECT_ROOT/logs/gunicorn-access.log" \
            --error-logfile "$PROJECT_ROOT/logs/gunicorn-error.log" \
            --log-level info \
            wsgi:app > /dev/null 2>&1 &
        sleep 2
        echo -e "${GREEN}✅ Backend iniciado${NC}"
    else
        echo -e "${YELLOW}📍 PID del backend: $BACKEND_PID${NC}"
        kill -HUP "$BACKEND_PID"
        sleep 1
        echo -e "${GREEN}✅ Backend reiniciado${NC}"
    fi
    
    # Verificar que esté corriendo
    if ps -p "$BACKEND_PID" > /dev/null 2>&1 || pgrep -f "gunicorn.*api-dev" > /dev/null; then
        echo -e "${GREEN}✅ Backend está corriendo correctamente${NC}"
        # Mostrar últimas líneas del log
        echo -e "${BLUE}📝 Últimas líneas del log:${NC}"
        tail -5 "$PROJECT_ROOT/logs/gunicorn-error.log" 2>/dev/null || echo "No hay logs disponibles"
    else
        echo -e "${RED}❌ Error: Backend no pudo iniciarse${NC}"
        return 1
    fi
}

# Función para reiniciar el frontend
restart_frontend() {
    echo -e "${BLUE}🔄 Reiniciando Frontend...${NC}"
    
    # Detener frontend si está corriendo
    FRONTEND_PIDS=$(ps aux | grep "npm.*dev" | grep -v grep | awk '{print $2}')
    
    if [ -n "$FRONTEND_PIDS" ]; then
        echo -e "${YELLOW}🛑 Deteniendo frontend...${NC}"
        echo "$FRONTEND_PIDS" | xargs -r kill -9 2>/dev/null
        sleep 1
        echo -e "${GREEN}✅ Frontend detenido${NC}"
    fi
    
    # Iniciar frontend
    echo -e "${YELLOW}🚀 Iniciando frontend...${NC}"
    cd "$PROJECT_ROOT/frontend"
    nohup npm run dev > /tmp/frontend-dev.log 2>&1 &
    sleep 3
    
    # Verificar que esté corriendo
    if ps aux | grep "npm.*dev" | grep -v grep > /dev/null; then
        echo -e "${GREEN}✅ Frontend iniciado correctamente${NC}"
        echo -e "${BLUE}📝 Últimas líneas del log:${NC}"
        tail -10 /tmp/frontend-dev.log | grep -E "VITE|Local|Network" || tail -5 /tmp/frontend-dev.log
    else
        echo -e "${RED}❌ Error: Frontend no pudo iniciarse${NC}"
        echo -e "${YELLOW}📝 Log completo:${NC}"
        cat /tmp/frontend-dev.log
        return 1
    fi
}

# Función para mostrar estado
show_status() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 Estado de Servicios API-DEV${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Backend
    if pgrep -f "gunicorn.*api-dev" > /dev/null; then
        BACKEND_PID=$(pgrep -f "gunicorn.*api-dev" | head -1)
        echo -e "${GREEN}✅ Backend: Corriendo (PID: $BACKEND_PID)${NC}"
        echo -e "   Puerto: 127.0.0.1:5000"
    else
        echo -e "${RED}❌ Backend: No está corriendo${NC}"
    fi
    
    # Frontend
    if pgrep -f "npm.*dev" > /dev/null; then
        FRONTEND_PID=$(pgrep -f "npm.*dev" | head -1)
        echo -e "${GREEN}✅ Frontend: Corriendo (PID: $FRONTEND_PID)${NC}"
        echo -e "   URL: http://localhost:5173/"
    else
        echo -e "${RED}❌ Frontend: No está corriendo${NC}"
    fi
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Menú principal
case "${1:-all}" in
    backend|back|b)
        restart_backend
        ;;
    frontend|front|f)
        restart_frontend
        ;;
    all|a|"")
        restart_backend
        echo ""
        restart_frontend
        ;;
    status|s)
        show_status
        ;;
    *)
        echo -e "${YELLOW}Uso: $0 [backend|frontend|all|status]${NC}"
        echo ""
        echo "Opciones:"
        echo "  backend, back, b    - Reiniciar solo el backend"
        echo "  frontend, front, f  - Reiniciar solo el frontend"
        echo "  all, a              - Reiniciar ambos (default)"
        echo "  status, s           - Mostrar estado de servicios"
        echo ""
        echo "Ejemplos:"
        echo "  $0              # Reinicia ambos"
        echo "  $0 backend      # Solo backend"
        echo "  $0 frontend     # Solo frontend"
        echo "  $0 status       # Ver estado"
        exit 1
        ;;
esac

echo ""
show_status
