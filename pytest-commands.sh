#!/bin/bash

# Script para ejecutar comandos de pytest comúnmente usados
# Uso: chmod +x pytest-commands.sh && ./pytest-commands.sh <comando>

set -e  # Salir si hay algún error

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo -e "${BLUE}╔═════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     PYTEST - Comandos Disponibles para CertyPro Backend     ║${NC}"
    echo -e "${BLUE}╚═════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Uso: ./pytest-commands.sh <comando>${NC}"
    echo ""
    echo -e "${YELLOW}Comandos disponibles:${NC}"
    echo ""
    echo "  ${GREEN}all${NC}               - Ejecutar todas las pruebas"
    echo "  ${GREEN}integration${NC}       - Ejecutar solo pruebas de integración"
    echo "  ${GREEN}unit${NC}              - Ejecutar solo pruebas unitarias"
    echo "  ${GREEN}events${NC}            - Ejecutar pruebas de la app 'events'"
    echo "  ${GREEN}coverage${NC}          - Ejecutar con reporte de cobertura"
    echo "  ${GREEN}coverage-html${NC}     - Generar reporte HTML de cobertura"
    echo "  ${GREEN}coverage-sonar${NC}    - Generar cobertura para SonarQube"
    echo "  ${GREEN}verbose${NC}           - Ejecutar con output detallado"
    echo "  ${GREEN}last-failed${NC}       - Ejecutar solo tests que fallaron la última vez"
    echo "  ${GREEN}pdb${NC}               - Ejecutar con debugger en caso de error"
    echo "  ${GREEN}watch${NC}             - Ejecutar en modo watch (ejecuta al guardar archivos)"
    echo "  ${GREEN}collect${NC}           - Listar todos los tests disponibles"
    echo "  ${GREEN}parallel${NC}          - Ejecutar tests en paralelo"
    echo "  ${GREEN}help${NC}              - Mostrar esta ayuda"
    echo ""
}

# Validar que Docker está corriendo
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Error: Docker no está en ejecución${NC}"
        echo "Por favor, inicia Docker Desktop o ejecuta: sudo systemctl start docker"
        exit 1
    fi
}

# Ejecutar comando
case "$1" in
    all)
        echo -e "${BLUE}▶ Ejecutando todas las pruebas...${NC}"
        check_docker
        pytest -v
        ;;
    
    integration)
        echo -e "${BLUE}▶ Ejecutando pruebas de INTEGRACIÓN...${NC}"
        check_docker
        pytest -m integration -v
        ;;
    
    unit)
        echo -e "${BLUE}▶ Ejecutando pruebas UNITARIAS...${NC}"
        pytest -m unit -v
        ;;
    
    events)
        echo -e "${BLUE}▶ Ejecutando pruebas de la app 'events'...${NC}"
        check_docker
        pytest events/ -v
        ;;
    
    coverage)
        echo -e "${BLUE}▶ Ejecutando pruebas con cobertura (terminal)...${NC}"
        check_docker
        pytest --cov=. --cov-report=term-missing --cov-report=xml:coverage.xml
        echo -e "${GREEN}✓ Reporte XML generado: coverage.xml${NC}"
        ;;
    
    coverage-html)
        echo -e "${BLUE}▶ Generando reporte HTML de cobertura...${NC}"
        check_docker
        pytest --cov=. --cov-report=html:htmlcov --cov-report=term-missing
        echo -e "${GREEN}✓ Reporte HTML generado: htmlcov/index.html${NC}"
        echo -e "${BLUE}Abre el archivo en tu navegador para ver el reporte${NC}"
        ;;
    
    coverage-sonar)
        echo -e "${BLUE}▶ Generando cobertura para SonarQube...${NC}"
        check_docker
        pytest --cov=. --cov-report=xml:coverage.xml -v
        echo -e "${GREEN}✓ Archivo listo para SonarQube: coverage.xml${NC}"
        ;;
    
    verbose)
        echo -e "${BLUE}▶ Ejecutando pruebas en modo VERBOSE...${NC}"
        check_docker
        pytest -vv --tb=long -s
        ;;
    
    last-failed)
        echo -e "${BLUE}▶ Ejecutando solo pruebas que fallaron...${NC}"
        check_docker
        pytest --lf -v
        ;;
    
    pdb)
        echo -e "${BLUE}▶ Ejecutando con debugger (pdb) activado...${NC}"
        check_docker
        pytest --pdb -x
        ;;
    
    watch)
        echo -e "${BLUE}▶ Ejecutando en modo WATCH...${NC}"
        echo -e "${YELLOW}Nota: Requiere pytest-watch. Instala con: pip install pytest-watch${NC}"
        check_docker
        ptw -- -v --tb=short
        ;;
    
    collect)
        echo -e "${BLUE}▶ Listando todos los tests disponibles...${NC}"
        pytest --collect-only -q
        ;;
    
    parallel)
        echo -e "${BLUE}▶ Ejecutando tests en PARALELO...${NC}"
        echo -e "${YELLOW}Nota: Requiere pytest-xdist. Instala con: pip install pytest-xdist${NC}"
        check_docker
        pytest -n auto -v
        ;;
    
    help|"")
        usage
        ;;
    
    *)
        echo -e "${RED}❌ Comando desconocido: $1${NC}"
        echo ""
        usage
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✓ Completado${NC}"
