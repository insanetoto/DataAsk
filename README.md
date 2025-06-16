# 百惟数问 - 智能数据问答平台

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey.svg)](https://github.com)

基于AI的企业级智能数据问答平台，支持自然语言查询数据库，自动生成SQL并执行查询。

## ✨ 核心功能

### 🤖 智能问答
- 🗣️ **自然语言交互**：支持中文自然语言查询
- 🔄 **自动SQL生成**：AI智能将问题转换为SQL语句
- 📊 **即时查询执行**：自动执行生成的SQL并返回结果
- 🎯 **高精度识别**：基于向量相似度的智能匹配

### 🎓 模型训练
- 📚 **知识库构建**：支持数据库Schema自动学习
- 🔧 **自定义训练**：支持问题-SQL对自定义训练
- 📖 **文档训练**：支持业务文档和DDL语句训练
- 🚀 **增量学习**：持续优化模型准确性

### 🔒 License授权系统
- 🏢 **机构授权管理**：支持机构名称、时间、用户数限制
- 🛡️ **功能权限控制**：细粒度功能特性控制
- ⏰ **时间验证**：自动检查License过期状态
- 🔐 **强加密保护**：PBKDF2+Fernet双重加密

### 🚀 高性能架构
- ⚡ **Redis缓存**：智能缓存提升响应速度
- 🔄 **连接池管理**：数据库连接池优化
- 📈 **负载均衡**：支持多实例部署
- 📊 **监控日志**：完善的日志和监控体系

### 🎨 现代化界面
- 📋 **API文档**：Swagger风格的接口文档
- 🔧 **在线测试**：支持接口在线调试
- 📱 **响应式设计**：适配多种设备屏幕
- 🎯 **用户友好**：直观的操作界面

## 🏗️ 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   Flask API     │    │   AI模型服务    │
│  (HTML/JS)     │◄──►│   (REST API)    │◄──►│  (Vanna AI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Redis缓存     │    │   向量数据库    │
                    │   (查询缓存)    │    │  (ChromaDB)     │
                    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   MySQL数据库   │
                    │   (业务数据)    │
                    └─────────────────┘
```

### 核心技术栈
- **🐍 后端框架**：Flask + Python 3.8+
- **🤖 AI模型**：Vanna AI + 阿里云百炼(Qwen)
- **💾 数据库**：MySQL 8.0+
- **🚀 缓存**：Redis 6.0+
- **🔍 向量存储**：ChromaDB
- **🔐 安全**：cryptography + PBKDF2

## 🚀 快速开始

### 方式一：一键部署脚本（推荐）

支持 Ubuntu 20.04+ 和 CentOS 7+ 系统：

```bash
# 下载部署脚本
wget https://raw.githubusercontent.com/insanetoto/DataAsk/main/deploy.sh

# 给脚本执行权限
chmod +x deploy.sh

# 执行一键部署（需要root权限）
sudo ./deploy.sh --repo https://github.com/insanetoto/DataAsk.git
```

### 方式二：手动安装

#### 1. 环境要求
- Python 3.8+
- MySQL 8.0+
- Redis 6.0+
- 4GB+ 内存

#### 2. 克隆项目
```bash
git clone https://github.com/insanetoto/DataAsk.git
cd DataAsk
```

#### 3. 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装Python依赖
pip install -r requirements.txt
```

#### 4. 配置环境
```bash
# 复制配置文件
cp env.example .env

# 编辑配置文件，设置数据库和API密钥
vim .env
```

#### 5. 数据库设置
```sql
-- 创建数据库
CREATE DATABASE llmstudy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'dataask'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON llmstudy.* TO 'dataask'@'localhost';
FLUSH PRIVILEGES;
```

#### 6. 启动应用
```bash
python app.py
```

应用将运行在 `http://localhost:8080`

## 🔑 License管理

### 生成License
License管理工具需要单独提供，包含以下功能：
- 生成加密的License文件
- 验证License有效性和过期时间
- 查看License详细信息
- 支持机构名称、用户数量、功能权限控制

请联系项目维护者获取License管理工具。

### License功能控制
- `ai_query`: 智能问答功能
- `sql_generation`: SQL生成功能  
- `data_visualization`: 数据可视化
- `cache_enabled`: 缓存功能
- `training_enabled`: 模型训练功能

## 📡 API接口

### 核心接口

#### 🤖 智能问答
```bash
POST /api/v1/ask
Content-Type: application/json

{
  "question": "查询客户总数"
}
```

#### 🔧 生成SQL
```bash
POST /api/v1/generate_sql
Content-Type: application/json

{
  "question": "统计各部门员工数量"
}
```

#### 🎓 模型训练
```bash
POST /api/v1/train
Content-Type: application/json

{
  "question": "查询用户信息",
  "sql": "SELECT * FROM users"
}
```

### 系统管理

#### 🔍 健康检查
```bash
GET /api/v1/health
```

#### 🔐 License状态
```bash
GET /api/v1/license/status
```

完整API文档请访问：`http://localhost:8080`

## 🛠️ 部署配置

### 生产环境部署

#### 使用Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 使用Supervisor进程管理
```ini
[program:dataask]
command=/opt/dataask/venv/bin/python app.py
directory=/opt/dataask
user=dataask
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dataask.log
```

#### 使用Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "app.py"]
```

## 📊 监控与日志

### 应用日志
- 位置：`app.log`
- 级别：INFO, WARNING, ERROR
- 轮转：自动按大小轮转

### 性能监控
- API响应时间
- 数据库查询性能
- Redis缓存命中率
- License使用情况

### 健康检查
```bash
# 检查应用状态
curl http://localhost:8080/api/v1/health

# 检查License状态
curl http://localhost:8080/api/v1/license/status
```

## 🤝 开发指南

### 项目结构
```
DataAsk/
├── app.py                 # 应用主入口
├── config.py              # 配置管理
├── requirements.txt       # 依赖清单
├── env.example           # 环境配置模板
├── deploy.sh             # 一键部署脚本
├── api/                  # API路由
│   ├── __init__.py
│   └── routes.py
├── services/             # 核心服务
│   ├── __init__.py
│   ├── database.py       # 数据库服务
│   ├── redis_service.py  # Redis服务
│   └── vanna_service.py  # AI服务
├── middleware/           # 中间件
│   ├── __init__.py
│   └── license_middleware.py  # License中间件
└── README.md
```

### 贡献指南
1. Fork 项目
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交Pull Request

### 编码规范
- 遵循PEP 8 Python编码规范
- 使用中文注释和文档
- 编写单元测试
- 保持代码简洁可读

## 🐛 故障排除

### 常见问题

#### 1. License验证失败
```bash
# 检查License文件是否存在
ls -la license.key

# 如果没有License文件，请联系项目维护者获取
# License管理工具单独提供，不包含在开源代码中
```

#### 2. 数据库连接失败
```bash
# 检查数据库状态
systemctl status mysql

# 测试连接
mysql -h localhost -u dataask -p llmstudy
```

#### 3. Redis连接失败
```bash
# 检查Redis状态
systemctl status redis

# 测试连接
redis-cli ping
```

#### 4. AI模型调用失败
- 检查API Key配置
- 验证网络连接
- 查看错误日志

### 日志查看
```bash
# 查看应用日志
tail -f app.log

# 查看系统日志
journalctl -u dataask -f

# 查看Nginx日志
tail -f /var/log/nginx/access.log
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Vanna AI](https://vanna.ai/) - 智能SQL生成
- [阿里云百炼](https://bailian.aliyun.com/) - AI模型服务
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [Flask](https://flask.palletsprojects.com/) - Web框架

## 📞 联系我们

- 📧 邮箱：support@dataask.com
- 🌐 官网：https://dataask.com
- 📱 微信：DataAsk2024

---

⭐ 如果这个项目对您有帮助，请给我们一个Star！ 