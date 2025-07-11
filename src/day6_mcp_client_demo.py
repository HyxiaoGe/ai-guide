#!/usr/bin/env python3
"""
第6天：MCP客户端示例
演示如何连接和使用MCP服务器
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_math_tools():
    """
    测试数学工具MCP服务器
    """
    print("🔧 MCP客户端示例")
    print("=" * 50)
    
    # 定义服务器连接参数
    server_params = StdioServerParameters(
        command="python",
        args=["src/day6_mcp_server_simple.py"],
        env=None
    )
    
    try:
        # 连接到MCP服务器
        print("📡 连接到MCP服务器...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化连接
                await session.initialize()
                print("✅ 连接成功！")
                
                # 列出可用工具
                print("\n📋 可用工具：")
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    print(f"  🔸 {tool.name}: {tool.description}")
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        props = tool.inputSchema.get('properties', {})
                        params = ", ".join([f"{k}({v.get('type', 'any')})" for k, v in props.items()])
                        print(f"     参数: {params}")
                
                # 测试各种数学运算
                print("\n🧮 测试数学运算：")
                
                # 测试加法
                print("\n1. 测试加法 (10 + 25):")
                result = await session.call_tool(
                    "add",
                    arguments={"a": 10, "b": 25}
                )
                print(f"   结果: {result.content[0].text}")
                
                # 测试乘法
                print("\n2. 测试乘法 (7 × 8):")
                result = await session.call_tool(
                    "multiply",
                    arguments={"a": 7, "b": 8}
                )
                print(f"   结果: {result.content[0].text}")
                
                # 测试除法
                print("\n3. 测试除法 (100 ÷ 4):")
                result = await session.call_tool(
                    "divide",
                    arguments={"a": 100, "b": 4}
                )
                print(f"   结果: {result.content[0].text}")
                
                # 测试除以零
                print("\n4. 测试除以零 (10 ÷ 0):")
                result = await session.call_tool(
                    "divide",
                    arguments={"a": 10, "b": 0}
                )
                print(f"   结果: {result.content[0].text}")
                
                # 测试幂运算
                print("\n5. 测试幂运算 (2^10):")
                result = await session.call_tool(
                    "power",
                    arguments={"a": 2, "b": 10}
                )
                print(f"   结果: {result.content[0].text}")
                
                # 测试浮点数运算
                print("\n6. 测试浮点数 (3.14 × 2.5):")
                result = await session.call_tool(
                    "multiply",
                    arguments={"a": 3.14, "b": 2.5}
                )
                print(f"   结果: {result.content[0].text}")
                
                # 测试错误的工具名
                print("\n7. 测试错误的工具名:")
                try:
                    result = await session.call_tool(
                        "unknown_tool",
                        arguments={"a": 1, "b": 2}
                    )
                    print(f"   结果: {result.content[0].text}")
                except Exception as e:
                    print(f"   错误: {e}")
                
                print("\n✅ 所有测试完成！")
                
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("提示：请确保MCP服务器正在运行")

async def interactive_math_client():
    """
    交互式数学客户端
    允许用户输入数学运算
    """
    print("\n🔢 交互式数学计算器（MCP版）")
    print("=" * 50)
    print("支持的操作：add, multiply, divide, power")
    print("输入 'quit' 退出")
    print("=" * 50)
    
    server_params = StdioServerParameters(
        command="python",
        args=["src/day6_mcp_server_simple.py"],
        env=None
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                while True:
                    print("\n请选择操作：")
                    print("1. 加法 (add)")
                    print("2. 乘法 (multiply)")
                    print("3. 除法 (divide)")
                    print("4. 幂运算 (power)")
                    print("5. 退出 (quit)")
                    
                    choice = input("\n选择 (1-5): ").strip()
                    
                    if choice == "5" or choice.lower() == "quit":
                        print("👋 再见！")
                        break
                    
                    operation_map = {
                        "1": "add",
                        "2": "multiply",
                        "3": "divide",
                        "4": "power"
                    }
                    
                    if choice not in operation_map:
                        print("❌ 无效的选择，请重试")
                        continue
                    
                    operation = operation_map[choice]
                    
                    try:
                        a = float(input("输入第一个数: "))
                        b = float(input("输入第二个数: "))
                        
                        result = await session.call_tool(
                            operation,
                            arguments={"a": a, "b": b}
                        )
                        
                        print(f"\n📊 {result.content[0].text}")
                        
                    except ValueError:
                        print("❌ 请输入有效的数字")
                    except Exception as e:
                        print(f"❌ 错误: {e}")
                        
    except Exception as e:
        print(f"\n❌ 无法连接到MCP服务器: {e}")

async def main():
    """主函数"""
    print("MCP客户端演示程序")
    print("=" * 50)
    print("1. 运行自动测试")
    print("2. 启动交互式计算器")
    
    choice = input("\n选择 (1/2): ").strip()
    
    if choice == "1":
        await test_math_tools()
    elif choice == "2":
        await interactive_math_client()
    else:
        print("无效的选择")

if __name__ == "__main__":
    asyncio.run(main())