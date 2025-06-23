#!/bin/bash

# 前端单元测试运行脚本
echo "🚀 启动前端单元测试..."

# 检查依赖
if ! command -v yarn &> /dev/null; then
    echo "❌ yarn 未安装，请先安装 yarn"
    exit 1
fi

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖中..."
    yarn install
fi

echo "🧪 运行所有测试（单次运行）..."
yarn test --watch=false --browsers=ChromeHeadless

echo ""
echo "📊 生成覆盖率报告..."
yarn test:coverage

echo ""
echo "✅ 测试完成！"
echo "📋 测试报告："
echo "   - 基础报告: 在终端输出"
echo "   - 覆盖率报告: coverage/dataask_front/index.html"
echo ""
echo "🔧 可用的测试命令："
echo "   yarn test          # 监视模式运行测试"
echo "   yarn test:coverage # 生成覆盖率报告"
echo "   yarn test:ci       # CI环境运行测试" 