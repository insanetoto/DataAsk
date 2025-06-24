#!/bin/bash
# 工作流引擎快速安装脚本

set -e

echo "🚀 开始安装工作流引擎..."

# 检查系统要求
echo "📋 检查系统要求..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建目录结构..."
mkdir -p airflow/{dags,logs,plugins,config}
mkdir -p docker
mkdir -p config

# 设置环境变量
echo "🔧 设置环境变量..."
export AIRFLOW_UID=$(id -u)
echo "AIRFLOW_UID=$AIRFLOW_UID" > .env

# 创建Airflow数据库初始化脚本
echo "📄 创建Airflow数据库初始化脚本..."
cat > sql/airflow_init.sql << 'EOF'
-- 创建Airflow数据库
CREATE DATABASE IF NOT EXISTS airflow DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 授权用户访问权限
GRANT ALL PRIVILEGES ON airflow.* TO 'dataask'@'%';
FLUSH PRIVILEGES;
EOF

# 安装Python依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

# 创建工作流数据表
echo "🗄️ 创建数据表..."
python -c "
from tools.database import get_database_service
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.getcwd())

try:
    db_service = get_database_service()
    with open('sql/workflow_tables.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割SQL语句并执行
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    with db_service.get_session() as session:
        for statement in statements:
            if statement and not statement.startswith('--'):
                session.execute(statement)
        session.commit()
    
    print('✅ 数据表创建成功')
except Exception as e:
    print(f'❌ 数据表创建失败: {e}')
    sys.exit(1)
"

# 启动Airflow服务
echo "🚀 启动Airflow服务..."
docker-compose -f docker/docker-compose.airflow.yml up -d

# 等待服务启动
echo "⏳ 等待Airflow服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ Airflow WebServer 启动成功"
    echo "🌐 访问地址: http://localhost:8080"
    echo "👤 用户名: admin"
    echo "🔑 密码: admin"
else
    echo "❌ Airflow服务启动失败，请检查日志"
    docker-compose -f docker/docker-compose.airflow.yml logs
fi

# 创建示例工作流
echo "📝 创建示例工作流..."
python -c "
import sys
import os
sys.path.insert(0, os.getcwd())

from service.workflow_service import get_workflow_service

workflow_service = get_workflow_service()

# 创建示例工作流
sample_workflow = {
    'name': '数据分析示例流程',
    'description': '演示数据ETL和分析的完整流程',
    'category': 'data_processing',
    'creator_id': 1,
    'steps': [
        {
            'name': '数据提取',
            'type': 'sql',
            'config': {
                'query': 'SELECT * FROM sys_user LIMIT 100',
                'connection_id': 'mysql_default'
            }
        },
        {
            'name': '数据清洗',
            'type': 'python',
            'config': {
                'script': '''
def clean_data(data):
    # 数据清洗逻辑
    print(f\"正在清洗 {len(data)} 条数据\")
    return data
'''
            }
        },
        {
            'name': '数据分析',
            'type': 'python',
            'config': {
                'script': '''
def analyze_data(data):
    # 数据分析逻辑
    print(f\"正在分析 {len(data)} 条数据\")
    return {\"total\": len(data), \"status\": \"completed\"}
'''
            }
        }
    ]
}

try:
    result = workflow_service.create_workflow(sample_workflow)
    if result['success']:
        print('✅ 示例工作流创建成功')
    else:
        print(f'❌ 示例工作流创建失败: {result.get(\"error\")}')
except Exception as e:
    print(f'❌ 示例工作流创建失败: {e}')
"

echo ""
echo "🎉 工作流引擎安装完成！"
echo ""
echo "📋 下一步："
echo "1. 访问 http://localhost:8080 查看Airflow管理界面"
echo "2. 访问 http://localhost:4200 查看前端工作流管理"
echo "3. 查看文档了解如何创建自定义工作流"
echo ""
echo "📚 相关文档："
echo "- Airflow文档: https://airflow.apache.org/docs/"
echo "- API文档: http://localhost:9000/api/workflow"
echo ""
echo "🔧 常用命令："
echo "- 查看日志: docker-compose -f docker/docker-compose.airflow.yml logs"
echo "- 停止服务: docker-compose -f docker/docker-compose.airflow.yml down"
echo "- 重启服务: docker-compose -f docker/docker-compose.airflow.yml restart" 