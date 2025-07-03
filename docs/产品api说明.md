# DataAsk API 文档

## 目录
1. [认证相关接口](#认证相关接口)
   - [用户登录](#用户登录)
   - [刷新令牌](#刷新令牌)
   - [用户登出](#用户登出)
   - [获取个人资料](#获取个人资料)
   - [获取个人权限](#获取个人权限)
2. [用户管理接口](#用户管理接口)
   - [创建用户](#创建用户)
   - [获取用户信息](#获取用户信息)
   - [获取用户列表](#获取用户列表)
   - [更新用户信息](#更新用户信息)
   - [删除用户](#删除用户)
3. [组织机构接口](#组织机构接口)
   - [创建组织](#创建组织)
   - [获取组织列表](#获取组织列表)
   - [获取组织详情](#获取组织详情)
   - [更新组织信息](#更新组织信息)
   - [删除组织](#删除组织)
4. [角色权限接口](#角色权限接口)
   - [创建角色](#创建角色)
   - [获取角色列表](#获取角色列表)
   - [获取角色详情](#获取角色详情)
   - [更新角色信息](#更新角色信息)
   - [删除角色](#删除角色)
   - [分配权限](#分配权限)
   - [获取权限列表](#获取权限列表)
5. [数据分析接口](#数据分析接口)
   - [获取数据概览](#获取数据概览)
   - [查询数据](#查询数据)
   - [导出数据](#导出数据)

## 认证相关接口

### 用户登录

**接口说明：** 用户登录接口，返回访问令牌和刷新令牌

- **URL:** `/api/auth/login`
- **方法:** `POST`
- **请求头：** `Content-Type: application/json`
- **请求体：**
```json
{
    "username": "用户编码",
    "password": "密码"
}
```

**成功响应：**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

**curl示例：**
```bash
curl -X POST http://localhost:9000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test001",
    "password": "test123"
  }'
```

### 刷新令牌

**接口说明：** 使用刷新令牌获取新的访问令牌

- **URL:** `/api/auth/refresh`
- **方法:** `POST`
- **请求头：** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <refresh_token>`

**成功响应：**
```json
{
  "code": 200,
  "message": "令牌刷新成功",
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

**curl示例：**
```bash
curl -X POST http://localhost:9000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 用户登出

**接口说明：** 注销用户登录，撤销所有令牌

- **URL:** `/api/auth/logout`
- **方法:** `POST`
- **请求头：** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`

**成功响应：**
```json
{
  "code": 200,
  "message": "登出成功"
}
```

**curl示例：**
```bash
curl -X POST http://localhost:9000/api/auth/logout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 获取个人资料

**接口说明：** 获取当前登录用户的个人资料

- **URL:** `/api/auth/profile`
- **方法:** `GET`
- **请求头：** 
  - `Authorization: Bearer <access_token>`

**成功响应：**
```json
{
  "success": true,
  "data": {
    "id": 6,
    "name": "测试用户",
    "avatar": "",
    "email": "",
    "role_code": "NORMAL_USER",
    "org_code": "050101",
    "permissions": []
  }
}
```

**curl示例：**
```bash
curl -X GET http://localhost:9000/api/auth/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 获取个人权限

**接口说明：** 获取当前登录用户的权限列表

- **URL:** `/api/auth/permissions`
- **方法:** `GET`
- **请求头：** 
  - `Authorization: Bearer <access_token>`

**成功响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "permission_code": "VIEW_DASHBOARD",
      "permission_name": "查看仪表盘",
      "api_path": "/api/dashboard",
      "api_method": "GET",
      "resource_type": "menu",
      "description": "查看仪表盘权限",
      "status": 1
    }
  ]
}
```

**curl示例：**
```bash
curl -X GET http://localhost:9000/api/auth/permissions \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 用户管理接口

### 创建用户

**接口说明：** 创建新用户（需要管理员权限）

- **URL:** `/api/users`
- **方法:** `POST`
- **请求头：** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`
- **请求体：**
```json
{
    "user_code": "test001",
    "username": "测试用户",
    "password": "test123",
    "org_code": "050101",
    "role_id": 3,
    "phone": "13800138001",
    "address": "测试地址"
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "用户创建成功",
  "data": {
    "id": 6,
    "user_code": "test001",
    "username": "测试用户",
    "org_code": "050101",
    "role_id": 3,
    "phone": "13800138001",
    "address": "测试地址",
    "status": 1
  }
}
```

**curl示例：**
```bash
curl -X POST http://localhost:9000/api/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "user_code": "test001",
    "username": "测试用户",
    "password": "test123",
    "org_code": "050101",
    "role_id": 3,
    "phone": "13800138001",
    "address": "测试地址"
  }'
```

### 获取用户列表

**接口说明：** 获取用户列表，支持分页和筛选

- **URL:** `/api/users`
- **方法:** `GET`
- **请求头：** 
  - `Authorization: Bearer <access_token>`
- **查询参数：**
  - `page`: 页码（默认1）
  - `page_size`: 每页数量（默认10）
  - `status`: 用户状态（可选）
  - `org_code`: 机构编码（可选）
  - `role_level`: 角色级别（可选）
  - `keyword`: 搜索关键词（可选）

**成功响应：**
```json
{
  "success": true,
  "data": {
    "list": [
      {
        "id": 6,
        "user_code": "test001",
        "username": "测试用户",
        "org_code": "050101",
        "org_name": "广州供电局",
        "role_code": "NORMAL_USER",
        "role_name": "普通用户",
        "status": 1
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total": 1,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

**curl示例：**
```bash
# 基础查询
curl -X GET "http://localhost:9000/api/users" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 带筛选条件的查询
curl -X GET "http://localhost:9000/api/users?page=1&page_size=10&status=1&org_code=050101" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 组织机构接口

### 创建组织

**接口说明：** 创建新的组织机构（需要管理员权限）

- **URL:** `/api/organizations`
- **方法:** `POST`
- **请求头：** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`
- **请求体：**
```json
{
    "org_code": "050102",
    "org_name": "深圳供电局",
    "parent_code": "0501",
    "org_level": 2,
    "description": "深圳供电局",
    "status": 1
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "组织创建成功",
  "data": {
    "id": 7,
    "org_code": "050102",
    "org_name": "深圳供电局",
    "parent_code": "0501",
    "org_level": 2,
    "description": "深圳供电局",
    "status": 1
  }
}
```

**curl示例：**
```bash
curl -X POST http://localhost:9000/api/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "org_code": "050102",
    "org_name": "深圳供电局",
    "parent_code": "0501",
    "org_level": 2,
    "description": "深圳供电局",
    "status": 1
  }'
```

### 获取组织列表

**接口说明：** 获取组织机构列表，支持树形结构

- **URL:** `/api/organizations`
- **方法:** `GET`
- **请求头：** 
  - `Authorization: Bearer <access_token>`
- **查询参数：**
  - `type`: 返回类型（tree/list，默认tree）
  - `status`: 状态（可选）
  - `parent_code`: 父级编码（可选）

**成功响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "org_code": "0501",
      "org_name": "广东省电力公司",
      "parent_code": "0",
      "org_level": 1,
      "status": 1,
      "children": [
        {
          "id": 2,
          "org_code": "050101",
          "org_name": "广州供电局",
          "parent_code": "0501",
          "org_level": 2,
          "status": 1
        }
      ]
    }
  ]
}
```

**curl示例：**
```bash
# 获取树形结构
curl -X GET "http://localhost:9000/api/organizations?type=tree" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 获取列表结构
curl -X GET "http://localhost:9000/api/organizations?type=list&parent_code=0501" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 角色权限接口

### 创建角色

**接口说明：** 创建新角色（需要超级管理员权限）

- **URL:** `/api/roles`
- **方法:** `POST`
- **请求头：** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`
- **请求体：**
```json
{
    "role_code": "DEPT_MANAGER",
    "role_name": "部门经理",
    "role_level": 2,
    "description": "部门管理员角色",
    "status": 1
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "角色创建成功",
  "data": {
    "id": 4,
    "role_code": "DEPT_MANAGER",
    "role_name": "部门经理",
    "role_level": 2,
    "description": "部门管理员角色",
    "status": 1
  }
}
```

**curl示例：**
```bash
curl -X POST http://localhost:9000/api/roles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "role_code": "DEPT_MANAGER",
    "role_name": "部门经理",
    "role_level": 2,
    "description": "部门管理员角色",
    "status": 1
  }'
```

### 分配权限

**接口说明：** 为角色分配权限（需要超级管理员权限）

- **URL:** `/api/roles/{role_id}/permissions`
- **方法:** `POST`
- **请求头：** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`
- **请求体：**
```json
{
    "permission_ids": [1, 2, 3, 4]
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "权限分配成功"
}
```

**curl示例：**
```bash
curl -X POST http://localhost:9000/api/roles/4/permissions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "permission_ids": [1, 2, 3, 4]
  }'
```

## 数据分析接口

### 获取数据概览

**接口说明：** 获取数据分析概览信息

- **URL:** `/api/analytics/overview`
- **方法:** `GET`
- **请求头：** 
  - `Authorization: Bearer <access_token>`
- **查询参数：**
  - `start_date`: 开始日期（可选）
  - `end_date`: 结束日期（可选）
  - `org_code`: 机构编码（可选）

**成功响应：**
```json
{
  "success": true,
  "data": {
    "total_users": 100,
    "active_users": 80,
    "total_organizations": 50,
    "data_points": 10000,
    "charts": {
      "user_trend": [],
      "org_distribution": [],
      "data_statistics": []
    }
  }
}
```

**curl示例：**
```bash
# 基础查询
curl -X GET "http://localhost:9000/api/analytics/overview" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 带时间范围的查询
curl -X GET "http://localhost:9000/api/analytics/overview?start_date=2025-01-01&end_date=2025-12-31&org_code=050101" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 查询数据

**接口说明：** 按条件查询分析数据

- **URL:** `/api/analytics/query`
- **方法:** `POST`
- **请求头：** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`
- **请求体：**
```json
{
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "org_codes": ["050101", "050102"],
    "metrics": ["user_count", "data_volume"],
    "dimensions": ["org", "date"],
    "filters": {
        "status": 1
    }
}
```

**成功响应：**
```json
{
  "success": true,
  "data": {
    "results": [],
    "summary": {
      "total": 0,
      "aggregations": {}
    }
  }
}
```

**curl示例：**
```bash
curl -X POST http://localhost:9000/api/analytics/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "org_codes": ["050101", "050102"],
    "metrics": ["user_count", "data_volume"],
    "dimensions": ["org", "date"],
    "filters": {
      "status": 1
    }
  }'
```

## 注意事项

1. 所有需要认证的接口都必须在请求头中携带有效的访问令牌
2. 访问令牌有效期为30分钟，过期后需要使用刷新令牌获取新的访问令牌
3. 非超级管理员只能访问同机构及下级机构的数据
4. 用户管理、组织管理相关接口需要管理员权限（角色级别 ≤ 2）
5. 角色权限管理相关接口需要超级管理员权限（角色级别 = 1）
6. 所有删除操作均为软删除，只是将状态设置为禁用（status = 0）
7. 创建和更新用户时，密码会自动进行加密存储
8. 数据分析接口的响应时间可能较长，建议适当设置超时时间
9. 所有时间相关的字段均使用UTC时间，前端需要根据用户时区进行转换
10. 分页接口默认每页显示10条数据，最大支持每页100条

## 使用说明

1. 在使用curl命令之前，请确保：
   - 已经安装了curl工具
   - 将示例中的localhost:9000替换为实际的服务器地址
   - 将示例中的token（eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...）替换为实际的token

2. Windows系统下使用curl时：
   - 使用双引号替换单引号
   - 使用 ^ 替换 \ 作为换行符
   - 例如：
   ```bash
   curl -X POST http://localhost:9000/api/auth/login ^
   -H "Content-Type: application/json" ^
   -d "{\"username\":\"test001\",\"password\":\"test123\"}"
   ```

3. 测试接口时建议使用Postman或类似工具：
   - 提供更友好的界面
   - 可以保存历史记录
   - 支持环境变量
   - 可以自动管理token 