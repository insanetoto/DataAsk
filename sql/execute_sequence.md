# 用户编码序列SQL脚本执行说明

## 🐳 Docker环境执行方法

### 方法1：通过Docker容器执行
```bash
# 假设MySQL容器名为mysql或dataask-mysql
docker exec -i mysql_container_name mysql -u root -p DataAsk < sql/user_sequence.sql

# 或者交互式执行
docker exec -it mysql_container_name mysql -u root -p
# 然后在MySQL命令行中：
USE DataAsk;
SOURCE /path/to/sql/user_sequence.sql;
```

### 方法2：Docker Compose执行
```bash
# 如果使用docker-compose
docker-compose exec mysql mysql -u root -p DataAsk < sql/user_sequence.sql
```

### 方法3：通过宿主机MySQL客户端
```bash
# 如果MySQL端口映射到宿主机（通常是3306）
mysql -h localhost -P 3306 -u root -p DataAsk < sql/user_sequence.sql

# 或者交互式
mysql -h localhost -P 3306 -u root -p
# 然后执行：
USE DataAsk;
SOURCE sql/user_sequence.sql;
```

## 🔍 查找Docker容器名称

```bash
# 查看运行中的MySQL容器
docker ps | grep mysql

# 查看所有容器（包括停止的）
docker ps -a | grep mysql
```

## ✅ 验证执行结果

执行完成后，验证序列表和函数是否创建成功：

```sql
-- 检查序列表是否存在
SHOW TABLES LIKE 'user_code_seq';

-- 检查函数是否存在
SHOW CREATE FUNCTION generate_user_code;

-- 测试函数
SELECT generate_user_code('0501') AS test_user_code;
```

### 🎯 实际测试结果（已验证成功）：

```bash
# 检查表
mysql> SHOW TABLES LIKE 'user_code_seq';
+--------------------------------+
| Tables_in_dataask (user_code_seq) |
+--------------------------------+
| user_code_seq                  |
+--------------------------------+

# 测试函数生成用户编码
mysql> SELECT generate_user_code('0501') AS test1, 
              generate_user_code('0502') AS test2, 
              generate_user_code('0503') AS test3;
+------------------+------------------+------------------+
| test1            | test2            | test3            |
+------------------+------------------+------------------+
| 0501000000000001 | 0502000000000002 | 0503000000000003 |
+------------------+------------------+------------------+
```

**说明**：
- 机构编码`0501`被正确补齐为`0501000000`（10位）
- 序列号从`1`开始，正确补齐为`000001`（6位）
- 最终用户编码格式：`机构编码10位` + `序列号6位` = `总共16位`

## 🎯 根据env.example配置

基于您的env.example配置：
- MySQL主机：localhost
- MySQL端口：3306
- MySQL用户：root
- MySQL密码：llmstudy
- 数据库名：dataask（注意：配置文件中是小写）

### ✅ 已执行成功的命令：
```bash
# Docker容器执行（已测试成功）
docker exec -i mysql-server-llm mysql -u root -pllmstudy dataask < sql/user_sequence.sql

# 或者如果您的容器名不同，可以这样执行：
# docker exec -i YOUR_MYSQL_CONTAINER_NAME mysql -u root -pllmstudy dataask < sql/user_sequence.sql
```

### 备用执行命令：
```bash
# 直接执行（如果MySQL端口映射到宿主机）
mysql -h localhost -P 3306 -u root -pllmstudy dataask < sql/user_sequence.sql
```

## ⚠️ 注意事项

1. **数据库名称**：env.example中配置的是`dataask`（小写），不是`DataAsk`
2. **MySQL 8.0**：确保您的MySQL版本确实是8.0+，支持原生序列
3. **权限**：确保用户有创建序列和函数的权限

## 🔧 如果遇到问题

1. **检查MySQL版本**：
   ```sql
   SELECT VERSION();
   ```

2. **检查权限**：
   ```sql
   SHOW GRANTS FOR 'root'@'localhost';
   ```

3. **检查数据库是否存在**：
   ```sql
   SHOW DATABASES LIKE 'dataask';
   ``` 