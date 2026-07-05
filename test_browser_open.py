#!/usr/bin/env python3
"""
测试行业分析后的浏览器打开功能
"""

import sys
from pathlib import Path

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent / "skills" / "deep-analysis" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

def test_browser_open():
    """测试浏览器打开功能"""
    print("🧪 测试浏览器打开功能\n")
    
    # 检查 run.py 中的代码逻辑
    run_py = Path(__file__).parent / "run.py"
    if not run_py.exists():
        print("❌ run.py 不存在")
        return False
    
    content = run_py.read_text(encoding="utf-8")
    
    # 检查是否添加了浏览器打开逻辑
    checks = [
        ("行业分析 - 浏览器打开", "webbrowser.open(report_path.as_uri())" in content),
        ("行业分析 - no-browser 参数", "not args.no_browser" in content),
        ("行业分析 - remote 参数", "args.remote" in content),
        ("行业对比 - 浏览器打开", "compare_industries" in content and "webbrowser" in content),
        ("行业选股 - 浏览器打开", "screen_industry" in content and "webbrowser" in content),
        ("组合诊断 - 浏览器打开", "analyze_portfolio" in content and "webbrowser" in content),
        ("智能投顾 - 浏览器打开", "recommend_portfolio" in content and "webbrowser" in content),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    result = test_browser_open()
    
    print("\n" + "="*60)
    if result:
        print("✅ 所有检查通过！浏览器打开功能已添加")
        print("\n使用方法：")
        print("  python run.py --industry 半导体 --detailed           # 自动打开浏览器")
        print("  python run.py --industry 半导体 --detailed --no-browser  # 不打开浏览器")
        print("  python run.py --industry 半导体 --detailed --remote     # 远程模式")
    else:
        print("❌ 部分检查失败，需要进一步检查")
