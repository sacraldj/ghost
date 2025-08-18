#!/bin/bash

# GHOST Orchestrator Startup Script
# Скрипт запуска центрального оркестратора

set -e  # Выход при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
ORCHESTRATOR_SCRIPT="core/ghost_orchestrator.py"
PID_FILE="pids/ghost_orchestrator.pid"
LOG_FILE="logs/ghost_orchestrator.log"

# Функции для вывода
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция для проверки зависимостей
check_dependencies() {
    info "Проверка зависимостей..."
    
    # Проверка Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 не найден. Установите Python 3.8+ для продолжения."
        exit 1
    fi
    
    # Проверка версии Python
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    python_major=$(echo $python_version | cut -d. -f1)
    python_minor=$(echo $python_version | cut -d. -f2)
    
    if [[ $python_major -lt 3 ]] || [[ $python_major -eq 3 && $python_minor -lt 8 ]]; then
        error "Требуется Python 3.8+. Текущая версия: $python_version"
        exit 1
    fi
    
    # Проверка pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 не найден. Установите pip для продолжения."
        exit 1
    fi
    
    success "Зависимости проверены ✓"
}

# Функция для создания директорий
create_directories() {
    info "Создание необходимых директорий..."
    
    mkdir -p "$PROJECT_ROOT/pids"
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/config"
    mkdir -p "$PROJECT_ROOT/core"
    mkdir -p "$PROJECT_ROOT/utils"
    
    success "Директории созданы ✓"
}

# Функция для установки Python зависимостей
install_dependencies() {
    info "Установка Python зависимостей..."
    
    # Проверяем существование requirements.txt
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        pip3 install -r "$PROJECT_ROOT/requirements.txt"
    else
        # Устанавливаем базовые зависимости
        pip3 install asyncio aioredis psutil pyyaml aiofiles
    fi
    
    success "Зависимости установлены ✓"
}

# Функция для проверки переменных окружения
check_environment() {
    info "Проверка переменных окружения..."
    
    # Проверяем .env файл
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        source "$PROJECT_ROOT/.env"
        success ".env файл загружен ✓"
    else
        warning ".env файл не найден. Некоторые функции могут быть недоступны."
    fi
    
    # Проверяем критичные переменные
    if [[ -z "$SUPABASE_URL" ]]; then
        warning "SUPABASE_URL не установлен"
    fi
    
    if [[ -z "$SUPABASE_SECRET_KEY" ]]; then
        warning "SUPABASE_SECRET_KEY не установлен"
    fi
}

# Функция для проверки запущен ли оркестратор
is_orchestrator_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Запущен
        else
            # PID файл существует, но процесс не запущен
            rm -f "$PID_FILE"
            return 1  # Не запущен
        fi
    else
        return 1  # Не запущен
    fi
}

# Функция для остановки оркестратора
stop_orchestrator() {
    info "Остановка GHOST Orchestrator..."
    
    if is_orchestrator_running; then
        local pid=$(cat "$PID_FILE")
        
        # Graceful shutdown
        kill -TERM "$pid" 2>/dev/null
        
        # Ждём завершения (максимум 30 секунд)
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [[ $count -lt 30 ]]; do
            sleep 1
            ((count++))
        done
        
        # Если всё ещё запущен, принудительно убиваем
        if ps -p "$pid" > /dev/null 2>&1; then
            warning "Принудительное завершение процесса..."
            kill -KILL "$pid" 2>/dev/null
        fi
        
        rm -f "$PID_FILE"
        success "GHOST Orchestrator остановлен ✓"
    else
        warning "GHOST Orchestrator не запущен"
    fi
}

# Функция для запуска оркестратора
start_orchestrator() {
    info "Запуск GHOST Orchestrator..."
    
    if is_orchestrator_running; then
        warning "GHOST Orchestrator уже запущен (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    # Переходим в корневую директорию проекта
    cd "$PROJECT_ROOT"
    
    # Устанавливаем PYTHONPATH
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # Запуск оркестратора в фоне
    nohup python3 "$ORCHESTRATOR_SCRIPT" > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Сохраняем PID
    echo "$pid" > "$PID_FILE"
    
    # Проверяем что процесс запустился
    sleep 2
    if ps -p "$pid" > /dev/null 2>&1; then
        success "GHOST Orchestrator запущен (PID: $pid) ✓"
        info "Логи: $LOG_FILE"
        info "PID файл: $PID_FILE"
    else
        error "Ошибка запуска GHOST Orchestrator"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Функция для получения статуса
get_status() {
    if is_orchestrator_running; then
        local pid=$(cat "$PID_FILE")
        success "GHOST Orchestrator запущен (PID: $pid)"
        
        # Дополнительная информация о процессе
        if command -v ps &> /dev/null; then
            info "Информация о процессе:"
            ps -p "$pid" -o pid,ppid,pcpu,pmem,etime,cmd
        fi
        
        # Последние строки лога
        if [[ -f "$LOG_FILE" ]]; then
            info "Последние записи в логе:"
            tail -n 5 "$LOG_FILE"
        fi
    else
        warning "GHOST Orchestrator не запущен"
    fi
}

# Функция для рестарта
restart_orchestrator() {
    info "Перезапуск GHOST Orchestrator..."
    stop_orchestrator
    sleep 2
    start_orchestrator
}

# Функция для отображения логов в реальном времени
follow_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        info "Отслеживание логов (Ctrl+C для выхода):"
        tail -f "$LOG_FILE"
    else
        error "Лог файл не найден: $LOG_FILE"
    fi
}

# Функция для отображения помощи
show_help() {
    echo "GHOST Orchestrator Control Script"
    echo ""
    echo "Использование:"
    echo "  $0 [command]"
    echo ""
    echo "Команды:"
    echo "  start     - Запустить оркестратор"
    echo "  stop      - Остановить оркестратор"
    echo "  restart   - Перезапустить оркестратор"
    echo "  status    - Показать статус"
    echo "  logs      - Показать логи в реальном времени"
    echo "  install   - Установить зависимости"
    echo "  help      - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
}

# Основная логика
main() {
    local command="${1:-help}"
    
    case "$command" in
        "start")
            check_dependencies
            create_directories
            check_environment
            start_orchestrator
            ;;
        "stop")
            stop_orchestrator
            ;;
        "restart")
            check_dependencies
            create_directories
            check_environment
            restart_orchestrator
            ;;
        "status")
            get_status
            ;;
        "logs")
            follow_logs
            ;;
        "install")
            check_dependencies
            create_directories
            install_dependencies
            success "Установка завершена ✓"
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            error "Неизвестная команда: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Обработка сигналов
trap 'echo -e "\n${YELLOW}Прервано пользователем${NC}"; exit 130' INT TERM

# Запуск
main "$@"
