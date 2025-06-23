#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查服务状态
check_service() {
    local service_name=$1
    local port=$2
    if nc -z localhost $port >/dev/null 2>&1; then
        print_message "$GREEN" "✓ $service_name 服务正在运行 (端口 $port)"
        return 0
    else
        print_message "$RED" "✗ $service_name 服务未运行 (端口 $port)"
        return 1
    fi
}

# 检查环境文件
check_env_file() {
    if [ ! -f .env ]; then
        print_message "$YELLOW" "未找到 .env 文件，正在从 env.example 创建..."
        cp env.example .env
        print_message "$GREEN" "✓ 已创建 .env 文件，请检查并修改配置"
    fi
}

# 检查数据库服务
check_database() {
    print_message "$YELLOW" "正在检查 MySQL 服务..."
    if ! check_service "MySQL" 3306; then
        print_message "$RED" "请确保 MySQL 服务已启动"
        exit 1
    fi
}

# 检查Redis服务
check_redis() {
    print_message "$YELLOW" "正在检查 Redis 服务..."
    if ! check_service "Redis" 6379; then
        print_message "$RED" "请确保 Redis 服务已启动"
        exit 1
    fi
}

# 检查Python环境
check_python_env() {
    print_message "$YELLOW" "正在检查 Python 环境..."
    if ! command -v conda &> /dev/null; then
        print_message "$RED" "未找到 conda 命令，请确保已安装 Anaconda 或 Miniconda"
        exit 1
    fi
    
    # 激活 conda 环境
    print_message "$YELLOW" "正在激活 DataAsk 环境..."
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate DataAsk
    
    if [ $? -ne 0 ]; then
        print_message "$RED" "激活 DataAsk 环境失败"
        exit 1
    fi
}

# 启动后端服务
start_backend() {
    print_message "$YELLOW" "正在启动后端服务..."
    
    # 检查端口是否被占用
    if check_service "Backend" 9000; then
        print_message "$YELLOW" "后端服务已在运行"
        return
    fi
    
    # 启动 Flask 应用
    export FLASK_APP=app.py
    export FLASK_ENV=development
    flask run --host=0.0.0.0 --port=9000 &
    
    # 等待服务启动
    sleep 2
    if check_service "Backend" 9000; then
        print_message "$GREEN" "✓ 后端服务启动成功"
    else
        print_message "$RED" "✗ 后端服务启动失败"
        exit 1
    fi
}

# 主函数
main() {
    print_message "$GREEN" "=== DataAsk 服务启动脚本 ==="
    
    # 检查各项服务和环境
    check_env_file
    check_database
    check_redis
    check_python_env
    
    # 启动服务
    start_backend
    
    print_message "$GREEN" "=== 所有服务启动完成 ==="
    print_message "$GREEN" "后端服务地址: http://localhost:9000"
}

# 执行主函数
main 