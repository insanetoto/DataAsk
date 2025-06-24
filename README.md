# 洞察魔方 - 生成式AI应用管理平台

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey.svg)](https://github.com)

基于生成式AI的企业级智能应用管理平台。

## 📋 项目概况

**洞察魔方** 是一个现代化的全栈生成式AI应用管理平台，采用前后端分离架构，集成了先进的AI技术栈，为企业提供智能化的AI服务。项目具备完整的用户权限管理、多层级组织架构、License授权控制等企业级特性。

## ✨ 核心功能

### 🤖 智能AI引擎
- 🗣️ **自然语言交互**：支持中文自然语言查询
- 🔄 **自动SQL生成**：AI智能将问题转换为SQL语句
- 📊 **即时查询执行**：自动执行生成的SQL并返回结果
- 🎯 **高精度识别**：基于向量相似度的智能匹配
- 📚 **知识库管理**：支持DDL学习、文档训练
- 🎓 **自定义训练**：支持问题-SQL对自定义训练

### 🏢 企业级管理
- 👥 **用户权限管理**：完整的RBAC权限控制体系
- 🏗️ **组织架构管理**：多层级机构管理，支持树形结构
- 🔐 **License授权系统**：企业级功能授权与控制
- 📊 **工作空间**：数据分析工作台、报表管理、系统监控
- 🛡️ **安全保障**：JWT认证、数据加密、API权限控制

### 🚀 高性能架构
- ⚡ **Redis缓存**：智能缓存提升响应速度
- 🔄 **连接池管理**：数据库连接池优化
- 📈 **负载均衡**：支持多实例部署
- 📊 **监控日志**：完善的日志和监控体系
- 🐳 **容器化部署**：Docker容器化服务

### 🎨 现代化界面
- 📋 **API文档**：Swagger风格的接口文档
- 🔧 **在线测试**：支持接口在线调试
- 📱 **响应式设计**：Angular19 + ng-alain企业级UI
- 🎯 **用户友好**：直观的操作界面

---

## 🏗️ 技术架构

### 🎯 整体架构模式
```
前端层 (Angular) ↔ API网关 (Flask) ↔ 业务服务层 ↔ 数据存储层
```

### 📦 技术栈详解

#### 🔧 后端技术栈
- **🎯 框架**: Flask 2.3.3 + Python 3.8+
- **💾 数据库**: MySQL 8.0+ (主业务) + MySQL (AI专用)
- **🚀 缓存**: Redis 6.0+
- **🔍 向量存储**: ChromaDB 0.4.18
- **🗃️ ORM**: SQLAlchemy 2.0.23
- **🔐 认证**: JWT + bcrypt
- **📊 数据处理**: pandas + numpy
- **📈 可视化**: plotly + matplotlib

#### 🎨 前端技术栈  
- **⚡ 框架**: Angular 19.2.0
- **🎨 UI库**: ng-zorro-antd 19.2.1 + ng-alain 19.2.0
- **🔧 状态管理**: @delon系列
- **🛠️ 构建工具**: Angular CLI + yarn
- **💄 样式**: Less + 响应式设计

### 🏛️ 系统架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端表现层    │    │   API接口层     │    │   AI模型服务    │
│  (Angular)     │◄──►│   (Flask)       │◄──►│  (AI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   缓存服务层    │    │   向量数据库    │
                    │   (Redis)       │    │  (ChromaDB)     │
                    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   数据持久层    │
                    │   (MySQL)       │
                    └─────────────────┘
```

---

## 📐 应用架构设计

### 🔄 分层架构模式

#### 🏢 后端服务架构 (采用依赖注入模式)
- **🎯 应用层**: `app.py` - Flask应用工厂
- **🔌 API层**: `api/routes.py` - RESTful接口定义
- **⚙️ 服务层**: `service/` - 业务逻辑处理
- **💾 数据层**: `models/` + `tools/database.py` - 数据访问
- **🤖 AI引擎**: `AIEngine/` - AI服务封装
- **🛡️ 中间件**: `tools/` - 认证、缓存、License等

#### 🎨 前端模块架构
- **⚙️ 核心模块**: `src/app/core/` - 启动服务、拦截器、国际化
- **🎨 布局模块**: `src/app/layout/` - 基础布局、导航结构
- **🛣️ 路由模块**: `src/app/routes/` - 功能模块路由
- **🔧 共享模块**: `src/app/shared/` - 公共组件、工具

---

## 💼 业务架构

### 🎯 核心业务模块

#### 1. 🤖 AI智能问答引擎
- **❓ 问答处理**: 自然语言转SQL，智能查询执行
- **📚 知识库管理**: DDL学习、文档训练、向量存储
- **🔗 数据源管理**: 多数据库连接配置与管理  
- **🧠 大模型管理**: AI模型参数调优与版本管理

#### 2. 👥 用户权限管理
- **🏢 组织架构**: 多层级机构管理，支持树形结构
- **👤 用户管理**: 用户CRUD、角色分配、权限继承
- **🎭 角色管理**: 角色定义、权限绑定、等级控制
- **🔐 权限控制**: 细粒度API权限、菜单权限、数据权限

#### 3. 📊 工作空间
- **🛠️ 工作台**: 数据分析工作区，查询历史管理
- **📋 报表管理**: 报表创建、模板管理、定时生成
- **📈 系统监控**: 性能监控、日志分析、告警管理

#### 4. ⚙️ 系统管理
- **🔑 License授权**: 企业级许可证管理、功能控制
- **⚙️ 系统配置**: 应用参数配置、环境管理
- **📝 日志审计**: 操作日志记录、安全审计

---

## 📁 代码结构分析

### 🗂️ 后端代码结构
```
DataAsk/
├── 📄 app.py                     # Flask应用入口
├── ⚙️ config.py                  # 配置管理
├── 📋 requirements.txt           # Python依赖
├── 🔌 api/                       # API接口层
│   └── routes.py                 # RESTful路由定义
├── 🤖 AIEngine/                  # AI引擎模块
│   ├── __init__.py               # 模块初始化
│   └── vanna_service.py          # Vanna AI服务
├── 📊 models/                    # 数据模型层
│   ├── base.py                   # 基础模型类
│   ├── user.py                   # 用户模型
│   ├── organization.py           # 组织模型
│   ├── role.py                   # 角色模型
│   └── permission.py             # 权限模型
├── ⚙️ service/                   # 业务服务层
│   ├── user_service.py           # 用户服务
│   ├── organization_service.py   # 组织服务
│   ├── role_service.py           # 角色服务
│   └── permission_service.py     # 权限服务
├── 🛠️ tools/                     # 工具层
│   ├── database.py               # 数据库服务
│   ├── redis_service.py          # Redis缓存服务
│   ├── auth_middleware.py        # 认证中间件
│   ├── license_middleware.py     # License中间件
│   └── di_container.py           # 依赖注入容器
└── 🗄️ sql/                       # 数据库脚本
    ├── init.sql                  # 初始化脚本
    └── menu.sql                  # 菜单数据
```

### 🎨 前端代码结构
```
dataask_front/src/app/
├── ⚙️ app.config.ts               # 应用配置
├── 🏗️ core/                      # 核心模块
│   ├── startup/                  # 启动服务
│   ├── net/                      # 网络拦截器
│   └── i18n/                     # 国际化
├── 🎨 layout/                     # 布局模块
│   ├── basic/                    # 基础布局
│   ├── blank/                    # 空白布局
│   └── passport/                 # 认证布局
├── 🛣️ routes/                     # 业务路由
│   ├── 🤖 ai-engine/             # AI引擎模块
│   │   ├── ask-data/             # 问答组件
│   │   ├── knowledge-base/       # 知识库组件
│   │   ├── datasource/           # 数据源组件
│   │   └── llmmanage/            # 大模型管理
│   ├── ⚙️ sys/                    # 系统管理
│   │   ├── user/                 # 用户管理
│   │   ├── role/                 # 角色管理
│   │   ├── permission/           # 权限管理
│   │   └── org/                  # 组织管理
│   └── 📊 workspace/              # 工作空间
│       ├── workbench/            # 工作台
│       ├── report/               # 报表管理
│       └── monitor/              # 系统监控
└── 🔧 shared/                     # 共享模块
    ├── shared.module.ts          # 共享模块定义
    └── utils/                    # 工具函数
```

---

## 🛡️ 安全架构

### 🔐 认证授权体系
1. **🎫 JWT认证**: 无状态令牌认证，支持访问令牌和刷新令牌
2. **🎭 角色权限**: 完整的RBAC权限模型，支持角色继承
3. **🔒 API权限**: 接口级细粒度权限控制，支持动态权限验证

### 🔒 数据安全
1. **🗄️ 双数据库隔离**: 业务数据与AI训练数据完全分离
2. **🛡️ SQL注入防护**: 全面使用参数化查询，防止SQL注入
3. **🔐 密码加密**: bcrypt强哈希算法，支持盐值加密
4. **📝 会话管理**: Redis安全令牌存储，支持会话过期控制

### 🔍 安全审计
1. **📋 操作日志**: 完整的用户操作审计日志
2. **🚨 异常监控**: 实时安全事件监控和告警
3. **🔐 权限变更**: 权限变更历史追踪和审计

---

## 🚀 部署架构

### 🐳 容器化部署
- **🗄️ MySQL**: Docker容器化数据库服务，支持主从复制
- **🚀 Redis**: Docker容器化缓存服务，支持集群模式
- **⚙️ 应用配置**: 通过env_init.bak进行环境配置管理

### 🖥️ 环境要求
- **🐍 后端环境**: conda环境管理 + pip包管理 + 清华源镜像
- **🎨 前端环境**: yarn构建工具 + 淘宝源镜像
- **🌐 网络配置**: 后端固定9000端口，前端4200端口

### 📊 性能优化
1. **🚀 缓存策略**: 多层缓存架构，查询结果缓存
2. **🔄 连接池**: 数据库连接池优化，减少连接开销
3. **📈 负载均衡**: 支持多实例横向扩展
4. **📊 监控体系**: 完善的性能监控和告警机制

---

## 🎯 设计特色

### 💡 架构优势
1. **🔧 微服务化**: 前后端分离，服务高度解耦
2. **📈 可扩展性**: 模块化设计，支持功能和性能扩展
3. **⚡ 高性能**: Redis缓存 + 连接池 + 查询优化
4. **🏢 企业级**: License管控 + 完善权限体系 + 审计日志
5. **🤖 AI驱动**: 智能SQL生成，自然语言数据交互

### 🔧 技术亮点
1. **💉 依赖注入**: 完整的DI容器，服务解耦便于测试
2. **📋 标准化响应**: 统一的API返回格式，错误处理机制
3. **🗄️ 双数据库**: 业务数据与AI训练数据物理隔离
4. **🚀 缓存策略**: 智能缓存，支持查询缓存和SQL缓存
5. **🎨 现代前端**: Angular19 + ng-alain企业级UI框架

---

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
- Node.js 18+
- 4GB+ 内存

#### 2. 克隆项目
```bash
git clone https://github.com/insanetoto/DataAsk.git
cd DataAsk
```

#### 3. 后端环境配置
```bash
# 创建conda虚拟环境
conda create -n DataAsk python=3.12
conda activate DataAsk

# 安装Python依赖（使用清华源）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### 4. 前端环境配置
```bash
cd dataask_front

# 配置yarn淘宝源
yarn config set registry https://registry.npmmirror.com

# 安装前端依赖
yarn install
```

#### 5. 配置环境变量
```bash
# 复制配置文件
cp env.example .env

# 编辑配置文件，设置数据库和API密钥
vim .env
```

#### 6. 数据库设置
```sql
-- 创建主业务数据库
CREATE DATABASE dataask CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建Vanna AI数据库
CREATE DATABASE vanna CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户并授权
CREATE USER 'dataask'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON dataask.* TO 'dataask'@'localhost';
GRANT ALL PRIVILEGES ON vanna.* TO 'dataask'@'localhost';
FLUSH PRIVILEGES;

-- 导入初始化数据
mysql -u dataask -p dataask < sql/init.sql
```

#### 7. 启动应用
```bash
# 启动后端服务（端口9000）
python app.py

# 启动前端服务（端口4200）
cd dataask_front
yarn start
```

### 应用访问地址
- **前端应用**: http://localhost:4200
- **后端API**: http://localhost:9000
- **API文档**: http://localhost:9000/


## 📡 API接口

### 核心接口

#### 🤖 智能问答
```bash
POST /api/ask
Content-Type: application/json

{
  "question": "查询客户总数"
}
```

#### 🔧 生成SQL
```bash
POST /api/generate_sql
Content-Type: application/json

{
  "question": "统计各部门员工数量"
}
```

#### 🎓 模型训练
```bash
POST /api/train
Content-Type: application/json

{
  "question": "查询用户信息",
  "sql": "SELECT * FROM users"
}
```

### 系统管理

#### 🔍 健康检查
```bash
GET /api/health
```

#### 🔐 用户认证
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "用户名",
  "password": "密码"
}
```

### 详细API文档
更多接口详情请参考 [API文档](产品api说明.md)

---

## 🔧 开发指南

### 环境配置
- 后端使用conda环境管理，激活命令：`conda activate DataAsk`
- 前端使用yarn包管理器，推荐使用淘宝源
- 数据库服务通过Docker运行，配置见env_init.bak

### 开发规范
1. **代码规范**: 遵循PEP8（后端）和Angular Style Guide（前端）
2. **分支管理**: 使用Git Flow工作流
3. **测试覆盖**: 单元测试覆盖率要求80%以上
4. **文档更新**: 代码变更需同步更新相关文档

### 调试模式
```bash
# 后端调试模式
export FLASK_ENV=development
export FLASK_DEBUG=true
python app.py

# 前端调试模式
cd dataask_front
yarn start --configuration development
```

---

## 📝 文档资源

- [启动说明](启动说明.md) - 详细的启动配置指南
- [API文档](产品api说明.md) - 完整的接口文档
- [图标指南](docs/icons-guide.md) - 项目图标使用说明
- [测试文档](dataask_front/docs/) - 前后端测试指南

---

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 开源协议

本项目基于 MIT 协议开源 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 📞 联系方式

- 项目主页: https://github.com/insanetoto/DataAsk
- 问题反馈: https://github.com/insanetoto/DataAsk/issues
- 技术支持: 请通过GitHub Issues联系

---