#!/usr/bin/env python3
"""系统测试脚本"""

import sys
import os

def test_imports():
    """测试关键包导入"""
    print("🧪 测试包导入...")
    
    packages = [
        ("mcp", "MCP"),
        ("langchain", "LangChain"), 
        ("chromadb", "ChromaDB"),
        ("openai", "OpenAI"),
        ("fastapi", "FastAPI"),
        ("streamlit", "Streamlit"),
    ]
    
    success = 0
    for package, name in packages:
        try:
            __import__(package)
            print(f"✅ {name}")
            success += 1
        except ImportError as e:
            print(f"❌ {name}: {e}")
    
    return success == len(packages)

def main():
    print("🔬 智能文档助手系统 - 环境测试")
    print("=" * 50)
    
    if test_imports():
        print("\n🎉 所有依赖包导入成功！")
        print("\n💡 下一步:")
        print("  1. 配置 .env 文件中的 API 密钥")
        print("  2. 运行: ./start.sh")
        return 0
    else:
        print("\n❌ 依赖包测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())