# -*- coding: utf-8 -*-
"""
后端单元测试执行脚本
提供多种测试执行方式和报告生成功能
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_command(cmd, capture_output=True):
    """执行命令并返回结果"""
    try:
        if capture_output:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=PROJECT_ROOT
            )
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, cwd=PROJECT_ROOT)
            return result.returncode, "", ""
    except Exception as e:
        return 1, "", str(e)


def check_environment():
    """检查测试环境"""
    print("🔍 检查测试环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查pytest是否安装
    code, stdout, stderr = run_command("python -m pytest --version")
    if code == 0:
        print(f"Pytest版本: {stdout.strip()}")
    else:
        print("❌ Pytest未安装，请运行: pip install pytest")
        return False
    
    # 检查测试依赖
    required_packages = ['pytest-cov', 'pytest-html', 'pytest-mock']
    missing_packages = []
    
    for package in required_packages:
        package_name = package.replace("-", "_")
        code, _, _ = run_command(f"python -c 'import {package_name}'")
        if code != 0:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print(f"请运行: pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 测试环境检查通过")
    return True


def run_unit_tests(args):
    """运行单元测试"""
    print("\n🧪 运行单元测试...")
    
    base_cmd = "python -m pytest tests/unit/"
    
    # 构建pytest命令
    pytest_args = []
    
    if args.verbose:
        pytest_args.append("-v")
    
    if args.coverage:
        pytest_args.extend([
            "--cov=service",
            "--cov=tools", 
            "--cov=models",
            "--cov=AIEngine",
            "--cov-report=html:tests/reports/coverage_html",
            "--cov-report=xml:tests/reports/coverage.xml",
            "--cov-report=term-missing"
        ])
    
    if args.html_report:
        pytest_args.extend([
            "--html=tests/reports/unit_test_report.html",
            "--self-contained-html"
        ])
    
    if args.markers:
        pytest_args.extend(["-m", args.markers])
    
    if args.failed_only:
        pytest_args.append("--lf")
    
    if args.parallel:
        pytest_args.extend(["-n", str(args.parallel)])
    
    # 执行命令
    cmd = f"{base_cmd} {' '.join(pytest_args)}"
    print(f"执行命令: {cmd}")
    
    start_time = time.time()
    code, stdout, stderr = run_command(cmd, capture_output=False)
    execution_time = time.time() - start_time
    
    print(f"\n⏱️  测试执行时间: {execution_time:.2f}秒")
    
    if code == 0:
        print("✅ 单元测试执行成功")
    else:
        print("❌ 单元测试执行失败")
        if stderr:
            print(f"错误信息: {stderr}")
    
    return code == 0


def run_integration_tests(args):
    """运行集成测试"""
    print("\n🔗 运行集成测试...")
    
    base_cmd = "python -m pytest tests/integration/"
    pytest_args = []
    
    if args.verbose:
        pytest_args.append("-v")
    
    if args.html_report:
        pytest_args.extend([
            "--html=tests/reports/integration_test_report.html",
            "--self-contained-html"
        ])
    
    cmd = f"{base_cmd} {' '.join(pytest_args)}"
    print(f"执行命令: {cmd}")
    
    start_time = time.time()
    code, stdout, stderr = run_command(cmd, capture_output=False)
    execution_time = time.time() - start_time
    
    print(f"\n⏱️  集成测试执行时间: {execution_time:.2f}秒")
    
    if code == 0:
        print("✅ 集成测试执行成功")
    else:
        print("❌ 集成测试执行失败")
    
    return code == 0


def run_specific_tests(test_path, args):
    """运行指定的测试"""
    print(f"\n🎯 运行指定测试: {test_path}")
    
    base_cmd = f"python -m pytest {test_path}"
    pytest_args = []
    
    if args.verbose:
        pytest_args.append("-v")
    
    if args.coverage:
        pytest_args.extend([
            "--cov=service",
            "--cov=tools",
            "--cov-report=term-missing"
        ])
    
    cmd = f"{base_cmd} {' '.join(pytest_args)}"
    print(f"执行命令: {cmd}")
    
    code, stdout, stderr = run_command(cmd, capture_output=False)
    
    if code == 0:
        print("✅ 指定测试执行成功")
    else:
        print("❌ 指定测试执行失败")
    
    return code == 0


def generate_test_report():
    """生成测试报告摘要"""
    print("\n📊 生成测试报告摘要...")
    
    # 确保报告目录存在
    reports_dir = PROJECT_ROOT / "tests" / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # 读取覆盖率报告
    coverage_file = reports_dir / "coverage.xml"
    if coverage_file.exists():
        print(f"📈 覆盖率报告已生成: {coverage_file}")
    
    # 检查HTML报告
    html_report = reports_dir / "unit_test_report.html"
    if html_report.exists():
        print(f"📄 HTML测试报告已生成: {html_report}")
    
    coverage_html_dir = reports_dir / "coverage_html"
    if coverage_html_dir.exists():
        print(f"🌐 覆盖率HTML报告已生成: {coverage_html_dir}/index.html")


def clean_test_artifacts():
    """清理测试产物"""
    print("\n🧹 清理测试产物...")
    
    artifacts = [
        "tests/reports",
        "tests/.pytest_cache",
        ".coverage",
        "**/__pycache__",
        "**/*.pyc"
    ]
    
    for pattern in artifacts:
        if pattern.startswith("tests/"):
            path = PROJECT_ROOT / pattern
            if path.exists():
                if path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                    print(f"删除目录: {path}")
                else:
                    path.unlink()
                    print(f"删除文件: {path}")
        else:
            # 使用glob模式清理
                         code, _, _ = run_command(f"find . -name \"{pattern}\" -delete")
    
    print("✅ 测试产物清理完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="后端单元测试执行脚本")
    
    # 基本选项
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("-c", "--coverage", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--html-report", action="store_true", help="生成HTML测试报告")
    
    # 测试选择
    parser.add_argument("-u", "--unit", action="store_true", help="只运行单元测试")
    parser.add_argument("-i", "--integration", action="store_true", help="只运行集成测试")
    parser.add_argument("-t", "--test-path", help="运行指定路径的测试")
    parser.add_argument("-m", "--markers", help="按标记过滤测试，如: unit,slow")
    
    # 执行选项
    parser.add_argument("--failed-only", action="store_true", help="只运行失败的测试")
    parser.add_argument("-n", "--parallel", type=int, help="并行执行测试的进程数")
    
    # 维护选项
    parser.add_argument("--clean", action="store_true", help="清理测试产物")
    parser.add_argument("--check-env", action="store_true", help="检查测试环境")
    
    args = parser.parse_args()
    
    # 如果没有指定参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    print("🚀 DataAsk后端测试执行器")
    print("=" * 50)
    
    # 检查环境
    if args.check_env:
        check_environment()
        return
    
    # 清理产物
    if args.clean:
        clean_test_artifacts()
        return
    
    # 检查基本环境
    if not check_environment():
        sys.exit(1)
    
    success = True
    
    # 运行指定测试
    if args.test_path:
        success = run_specific_tests(args.test_path, args)
    else:
        # 运行单元测试
        if args.unit or not args.integration:
            success = run_unit_tests(args) and success
        
        # 运行集成测试
        if args.integration or not args.unit:
            success = run_integration_tests(args) and success
    
    # 生成报告
    if args.coverage or args.html_report:
        generate_test_report()
    
    # 输出总结
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有测试执行成功！")
        sys.exit(0)
    else:
        print("💥 测试执行失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main() 