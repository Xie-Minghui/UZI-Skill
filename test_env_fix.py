#!/usr/bin/env python3
"""
测试 env 变量引用错误的修复
"""

import sys
from pathlib import Path

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent / "skills" / "deep-analysis" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

def test_env_fix():
    """测试 env 变量引用错误修复"""
    print("🧪 测试 env 变量引用错误修复\n")
    
    # 检查 run.py 中的代码逻辑
    run_py = Path(__file__).parent / "run.py"
    if not run_py.exists():
        print("❌ run.py 不存在")
        return False
    
    content = run_py.read_text(encoding="utf-8")
    
    # 检查 env 定义和使用顺序
    lines = content.split("\n")
    
    env_def_line = -1
    env_use_lines = []
    
    for i, line in enumerate(lines, 1):
        if "env = detect_environment()" in line:
            env_def_line = i
        if "env[" in line and "detect_environment" not in line:
            env_use_lines.append(i)
    
    print(f"env 定义位置: 第 {env_def_line} 行")
    print(f"env 使用位置: {env_use_lines[:5]} ...")
    
    if env_def_line == -1:
        print("\n❌ 未找到 env 定义")
        return False
    
    # 检查是否有在定义之前使用 env
    early_uses = [line for line in env_use_lines if line < env_def_line]
    if early_uses:
        print(f"\n❌ env 在定义之前被使用: 第 {early_uses} 行")
        return False
    else:
        print(f"\n✅ env 定义在所有使用之前")
    
    # 检查是否有重复的 env 定义
    env_def_count = content.count("env = detect_environment()")
    if env_def_count > 1:
        print(f"⚠️  发现 {env_def_count} 个 env 定义（可能有重复）")
    else:
        print(f"✅ env 定义只有 1 个")
    
    return True

if __name__ == "__main__":
    result = test_env_fix()
    
    print("\n" + "="*60)
    if result:
        print("✅ 测试通过！env 引用错误已修复")
        print("\n现在可以运行：")
        print("  python run.py --industry 半导体 --top-n 3 --detailed")
    else:
        print("❌ 测试失败，需要进一步检查")
