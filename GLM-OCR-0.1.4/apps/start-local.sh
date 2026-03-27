#!/bin/bash

# 本地启动 frontend 和 backend 项目的脚本
# 使用 Python 启动 backend，使用 pnpm 启动 frontend

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    本地启动 Frontend 和 Backend     ${NC}"
echo -e "${BLUE}========================================${NC}"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 函数：检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ 错误: 未找到 $1，请先安装${NC}"
        exit 1
    fi
}

# 检查必要的命令
echo -e "\n${YELLOW}检查依赖...${NC}"
check_command python3
check_command pnpm

# 函数：启动 backend
start_backend() {
    echo -e "\n${GREEN}[1/2] 启动 Backend...${NC}"
    cd "$SCRIPT_DIR/backend"

    # 检查是否存在虚拟环境
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}未找到虚拟环境，正在创建...${NC}"
        python3 -m venv .venv
    fi

    # 激活虚拟环境
    source .venv/bin/activate

    # 安装依赖（如果需要）
    if [ ! -f ".venv/bin/uvicorn" ] || [ "pyproject.toml" -nt ".venv/bin/uvicorn" ]; then
        echo -e "${YELLOW}安装 Backend 依赖...${NC}"
        pip install -e .
    fi

    # 启动 backend
    echo -e "${GREEN}启动 Backend 服务...${NC}"
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$SCRIPT_DIR/.backend.pid"
    echo -e "${GREEN}✓ Backend 已启动 (PID: $BACKEND_PID)${NC}"
}

# 函数：启动 frontend
start_frontend() {
    echo -e "\n${GREEN}[2/2] 启动 Frontend...${NC}"
    cd "$SCRIPT_DIR/frontend"

    # 安装依赖（如果需要）
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}安装 Frontend 依赖...${NC}"
        pnpm install
    fi

    # 启动 frontend
    echo -e "${GREEN}启动 Frontend 开发服务器...${NC}"
    pnpm dev --host 0.0.0.0 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$SCRIPT_DIR/.frontend.pid"
    echo -e "${GREEN}✓ Frontend 已启动 (PID: $FRONTEND_PID)${NC}"
}

# 主执行流程
start_backend
start_frontend

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 所有服务已成功启动！${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Frontend:${NC} http://localhost:5173"
echo -e "${YELLOW}Backend:${NC}  http://localhost:8000"
echo -e "${YELLOW}API Docs:${NC} http://localhost:8000/docs"
echo -e "\n${YELLOW}进程 ID 已保存到：${NC}"
echo -e "  Backend:  $SCRIPT_DIR/.backend.pid"
echo -e "  Frontend: $SCRIPT_DIR/.frontend.pid"
echo -e "\n${YELLOW}停止服务命令：${NC}"
echo -e "  kill \$(cat $SCRIPT_DIR/.backend.pid)"
echo -e "  kill \$(cat $SCRIPT_DIR/.frontend.pid)"
echo -e "  或使用: pkill -f 'uvicorn|pnpm dev'"
echo -e "${BLUE}========================================${NC}"

# 等待用户按键退出
echo -e "\n${YELLOW}按 Ctrl+C 停止所有服务${NC}"
# 保持脚本运行，等待 Ctrl+C
trap "echo -e '\n${RED}正在停止所有服务...${NC}'; kill \$(cat $SCRIPT_DIR/.backend.pid) 2>/dev/null || true; kill \$(cat $SCRIPT_DIR/.frontend.pid) 2>/dev/null || true; rm -f $SCRIPT_DIR/.backend.pid $SCRIPT_DIR/.frontend.pid; echo -e '${GREEN}所有服务已停止${NC}'; exit 0" INT TERM

# 保持脚本运行
wait
