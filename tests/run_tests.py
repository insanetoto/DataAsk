#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试运行脚本
提供便捷的测试执行和报告生成功能
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime


def run_command(command, description=""):
    """运行命令并处理结果"""
    print(f"\n{'='*60}")
    if description:
        print(f"执行: {description}")
    print(f"命令: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("警告信息:")
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败 (退出码: {e.returncode})")
        if e.stdout:
            print("标准输出:")
            print(e.stdout)
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        return False


def install_dependencies():
    """安装测试依赖"""
    dependencies = [
        'pytest>=7.0.0',
        'pytest-html>=3.1.0',
        'pytest-cov>=4.0.0',
        'pytest-xdist>=3.0.0',
        'pytest-mock>=3.10.0',
        'coverage>=6.0.0'
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"安装 {dep}"):
            print(f"安装 {dep} 失败")
            return False
    
    return True


def run_unit_tests(coverage=True, parallel=False):
    """运行单元测试"""
    cmd = "python -m pytest tests/unit/"
    
    if coverage:
        cmd += " --cov=service --cov=tools"
        cmd += " --cov-report=html:tests/reports/coverage_html"
        cmd += " --cov-report=xml:tests/reports/coverage.xml"
        cmd += " --cov-report=term-missing"
    
    if parallel:
        cmd += " -n auto"
    
    cmd += " --html=tests/reports/unit_tests_report.html --self-contained-html"
    cmd += " --junitxml=tests/reports/unit_tests_junit.xml"
    cmd += " -v"
    
    return run_command(cmd, "运行单元测试")


def run_integration_tests(parallel=False):
    """运行集成测试"""
    cmd = "python -m pytest tests/integration/"
    
    if parallel:
        cmd += " -n auto"
    
    cmd += " --html=tests/reports/integration_tests_report.html --self-contained-html"
    cmd += " --junitxml=tests/reports/integration_tests_junit.xml"
    cmd += " -v"
    
    return run_command(cmd, "运行集成测试")


def run_all_tests(coverage=True, parallel=False):
    """运行所有测试"""
    cmd = "python -m pytest tests/"
    
    if coverage:
        cmd += " --cov=service --cov=tools"
        cmd += " --cov-report=html:tests/reports/coverage_html"
        cmd += " --cov-report=xml:tests/reports/coverage.xml"
        cmd += " --cov-report=term-missing"
    
    if parallel:
        cmd += " -n auto"
    
    cmd += " --html=tests/reports/all_tests_report.html --self-contained-html"
    cmd += " --junitxml=tests/reports/all_tests_junit.xml"
    cmd += " -v"
    
    return run_command(cmd, "运行所有测试")


def run_specific_tests(test_pattern, coverage=False):
    """运行特定测试"""
    cmd = f"python -m pytest {test_pattern}"
    
    if coverage:
        cmd += " --cov=service --cov=tools"
        cmd += " --cov-report=term-missing"
    
    cmd += " -v"
    
    return run_command(cmd, f"运行测试: {test_pattern}")


def run_performance_tests():
    """运行性能测试"""
    cmd = "python -m pytest tests/ -m slow"
    cmd += " --html=tests/reports/performance_tests_report.html --self-contained-html"
    cmd += " --junitxml=tests/reports/performance_tests_junit.xml"
    cmd += " -v"
    
    return run_command(cmd, "运行性能测试")


def generate_coverage_report():
    """生成覆盖率报告"""
    print("\n生成覆盖率报告...")
    
    # 生成HTML报告
    if run_command("coverage html -d tests/reports/coverage_html", "生成HTML覆盖率报告"):
        print("HTML覆盖率报告已生成: tests/reports/coverage_html/index.html")
    
    # 生成XML报告
    if run_command("coverage xml -o tests/reports/coverage.xml", "生成XML覆盖率报告"):
        print("XML覆盖率报告已生成: tests/reports/coverage.xml")
    
    # 显示覆盖率总结
    run_command("coverage report", "显示覆盖率总结")


def clean_reports():
    """清理旧的测试报告"""
    import shutil
    
    reports_dir = "tests/reports"
    if os.path.exists(reports_dir):
        shutil.rmtree(reports_dir)
        print(f"已清理报告目录: {reports_dir}")
    
    os.makedirs(reports_dir, exist_ok=True)
    print(f"已创建报告目录: {reports_dir}")


def setup_test_environment():
    """设置测试环境"""
    print("设置测试环境...")
    
    # 创建必要的目录
    os.makedirs("tests/reports", exist_ok=True)
    
    # 设置环境变量
    os.environ['TESTING'] = 'true'
    os.environ['FLASK_ENV'] = 'testing'
    
    # 确保在项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    print(f"工作目录: {os.getcwd()}")
    print("测试环境设置完成")


def print_test_summary():
    """打印测试总结"""
    reports_dir = "tests/reports"
    
    print(f"\n{'='*60}")
    print("测试执行完成!")
    print(f"{'='*60}")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if os.path.exists(reports_dir):
        print(f"\n测试报告位置: {reports_dir}")
        
        report_files = {
            "all_tests_report.html": "完整测试报告",
            "unit_tests_report.html": "单元测试报告", 
            "integration_tests_report.html": "集成测试报告",
            "performance_tests_report.html": "性能测试报告",
            "coverage_html/index.html": "覆盖率报告",
            "coverage.xml": "覆盖率XML报告"
        }
        
        for file_name, description in report_files.items():
            file_path = os.path.join(reports_dir, file_name)
            if os.path.exists(file_path):
                print(f"  - {description}: {file_path}")
    
    print(f"\n{'='*60}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="DataAsk 测试运行器")
    parser.add_argument('--install-deps', action='store_true', help='安装测试依赖')
    parser.add_argument('--unit', action='store_true', help='运行单元测试')
    parser.add_argument('--integration', action='store_true', help='运行集成测试')
    parser.add_argument('--performance', action='store_true', help='运行性能测试')
    parser.add_argument('--all', action='store_true', help='运行所有测试')
    parser.add_argument('--pattern', type=str, help='运行匹配模式的测试')
    parser.add_argument('--no-coverage', action='store_true', help='禁用覆盖率报告')
    parser.add_argument('--parallel', action='store_true', help='并行运行测试')
    parser.add_argument('--clean', action='store_true', help='清理测试报告')
    parser.add_argument('--coverage-only', action='store_true', help='仅生成覆盖率报告')
    
    args = parser.parse_args()
    
    # 设置测试环境
    setup_test_environment()
    
    # 安装依赖
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
        return
    
    # 清理报告
    if args.clean:
        clean_reports()
        return
    
    # 仅生成覆盖率报告
    if args.coverage_only:
        generate_coverage_report()
        return
    
    # 清理旧报告
    clean_reports()
    
    coverage = not args.no_coverage
    success = True
    
    # 运行测试
    if args.unit:
        success = run_unit_tests(coverage=coverage, parallel=args.parallel)
    elif args.integration:
        success = run_integration_tests(parallel=args.parallel)
    elif args.performance:
        success = run_performance_tests()
    elif args.pattern:
        success = run_specific_tests(args.pattern, coverage=coverage)
    elif args.all:
        success = run_all_tests(coverage=coverage, parallel=args.parallel)
    else:
        # 默认运行所有测试
        success = run_all_tests(coverage=coverage, parallel=args.parallel)
    
    # 生成覆盖率报告
    if coverage and success:
        generate_coverage_report()
    
    # 打印总结
    print_test_summary()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 