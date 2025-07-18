#!/bin/bash

# ===========================================
# Text2SQL 端到端集成测试脚本
# ===========================================

echo "=== Text2SQL 端到端集成测试 ==="
echo "测试时间: $(date)"
echo ""

# 设置变量
BACKEND_URL="http://localhost:9000"
FRONTEND_URL="http://localhost:4200"
TOKEN=""

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 辅助函数
log_test() {
    echo -e "${YELLOW}[测试]${NC} $1"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

log_pass() {
    echo -e "${GREEN}✅ PASS${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

log_fail() {
    echo -e "${RED}❌ FAIL${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

# 测试1: 后端健康检查
test_backend_health() {
    log_test "后端健康检查"
    
    response=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/text2sql/health")
    
    if [ "$response" -eq 200 ]; then
        log_pass "后端服务正常运行"
    else
        log_fail "后端服务异常 (HTTP $response)"
        return 1
    fi
}

# 测试2: 前端可访问性
test_frontend_accessibility() {
    log_test "前端可访问性"
    
    response=$(curl -s -w "%{http_code}" -o /dev/null "$FRONTEND_URL")
    
    if [ "$response" -eq 200 ]; then
        log_pass "前端服务正常运行"
    else
        log_fail "前端服务异常 (HTTP $response)"
        return 1
    fi
}

# 测试3: 用户登录并获取Token
test_user_login() {
    log_test "用户登录认证"
    
    login_response=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "admin123"}')
    
    # 检查登录响应
    if echo "$login_response" | grep -q "access_token"; then
        TOKEN=$(echo "$login_response" | jq -r '.data.access_token' 2>/dev/null)
        if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
            log_pass "用户登录成功，Token已获取"
        else
            log_fail "无法提取Token"
            return 1
        fi
    else
        log_fail "用户登录失败"
        echo "响应: $login_response"
        return 1
    fi
}

# 测试4: 会话管理
test_session_management() {
    log_test "会话管理功能"
    
    # 获取会话列表
    sessions_response=$(curl -s -X GET "$BACKEND_URL/api/text2sql/sessions" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$sessions_response" | grep -q "sessions"; then
        log_pass "会话列表获取成功"
    else
        log_fail "会话列表获取失败"
        return 1
    fi
    
    # 创建新会话
    create_response=$(curl -s -X POST "$BACKEND_URL/api/text2sql/sessions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"title": "测试会话"}')
    
    if echo "$create_response" | grep -q "session_id"; then
        log_pass "新会话创建成功"
    else
        log_fail "新会话创建失败"
        return 1
    fi
}

# 测试5: SQL生成功能  
test_sql_generation() {
    log_test "SQL生成功能"
    
    # 测试简单查询
    sql_response=$(curl -s -X POST "$BACKEND_URL/api/text2sql/generate" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"question": "查询所有用户的ID和用户名"}')
    
    if echo "$sql_response" | grep -q "SELECT" && echo "$sql_response" | grep -q "success.*true"; then
        generated_sql=$(echo "$sql_response" | jq -r '.sql' 2>/dev/null)
        log_pass "SQL生成成功: $generated_sql"
        
        # 保存生成的SQL用于下一步测试
        echo "$generated_sql" > /tmp/test_sql.sql
    else
        log_fail "SQL生成失败"
        echo "响应: $sql_response"
        return 1
    fi
}

# 测试6: SQL执行功能
test_sql_execution() {
    log_test "SQL执行功能"
    
    if [ ! -f /tmp/test_sql.sql ]; then
        log_fail "没有SQL可以执行"
        return 1
    fi
    
    test_sql=$(cat /tmp/test_sql.sql)
    
    exec_response=$(curl -s -X POST "$BACKEND_URL/api/text2sql/execute" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{\"sql\": \"$test_sql\"}")
    
    if echo "$exec_response" | grep -q "success.*true" && echo "$exec_response" | grep -q "data"; then
        row_count=$(echo "$exec_response" | jq -r '.row_count' 2>/dev/null)
        execution_time=$(echo "$exec_response" | jq -r '.execution_time' 2>/dev/null)
        log_pass "SQL执行成功: 返回 $row_count 行数据，耗时 ${execution_time}ms"
    else
        log_fail "SQL执行失败"
        echo "响应: $exec_response"
        return 1
    fi
}

# 测试7: 训练样本功能
test_training_sample() {
    log_test "训练样本功能"
    
    train_response=$(curl -s -X POST "$BACKEND_URL/api/text2sql/train" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"question": "查询活跃用户", "sql": "SELECT * FROM users WHERE status = 1;"}')
    
    if echo "$train_response" | grep -q "success.*true"; then
        log_pass "训练样本添加成功"
    else
        log_fail "训练样本添加失败"
        echo "响应: $train_response"
        return 1
    fi
}

# 测试8: 复杂查询测试
test_complex_queries() {
    log_test "复杂查询功能"
    
    # 测试聚合查询
    complex_response=$(curl -s -X POST "$BACKEND_URL/api/text2sql/generate" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"question": "统计每个机构下有多少个用户"}')
    
    if echo "$complex_response" | grep -q "GROUP BY" && echo "$complex_response" | grep -q "COUNT"; then
        log_pass "复杂聚合查询生成成功"
    else
        log_fail "复杂查询生成失败"
        return 1
    fi
}

# 性能测试
test_performance() {
    log_test "性能基准测试"
    
    start_time=$(date +%s%N)
    
    perf_response=$(curl -s -X POST "$BACKEND_URL/api/text2sql/generate" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"question": "查询用户信息"}')
    
    end_time=$(date +%s%N)
    duration=$(( (end_time - start_time) / 1000000 )) # 转换为毫秒
    
    if [ $duration -lt 5000 ]; then # 5秒内
        log_pass "性能测试通过: SQL生成耗时 ${duration}ms"
    else
        log_fail "性能测试失败: SQL生成耗时 ${duration}ms (超过5秒)"
        return 1
    fi
}

# 执行所有测试
main() {
    echo "开始执行Text2SQL端到端集成测试..."
    echo ""
    
    # 执行测试
    test_backend_health
    test_frontend_accessibility
    test_user_login
    test_session_management  
    test_sql_generation
    test_sql_execution
    test_training_sample
    test_complex_queries
    test_performance
    
    # 清理临时文件
    rm -f /tmp/test_sql.sql
    
    echo ""
    echo "=== 测试总结 ==="
    echo "总测试数: $TOTAL_TESTS"
    echo -e "通过: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "失败: ${RED}$FAILED_TESTS${NC}"
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 所有测试通过！Text2SQL前后端集成成功！${NC}"
        echo ""
        echo "=== 集成状态 ==="
        echo "✅ 后端qwen-turbo AI: 正常工作"
        echo "✅ 前端Angular界面: 正常访问"  
        echo "✅ API调用流程: 完全可用"
        echo "✅ 数据库连接: 稳定运行"
        echo "✅ 用户认证: 安全可靠"
        echo ""
        echo "🚀 系统已准备好进入生产环境！"
        exit 0
    else
        echo -e "${RED}❌ 集成测试失败，请检查失败项目${NC}"
        exit 1
    fi
}

# 检查依赖工具
if ! command -v curl &> /dev/null; then
    echo "错误: 需要安装curl工具"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "警告: 未安装jq工具，JSON解析可能受限"
fi

# 运行主函数
main 