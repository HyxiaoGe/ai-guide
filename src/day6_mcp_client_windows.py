#!/usr/bin/env python3
"""
第6天：Windows兼容的MCP客户端示例
解决Windows环境下stdio通信问题
"""

import asyncio
import sys
import os
from typing import Dict, Any
import subprocess
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class WindowsMCPClient:
    """
    Windows兼容的MCP客户端
    使用subprocess直接通信而不是stdio_client
    """
    
    def __init__(self, server_script: str):
        self.server_script = server_script
        self.process = None
    
    async def start_server(self):
        """启动MCP服务器进程"""
        try:
            # 在Windows上使用subprocess.Popen
            self.process = subprocess.Popen(
                [sys.executable, self.server_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            print("✅ MCP服务器启动成功")
            return True
        except Exception as e:
            print(f"❌ 启动服务器失败: {e}")
            return False
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求到MCP服务器"""
        if not self.process:
            raise RuntimeError("服务器未启动")
        
        try:
            # 构建JSON-RPC请求
            json_request = json.dumps(request) + "\n"
            
            # 发送请求
            self.process.stdin.write(json_request)
            self.process.stdin.flush()
            
            # 读取响应
            response_line = self.process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
            else:
                raise RuntimeError("服务器没有响应")
                
        except Exception as e:
            print(f"通信错误: {e}")
            raise
    
    async def list_tools(self):
        """列出可用工具"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        return await self.send_request(request)
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """调用工具"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        return await self.send_request(request)
    
    async def initialize(self):
        """初始化连接"""
        request = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        return await self.send_request(request)
    
    def close(self):
        """关闭连接"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("🔌 连接已关闭")

async def test_math_tools_windows():
    """
    在Windows环境下测试数学工具
    """
    print("🔧 Windows MCP客户端测试")
    print("=" * 50)
    
    # 获取服务器脚本路径
    server_script = os.path.join(
        os.path.dirname(__file__), 
        "day6_mcp_server_simple.py"
    )
    
    if not os.path.exists(server_script):
        print(f"❌ 服务器脚本不存在: {server_script}")
        return
    
    client = WindowsMCPClient(server_script)
    
    try:
        # 启动服务器
        if not await client.start_server():
            return
        
        # 等待服务器初始化
        await asyncio.sleep(1)
        
        print("\n📡 初始化连接...")
        try:
            init_response = await client.initialize()
            print(f"初始化响应: {init_response}")
        except Exception as e:
            print(f"⚠️ 初始化可能失败，但继续测试: {e}")
        
        # 列出工具
        print("\n📋 获取可用工具...")
        try:
            tools_response = await client.list_tools()
            print(f"工具列表响应: {tools_response}")
        except Exception as e:
            print(f"获取工具列表失败: {e}")
        
        # 测试数学运算
        test_cases = [
            ("add", {"a": 10, "b": 25}, "加法测试"),
            ("multiply", {"a": 7, "b": 8}, "乘法测试"),
            ("divide", {"a": 100, "b": 4}, "除法测试"),
            ("power", {"a": 2, "b": 10}, "幂运算测试")
        ]
        
        print("\n🧮 开始数学运算测试:")
        for tool_name, args, description in test_cases:
            try:
                print(f"\n{description} ({tool_name}):")
                response = await client.call_tool(tool_name, args)
                print(f"  结果: {response}")
            except Exception as e:
                print(f"  ❌ 测试失败: {e}")
        
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
    
    finally:
        client.close()

async def simple_manual_test():
    """
    简单的手动测试（如果自动测试失败）
    """
    print("\n" + "="*50)
    print("🔧 手动测试模式")
    print("=" * 50)
    
    server_script = os.path.join(
        os.path.dirname(__file__), 
        "day6_mcp_server_simple.py"
    )
    
    print(f"请在另一个终端中运行: python {server_script}")
    print("然后手动输入以下JSON-RPC请求:")
    
    # 初始化请求
    init_request = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    print("\n1. 初始化请求:")
    print(json.dumps(init_request, indent=2))
    
    # 列出工具请求
    list_tools_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    print("\n2. 列出工具:")
    print(json.dumps(list_tools_request, indent=2))
    
    # 调用工具请求
    call_tool_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "add",
            "arguments": {"a": 10, "b": 25}
        }
    }
    
    print("\n3. 调用加法工具:")
    print(json.dumps(call_tool_request, indent=2))

async def check_environment():
    """检查运行环境"""
    print("🔍 环境检查")
    print("=" * 30)
    
    print(f"操作系统: {os.name}")
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查MCP包
    try:
        import mcp
        print(f"✅ MCP包版本: {mcp.__version__}")
    except ImportError:
        print("❌ MCP包未安装")
        print("请运行: pip install mcp")
        return False
    except AttributeError:
        print("✅ MCP包已安装（版本信息不可用）")
    
    # 检查服务器脚本
    server_script = os.path.join(
        os.path.dirname(__file__), 
        "day6_mcp_server_simple.py"
    )
    
    if os.path.exists(server_script):
        print(f"✅ 服务器脚本存在: {server_script}")
    else:
        print(f"❌ 服务器脚本不存在: {server_script}")
        return False
    
    return True

async def main():
    """主函数"""
    print("🚀 Windows MCP客户端测试程序")
    print("=" * 50)
    
    # 环境检查
    if not await check_environment():
        return
    
    print("\n选择测试模式:")
    print("1. 自动测试 (推荐)")
    print("2. 手动测试说明")
    print("3. 环境检查")
    
    # 在Jupyter中自动选择模式1
    choice = "1"
    
    if choice == "1":
        await test_math_tools_windows()
    elif choice == "2":
        await simple_manual_test()
    elif choice == "3":
        await check_environment()
    else:
        print("无效选择")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()