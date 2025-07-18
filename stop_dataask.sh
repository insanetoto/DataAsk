#!/bin/bash

# DataAsk 停止服务脚本
# 使用方法: chmod +x stop_dataask.sh && ./stop_dataask.sh

echo "=== DataAsk 停止服务脚本 ==="
echo "时间: $(date)"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 停止后端服务
echo -e "${YELLOW}1. 停止后端服务...${NC}"
backend_pids=$(pgrep -f "python app.py")
if [ -n "$backend_pids" ]; then
    echo "找到后端进程: $backend_pids"
    pkill -f "python app.py"
    sleep 2
    if pgrep -f "python app.py" > /dev/null; then
        echo -e "${RED}❌ 后端服务停止失败，强制终止...${NC}"
        pkill -9 -f "python app.py"
    else
        echo -e "${GREEN}✅ 后端服务已停止${NC}"
    fi
else
    echo -e "${GREEN}✅ 后端服务未运行${NC}"
fi

# 停止前端服务
echo -e "${YELLOW}2. 停止前端服务...${NC}"
frontend_pids=$(pgrep -f "ng serve")
if [ -n "$frontend_pids" ]; then
    echo "找到前端进程: $frontend_pids"
    pkill -f "ng serve"
    sleep 2
    if pgrep -f "ng serve" > /dev/null; then
        echo -e "${RED}❌ 前端服务停止失败，强制终止...${NC}"
        pkill -9 -f "ng serve"
    else
        echo -e "${GREEN}✅ 前端服务已停止${NC}"
    fi
else
    echo -e "${GREEN}✅ 前端服务未运行${NC}"
fi

# 停止yarn相关进程
echo -e "${YELLOW}3. 停止yarn相关进程...${NC}"
yarn_pids=$(pgrep -f "yarn")
if [ -n "$yarn_pids" ]; then
    echo "找到yarn进程: $yarn_pids"
    pkill -f "yarn"
    sleep 1
    echo -e "${GREEN}✅ yarn进程已停止${NC}"
else
    echo -e "${GREEN}✅ yarn进程未运行${NC}"
fi

# 清理临时文件
echo -e "${YELLOW}4. 清理临时文件...${NC}"
if [ -f "backend.log" ]; then
    rm backend.log
    echo "✅ 已清理 backend.log"
fi
if [ -f "frontend.log" ]; then
    rm frontend.log
    echo "✅ 已清理 frontend.log"
fi

echo ""
echo "=== 停止完成 ==="
echo -e "${GREEN}🎉 所有DataAsk服务已停止！${NC}"
echo ""
echo "📊 服务状态:"
echo -e "  • 后端服务 (9000端口): ${RED}已停止${NC}"
echo -e "  • 前端服务 (4200端口): ${RED}已停止${NC}"
echo ""
echo "🔧 重新启动:"
echo "  • 运行: ./start_dataask.sh" 