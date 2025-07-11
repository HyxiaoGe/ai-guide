#!/usr/bin/env python3
"""
第6天：文件管理MCP服务器
提供文件浏览、读取和信息查询功能
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

from mcp.server import Server, stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Tool,
    Resource,
    TextContent,
    ResourceContents,
    TextResourceContents
)

class FileManagerMCPServer:
    """
    文件管理MCP服务器
    提供安全的文件系统访问功能
    """
    
    def __init__(self, base_path: str = "."):
        """
        初始化文件管理服务器
        
        参数:
            base_path: 基础路径，所有文件操作都限制在此路径内
        """
        self.base_path = Path(base_path).resolve()
        self.server = Server("file-manager")
        self._setup_handlers()
        
        print(f"📁 文件管理服务器初始化")
        print(f"📍 基础路径: {self.base_path}")
    
    def _setup_handlers(self):
        """设置所有MCP处理器"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """定义可用的文件操作工具"""
            return [
                Tool(
                    name="list_files",
                    description="列出目录中的文件和子目录",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "目录路径（相对于基础路径）",
                                "default": "."
                            },
                            "pattern": {
                                "type": "string",
                                "description": "文件匹配模式（如 *.py, *.md）",
                                "default": "*"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "是否递归搜索子目录",
                                "default": False
                            }
                        }
                    }
                ),
                Tool(
                    name="read_file",
                    description="读取文件内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件路径（相对于基础路径）"
                            },
                            "encoding": {
                                "type": "string",
                                "description": "文件编码",
                                "default": "utf-8"
                            },
                            "max_lines": {
                                "type": "integer",
                                "description": "最大读取行数（-1表示全部）",
                                "default": -1
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="file_info",
                    description="获取文件或目录的详细信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件或目录路径"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="search_content",
                    description="在文件中搜索特定内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "要搜索的关键词"
                            },
                            "path": {
                                "type": "string",
                                "description": "搜索路径",
                                "default": "."
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "文件模式（如 *.py）",
                                "default": "*"
                            },
                            "case_sensitive": {
                                "type": "boolean",
                                "description": "是否区分大小写",
                                "default": False
                            }
                        },
                        "required": ["keyword"]
                    }
                )
            ]
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """列出重要文件作为资源"""
            resources = []
            
            # 查找项目中的重要文件
            important_files = {
                "README.md": "项目说明文档",
                "requirements.txt": "Python依赖列表",
                ".env.example": "环境变量示例",
                ".gitignore": "Git忽略文件配置",
                "CLAUDE.md": "Claude Code配置文件"
            }
            
            for filename, description in important_files.items():
                file_path = self.base_path / filename
                if file_path.exists():
                    resources.append(
                        Resource(
                            uri=f"file:///{filename}",
                            name=filename,
                            description=description,
                            mimeType=self._get_mime_type(filename)
                        )
                    )
            
            # 添加目录结构作为资源
            resources.append(
                Resource(
                    uri="tree:///",
                    name="项目结构",
                    description="项目的目录树结构",
                    mimeType="text/plain"
                )
            )
            
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ResourceContents:
            """读取资源内容"""
            if uri.startswith("file:///"):
                # 读取文件资源
                filename = uri[8:]  # 移除 file:///
                file_path = self.base_path / filename
                
                if not self._is_safe_path(file_path):
                    return TextResourceContents(
                        uri=uri,
                        mimeType="text/plain",
                        text="错误：访问被拒绝"
                    )
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    return TextResourceContents(
                        uri=uri,
                        mimeType=self._get_mime_type(filename),
                        text=content
                    )
                except Exception as e:
                    return TextResourceContents(
                        uri=uri,
                        mimeType="text/plain",
                        text=f"错误：无法读取文件 - {e}"
                    )
            
            elif uri == "tree:///":
                # 生成目录树
                tree = self._generate_tree(self.base_path, prefix="", max_depth=3)
                return TextResourceContents(
                    uri=uri,
                    mimeType="text/plain",
                    text=f"项目结构:\n\n{tree}"
                )
            
            else:
                return TextResourceContents(
                    uri=uri,
                    mimeType="text/plain",
                    text=f"错误：未知的资源URI - {uri}"
                )
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str,
            arguments: Dict[str, Any]
        ) -> list[TextContent]:
            """处理工具调用"""
            
            try:
                if name == "list_files":
                    result = await self._list_files(
                        arguments.get("path", "."),
                        arguments.get("pattern", "*"),
                        arguments.get("recursive", False)
                    )
                
                elif name == "read_file":
                    result = await self._read_file(
                        arguments["path"],
                        arguments.get("encoding", "utf-8"),
                        arguments.get("max_lines", -1)
                    )
                
                elif name == "file_info":
                    result = await self._file_info(arguments["path"])
                
                elif name == "search_content":
                    result = await self._search_content(
                        arguments["keyword"],
                        arguments.get("path", "."),
                        arguments.get("file_pattern", "*"),
                        arguments.get("case_sensitive", False)
                    )
                
                else:
                    result = f"错误：未知的工具 - {name}"
                
                return [TextContent(type="text", text=result)]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"错误：执行工具时出错 - {str(e)}"
                )]
    
    def _is_safe_path(self, path: Path) -> bool:
        """检查路径是否在允许的范围内"""
        try:
            resolved = path.resolve()
            return str(resolved).startswith(str(self.base_path))
        except:
            return False
    
    def _get_mime_type(self, filename: str) -> str:
        """根据文件扩展名返回MIME类型"""
        ext = Path(filename).suffix.lower()
        mime_types = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".py": "text/x-python",
            ".json": "application/json",
            ".yaml": "text/yaml",
            ".yml": "text/yaml",
            ".html": "text/html",
            ".css": "text/css",
            ".js": "text/javascript",
            ".ipynb": "application/x-ipynb+json"
        }
        return mime_types.get(ext, "text/plain")
    
    async def _list_files(self, path: str, pattern: str, recursive: bool) -> str:
        """列出文件"""
        try:
            target_path = (self.base_path / path).resolve()
            
            if not self._is_safe_path(target_path):
                return "错误：访问被拒绝（路径超出允许范围）"
            
            if not target_path.exists():
                return f"错误：路径不存在 - {path}"
            
            if not target_path.is_dir():
                return f"错误：{path} 不是目录"
            
            # 收集文件
            if recursive:
                files = list(target_path.rglob(pattern))
            else:
                files = list(target_path.glob(pattern))
            
            if not files:
                return f"在 {path} 中没有找到匹配 {pattern} 的文件"
            
            # 格式化输出
            result = f"📂 {path} 中的文件:\n\n"
            
            # 分类文件和目录
            dirs = sorted([f for f in files if f.is_dir()])
            files = sorted([f for f in files if f.is_file()])
            
            # 显示目录
            if dirs:
                result += "目录:\n"
                for d in dirs:
                    rel_path = d.relative_to(target_path)
                    result += f"  📁 {rel_path}/\n"
                result += "\n"
            
            # 显示文件
            if files:
                result += "文件:\n"
                for f in files:
                    rel_path = f.relative_to(target_path)
                    size = f.stat().st_size
                    result += f"  📄 {rel_path} ({self._format_size(size)})\n"
            
            # 统计信息
            result += f"\n总计: {len(dirs)} 个目录, {len(files)} 个文件"
            
            return result
            
        except Exception as e:
            return f"错误：{e}"
    
    async def _read_file(self, path: str, encoding: str, max_lines: int) -> str:
        """读取文件内容"""
        try:
            file_path = (self.base_path / path).resolve()
            
            if not self._is_safe_path(file_path):
                return "错误：访问被拒绝"
            
            if not file_path.exists():
                return f"错误：文件不存在 - {path}"
            
            if file_path.is_dir():
                return f"错误：{path} 是目录，不是文件"
            
            # 检查文件大小
            size = file_path.stat().st_size
            if size > 1024 * 1024:  # 1MB
                return f"错误：文件太大（{self._format_size(size)}），超过1MB限制"
            
            # 读取文件
            with open(file_path, 'r', encoding=encoding) as f:
                if max_lines > 0:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f"\n... (省略剩余内容，文件共 {sum(1 for _ in f) + i + 1} 行)")
                            break
                        lines.append(line.rstrip())
                    content = '\n'.join(lines)
                else:
                    content = f.read()
            
            # 添加文件信息头
            header = f"📄 文件: {path}\n"
            header += f"📏 大小: {self._format_size(size)}\n"
            header += f"🔤 编码: {encoding}\n"
            header += "=" * 50 + "\n\n"
            
            return header + content
            
        except UnicodeDecodeError:
            return f"错误：无法使用编码 {encoding} 读取文件，请尝试其他编码（如 gbk, latin1）"
        except Exception as e:
            return f"错误：{e}"
    
    async def _file_info(self, path: str) -> str:
        """获取文件信息"""
        try:
            file_path = (self.base_path / path).resolve()
            
            if not self._is_safe_path(file_path):
                return "错误：访问被拒绝"
            
            if not file_path.exists():
                return f"错误：路径不存在 - {path}"
            
            stat = file_path.stat()
            
            info = f"📊 文件信息: {path}\n"
            info += "=" * 50 + "\n\n"
            
            # 基本信息
            info += f"类型: {'📁 目录' if file_path.is_dir() else '📄 文件'}\n"
            info += f"大小: {self._format_size(stat.st_size)}\n"
            
            # 时间信息
            info += f"创建时间: {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}\n"
            info += f"修改时间: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n"
            info += f"访问时间: {datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # 权限信息（Unix-like系统）
            if hasattr(stat, 'st_mode'):
                import stat as stat_module
                mode = stat.st_mode
                info += f"\n权限: {stat_module.filemode(mode)}\n"
            
            # 文件特定信息
            if file_path.is_file():
                info += f"\n文件扩展名: {file_path.suffix or '无'}\n"
                
                # 尝试统计行数（文本文件）
                if file_path.suffix in ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml']:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            line_count = sum(1 for _ in f)
                        info += f"行数: {line_count}\n"
                    except:
                        pass
            
            # 目录特定信息
            elif file_path.is_dir():
                try:
                    items = list(file_path.iterdir())
                    file_count = sum(1 for item in items if item.is_file())
                    dir_count = sum(1 for item in items if item.is_dir())
                    info += f"\n包含: {file_count} 个文件, {dir_count} 个目录\n"
                except:
                    pass
            
            return info
            
        except Exception as e:
            return f"错误：{e}"
    
    async def _search_content(self, keyword: str, path: str, 
                            file_pattern: str, case_sensitive: bool) -> str:
        """在文件中搜索内容"""
        try:
            target_path = (self.base_path / path).resolve()
            
            if not self._is_safe_path(target_path):
                return "错误：访问被拒绝"
            
            if not target_path.exists():
                return f"错误：路径不存在 - {path}"
            
            # 准备搜索
            if not case_sensitive:
                keyword = keyword.lower()
            
            results = []
            
            # 搜索文件
            if target_path.is_file():
                files = [target_path]
            else:
                files = list(target_path.rglob(file_pattern))
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                # 跳过二进制文件
                if file_path.suffix in ['.exe', '.dll', '.so', '.dylib', '.pdf', 
                                       '.jpg', '.png', '.gif', '.zip', '.tar']:
                    continue
                
                try:
                    matches = []
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            search_line = line if case_sensitive else line.lower()
                            if keyword in search_line:
                                matches.append({
                                    'line_num': line_num,
                                    'content': line.strip()
                                })
                    
                    if matches:
                        results.append({
                            'file': file_path.relative_to(self.base_path),
                            'matches': matches
                        })
                        
                except (UnicodeDecodeError, PermissionError):
                    # 跳过无法读取的文件
                    continue
            
            # 格式化结果
            if not results:
                return f"在 {path} 中没有找到包含 '{keyword}' 的文件"
            
            output = f"🔍 搜索结果 - 关键词: '{keyword}'\n"
            output += f"📍 搜索路径: {path}\n"
            output += f"📄 文件模式: {file_pattern}\n"
            output += f"🔤 区分大小写: {'是' if case_sensitive else '否'}\n"
            output += "=" * 50 + "\n\n"
            
            total_matches = 0
            for result in results:
                output += f"\n📄 {result['file']} ({len(result['matches'])} 处匹配):\n"
                for match in result['matches'][:5]:  # 每个文件最多显示5个匹配
                    output += f"  第 {match['line_num']} 行: {match['content'][:100]}\n"
                if len(result['matches']) > 5:
                    output += f"  ... 还有 {len(result['matches']) - 5} 处匹配\n"
                total_matches += len(result['matches'])
            
            output += f"\n总计: 在 {len(results)} 个文件中找到 {total_matches} 处匹配"
            
            return output
            
        except Exception as e:
            return f"错误：{e}"
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def _generate_tree(self, path: Path, prefix: str = "", 
                      max_depth: int = 3, current_depth: int = 0) -> str:
        """生成目录树"""
        if current_depth >= max_depth:
            return prefix + "...\n"
        
        tree = ""
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            next_prefix = "    " if is_last else "│   "
            
            if item.is_dir():
                tree += prefix + current_prefix + f"📁 {item.name}/\n"
                if current_depth < max_depth - 1:
                    tree += self._generate_tree(
                        item, 
                        prefix + next_prefix, 
                        max_depth, 
                        current_depth + 1
                    )
            else:
                size = self._format_size(item.stat().st_size)
                tree += prefix + current_prefix + f"📄 {item.name} ({size})\n"
        
        return tree
    
    async def run(self):
        """运行MCP服务器"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions()
            )

async def main():
    """主函数"""
    print("🚀 启动文件管理MCP服务器...")
    print("=" * 50)
    
    # 创建并运行服务器
    server = FileManagerMCPServer(".")
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())