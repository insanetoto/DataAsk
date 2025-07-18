#!/bin/bash

# DataAsk 一键启动脚本
# 使用方法: chmod +x start_dataask.sh && ./start_dataask.sh

echo "=== DataAsk 智能数据问答平台 启动脚本 ==="
echo "时间: $(date)"
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查Python环境
echo -e "${YELLOW}1. 检查Python环境...${NC}"
if ! conda info --envs | grep -q "DataAsk"; then
    echo -e "${RED}❌ conda环境 'DataAsk' 不存在${NC}"
    echo "请先创建conda环境: conda create -n DataAsk python=3.8"
    exit 1
else
    echo -e "${GREEN}✅ conda环境 'DataAsk' 已找到${NC}"
fi

# 激活conda环境
echo -e "${YELLOW}2. 激活conda环境...${NC}"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate DataAsk
echo -e "${GREEN}✅ 已激活DataAsk环境${NC}"

# 检查并启动后端
echo -e "${YELLOW}3. 启动后端服务...${NC}"
if pgrep -f "python app.py" > /dev/null; then
    echo -e "${GREEN}✅ 后端服务已在运行 (端口: 9000)${NC}"
else
    echo "正在启动后端服务..."
    nohup python app.py > backend.log 2>&1 &
    sleep 3
    if pgrep -f "python app.py" > /dev/null; then
        echo -e "${GREEN}✅ 后端服务启动成功 (端口: 9000)${NC}"
    else
        echo -e "${RED}❌ 后端服务启动失败${NC}"
        exit 1
    fi
fi

# 检查并启动前端
echo -e "${YELLOW}4. 启动前端服务...${NC}"
cd dataask_front
if pgrep -f "ng serve" > /dev/null; then
    echo -e "${GREEN}✅ 前端服务已在运行 (端口: 4200)${NC}"
else
    echo "正在启动前端服务..."
    nohup yarn start > ../frontend.log 2>&1 &
    sleep 5
    if pgrep -f "ng serve" > /dev/null; then
        echo -e "${GREEN}✅ 前端服务启动成功 (端口: 4200)${NC}"
    else
        echo -e "${RED}❌ 前端服务启动失败${NC}"
        echo "请检查 frontend.log 文件"
    fi
fi
cd ..

# 运行API测试
echo -e "${YELLOW}5. 运行API健康检查...${NC}"
sleep 2
health_check=$(curl -s http://localhost:9000/api/text2sql/health 2>/dev/null)
if echo "$health_check" | grep -q '"status": "healthy"'; then
    echo -e "${GREEN}✅ API服务正常${NC}"
else
    echo -e "${RED}❌ API服务异常${NC}"
    echo "响应: $health_check"
fi

echo ""
echo "=== 启动完成 ==="
echo -e "${GREEN}🎉 DataAsk 平台启动成功！${NC}"
echo ""
echo "📱 访问地址:"
echo -e "  • 前端界面: ${BLUE}http://localhost:4200${NC}"
echo -e "  • Text2SQL: ${BLUE}http://localhost:4200/ai-app/text2sql${NC}"
echo -e "  • 后端API: ${BLUE}http://localhost:9000${NC}"
echo ""
echo "🔧 管理工具:"
echo "  • 查看后端日志: tail -f backend.log"
echo "  • 查看前端日志: tail -f frontend.log"
echo "  • 运行API测试: ./test_vanna_api.sh"
echo "  • 停止所有服务: ./stop_dataask.sh"
echo ""
echo "👤 默认登录账户:"
echo "  • 用户名: admin"
echo "  • 密码: admin123"
echo ""
echo "✨ Text2SQL功能特性:"
echo "  • 智能自然语言转SQL"
echo "  • 实时SQL执行和结果展示"
echo "  • 对话式交互界面"
echo "  • 训练样本管理"
echo "  • 会话历史记录" 