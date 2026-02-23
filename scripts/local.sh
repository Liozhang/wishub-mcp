#!/bin/bash

# WisHub MCP 本地启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${YELLOW}ℹ${NC} $1"; }
print_step() { echo -e "${BLUE}▶${NC} $1"; }

# 配置
VENV_DIR=".venv"
PYTHON_VERSION="3.11"
API_PORT="${API_PORT:-8000}"

# 检查 Python 版本
check_python() {
    print_step "检查 Python 版本..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 未安装"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python 版本: $PYTHON_VERSION"
}

# 创建虚拟环境
create_venv() {
    print_step "创建虚拟环境..."
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        print_success "虚拟环境创建成功: $VENV_DIR"
    else
        print_info "虚拟环境已存在: $VENV_DIR"
    fi
}

# 激活虚拟环境
activate_venv() {
    print_step "激活虚拟环境..."
    source "$VENV_DIR/bin/activate"
    print_success "虚拟环境已激活"
}

# 安装依赖
install_deps() {
    print_step "安装 Python 依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "依赖安装完成"
}

# 安装开发依赖
install_dev_deps() {
    print_step "安装开发依赖..."
    pip install pytest pytest-asyncio pytest-cov black ruff mypy httpx
    print_success "开发依赖安装完成"
}

# 检查环境变量
check_env() {
    print_step "检查环境变量..."
    if [ ! -f ".env" ]; then
        print_info "创建 .env 文件..."
        cp .env.example .env
        print_success "请编辑 .env 文件配置您的环境变量"
    else
        print_info "环境文件已存在: .env"
    fi
}

# 运行测试
run_tests() {
    print_step "运行测试..."
    pytest tests/ -v
    print_success "测试完成"
}

# 启动服务器
start_server() {
    print_step "启动开发服务器..."
    print_info "访问: http://localhost:$API_PORT"
    print_info "API 文档: http://localhost:$API_PORT/docs"
    print_info "按 Ctrl+C 停止服务器"
    uvicorn wishub_mcp.server.app:app --host 0.0.0.0 --port "$API_PORT" --reload
}

# 清理
clean() {
    print_step "清理虚拟环境..."
    rm -rf "$VENV_DIR"
    rm -rf __pycache__
    rm -rf .pytest_cache
    rm -rf .coverage
    rm -rf htmlcov
    print_success "清理完成"
}

# 主函数
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║     WisHub MCP - 本地开发环境                           ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    case "${1:-setup}" in
        setup)
            check_python
            create_venv
            activate_venv
            install_deps
            install_dev_deps
            check_env
            print_success "本地环境设置完成！"
            echo ""
            echo "运行以下命令启动服务器:"
            echo "  ./scripts/local.sh start"
            echo ""
            echo "运行测试:"
            echo "  ./scripts/local.sh test"
            ;;
        start)
            check_python
            activate_venv
            check_env
            start_server
            ;;
        test)
            check_python
            activate_venv
            run_tests
            ;;
        install)
            check_python
            activate_venv
            install_deps
            ;;
        install-dev)
            check_python
            activate_venv
            install_dev_deps
            ;;
        clean)
            clean
            ;;
        *)
            echo "用法: $0 {setup|start|test|install|install-dev|clean}"
            echo ""
            echo "命令:"
            echo "  setup        设置本地开发环境（首次使用）"
            echo "  start        启动开发服务器"
            echo "  test         运行测试"
            echo "  install      安装依赖"
            echo "  install-dev  安装开发依赖"
            echo "  clean        清理虚拟环境"
            exit 1
            ;;
    esac
}

main "$@"
