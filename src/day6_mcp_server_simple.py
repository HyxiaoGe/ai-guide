#!/usr/bin/env python3
"""
第6天：简单的MCP服务器示例
提供基础的数学计算工具
"""

import asyncio
from typing import Any, Dict

from mcp.server import Server, stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsResult
)

# 创建MCP服务器实例
server = Server("math-tools")

# 定义可用的工具
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    列出所有可用的工具
    这个方法告诉客户端服务器提供哪些工具
    """
    return [
        Tool(
            name="add",
            description="将两个数字相加",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "第一个数"},
                    "b": {"type": "number", "description": "第二个数"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="multiply",
            description="将两个数字相乘",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "第一个数"},
                    "b": {"type": "number", "description": "第二个数"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="divide",
            description="将第一个数除以第二个数",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "被除数"},
                    "b": {"type": "number", "description": "除数（不能为0）"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="power",
            description="计算a的b次方",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "底数"},
                    "b": {"type": "number", "description": "指数"}
                },
                "required": ["a", "b"]
            }
        )
    ]

# 实现工具调用处理
@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: Dict[str, Any]
) -> list[TextContent]:
    """
    处理工具调用请求
    根据工具名称执行相应的操作
    """
    try:
        if name == "add":
            result = arguments["a"] + arguments["b"]
            return [TextContent(
                type="text",
                text=f"{arguments['a']} + {arguments['b']} = {result}"
            )]
        
        elif name == "multiply":
            result = arguments["a"] * arguments["b"]
            return [TextContent(
                type="text",
                text=f"{arguments['a']} × {arguments['b']} = {result}"
            )]
        
        elif name == "divide":
            if arguments["b"] == 0:
                return [TextContent(
                    type="text",
                    text="错误：除数不能为0"
                )]
            result = arguments["a"] / arguments["b"]
            return [TextContent(
                type="text",
                text=f"{arguments['a']} ÷ {arguments['b']} = {result}"
            )]
        
        elif name == "power":
            result = arguments["a"] ** arguments["b"]
            return [TextContent(
                type="text",
                text=f"{arguments['a']} ^ {arguments['b']} = {result}"
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"错误：未知的工具 '{name}'"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"错误：执行工具时出错 - {str(e)}"
        )]

async def main():
    """启动MCP服务器"""
    print("🚀 启动数学工具MCP服务器...")
    print("📝 提供的工具：add, multiply, divide, power")
    print("⏳ 等待客户端连接...")
    
    # 使用标准输入输出进行通信
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions()
        )

if __name__ == "__main__":
    asyncio.run(main())