#!/usr/bin/env python3
"""
第7天：将RAG系统改造为MCP服务器
提供文档管理、检索和问答的MCP接口
"""

import asyncio
import os
import shutil
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server, stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Tool,
    Resource,
    TextContent,
    ResourceContents,
    TextResourceContents
)

# RAG相关导入
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.schema import Document

class RAGMCPServer:
    """
    RAG系统的MCP服务器
    将向量检索和问答功能暴露为MCP工具
    """
    
    def __init__(self, persist_directory: str = "./mcp_chroma_db"):
        """
        初始化RAG MCP服务器
        
        参数:
            persist_directory: 向量数据库持久化目录
        """
        self.server = Server("rag-system")
        self.persist_directory = persist_directory
        self.vectorstore = None
        self.embeddings = None
        self.llm = None
        
        print(f"🚀 初始化RAG MCP服务器")
        print(f"📁 数据库目录: {persist_directory}")
        
        # 初始化组件
        self._initialize_components()
        self._setup_handlers()
    
    def _initialize_components(self):
        """初始化RAG组件"""
        try:
            print("🔧 初始化嵌入模型...")
            # 使用本地嵌入模型
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            print("📚 初始化向量数据库...")
            # 初始化或加载向量数据库
            if os.path.exists(self.persist_directory):
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                print(f"✅ 加载现有数据库，包含 {self.vectorstore._collection.count()} 个文档")
            else:
                os.makedirs(self.persist_directory, exist_ok=True)
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                print("✅ 创建新的向量数据库")
            
            print("🤖 初始化语言模型...")
            # 初始化LLM（用于生成答案）
            self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
            print("✅ 所有组件初始化完成")
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            raise
    
    def _setup_handlers(self):
        """设置MCP处理器"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """定义可用的RAG工具"""
            return [
                Tool(
                    name="add_document",
                    description="添加文档到知识库",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "文档内容"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "文档元数据（如标题、来源、标签等）",
                                "default": {}
                            },
                            "chunk_size": {
                                "type": "integer",
                                "description": "文本分块大小",
                                "default": 500
                            },
                            "chunk_overlap": {
                                "type": "integer",
                                "description": "分块重叠大小",
                                "default": 50
                            }
                        },
                        "required": ["content"]
                    }
                ),
                Tool(
                    name="add_file",
                    description="从文件添加文档到知识库",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "encoding": {
                                "type": "string",
                                "description": "文件编码",
                                "default": "utf-8"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "额外的元数据",
                                "default": {}
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="search",
                    description="在知识库中搜索相关文档",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询"
                            },
                            "k": {
                                "type": "integer",
                                "description": "返回结果数量",
                                "default": 5
                            },
                            "filter": {
                                "type": "object",
                                "description": "元数据过滤条件",
                                "default": None
                            },
                            "include_scores": {
                                "type": "boolean",
                                "description": "是否包含相似度分数",
                                "default": False
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="answer_question",
                    description="基于知识库回答问题",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "要回答的问题"
                            },
                            "context_k": {
                                "type": "integer",
                                "description": "使用的上下文文档数量",
                                "default": 3
                            },
                            "include_sources": {
                                "type": "boolean",
                                "description": "是否在回答中包含信息来源",
                                "default": True
                            },
                            "temperature": {
                                "type": "number",
                                "description": "回答的创造性（0-1）",
                                "default": 0.1
                            }
                        },
                        "required": ["question"]
                    }
                ),
                Tool(
                    name="list_documents",
                    description="列出知识库中的文档信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "返回的文档数量限制",
                                "default": 10
                            },
                            "filter": {
                                "type": "object",\n",
                                "description": "元数据过滤条件",
                                "default": None
                            }
                        }
                    }
                ),
                Tool(
                    name="delete_documents",
                    description="从知识库删除文档",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "object",
                                "description": "删除条件（基于元数据）"
                            },
                            "confirm": {
                                "type": "boolean",
                                "description": "确认删除",
                                "default": False
                            }
                        },
                        "required": ["filter", "confirm"]
                    }
                ),
                Tool(
                    name="get_stats",
                    description="获取知识库统计信息",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """列出可用的资源"""
            return [
                Resource(
                    uri="rag://stats",
                    name="知识库统计",
                    description="当前知识库的统计信息",
                    mimeType="text/plain"
                ),
                Resource(
                    uri="rag://schema",
                    name="数据库模式",
                    description="向量数据库的结构信息",
                    mimeType="text/plain"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ResourceContents:
            """读取资源内容"""
            if uri == "rag://stats":
                stats = await self._get_detailed_stats()
                return TextResourceContents(
                    uri=uri,
                    mimeType="text/plain",
                    text=stats
                )
            elif uri == "rag://schema":
                schema = self._get_database_schema()
                return TextResourceContents(
                    uri=uri,
                    mimeType="text/plain",
                    text=schema
                )
            else:
                return TextResourceContents(
                    uri=uri,
                    mimeType="text/plain",
                    text=f"未知的资源: {uri}"
                )
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str,
            arguments: Dict[str, Any]
        ) -> list[TextContent]:
            """处理工具调用"""
            
            try:
                if name == "add_document":
                    result = await self._add_document(
                        arguments["content"],
                        arguments.get("metadata", {}),
                        arguments.get("chunk_size", 500),
                        arguments.get("chunk_overlap", 50)
                    )
                
                elif name == "add_file":
                    result = await self._add_file(
                        arguments["file_path"],
                        arguments.get("encoding", "utf-8"),
                        arguments.get("metadata", {})
                    )
                
                elif name == "search":
                    result = await self._search(
                        arguments["query"],
                        arguments.get("k", 5),
                        arguments.get("filter"),
                        arguments.get("include_scores", False)
                    )
                
                elif name == "answer_question":
                    result = await self._answer_question(
                        arguments["question"],
                        arguments.get("context_k", 3),
                        arguments.get("include_sources", True),
                        arguments.get("temperature", 0.1)
                    )
                
                elif name == "list_documents":
                    result = await self._list_documents(
                        arguments.get("limit", 10),
                        arguments.get("filter")
                    )
                
                elif name == "delete_documents":
                    result = await self._delete_documents(
                        arguments["filter"],
                        arguments.get("confirm", False)
                    )
                
                elif name == "get_stats":
                    result = await self._get_detailed_stats()
                
                else:
                    result = f"错误：未知的工具 - {name}"\n",
                
                return [TextContent(type="text", text=result)]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"错误：执行工具 {name} 时出错 - {str(e)}"
                )]
    
    async def _add_document(self, content: str, metadata: Dict, 
                          chunk_size: int, chunk_overlap: int) -> str:
        """添加文档到知识库"""
        try:
            if not content.strip():
                return "错误：文档内容不能为空"
            
            # 文本分割
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\\n\\n", "\\n", "。", "！", "？", "，", " ", ""]
            )
            
            chunks = text_splitter.split_text(content)
            
            if not chunks:
                return "错误：无法分割文档内容"
            
            # 为每个块添加元数据
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = i
                chunk_metadata["total_chunks"] = len(chunks)
                chunk_metadata["chunk_size"] = len(chunk)
                
                documents.append(Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                ))\n",
            
            # 添加到向量数据库
            self.vectorstore.add_documents(documents)
            
            # 持久化
            self.vectorstore.persist()
            
            return f"✅ 成功添加文档，共生成 {len(chunks)} 个文本块\\n" + \\\n",
                   f"📊 平均块大小: {sum(len(c) for c in chunks) // len(chunks)} 字符\\n" + \\\n",
                   f"📝 元数据: {metadata}"
            
        except Exception as e:
            return f"添加文档失败：{e}"
    
    async def _add_file(self, file_path: str, encoding: str, 
                       metadata: Dict) -> str:
        """从文件添加文档"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return f"错误：文件不存在 - {file_path}"
            
            if not path.is_file():
                return f"错误：{file_path} 不是文件"
            
            # 读取文件内容
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # 添加文件相关的元数据
            file_metadata = {
                "source": str(path),
                "filename": path.name,
                "file_extension": path.suffix,
                "file_size": path.stat().st_size,
                **metadata
            }
            
            # 调用添加文档方法
            return await self._add_document(content, file_metadata, 500, 50)
            
        except UnicodeDecodeError as e:
            return f"文件编码错误：{e}\\n提示：尝试使用不同的编码（如 gbk, latin1）"
        except Exception as e:
            return f"添加文件失败：{e}"
    
    async def _search(self, query: str, k: int, filter: Optional[Dict], 
                     include_scores: bool) -> str:
        """搜索相关文档"""
        try:
            if not query.strip():
                return "错误：搜索查询不能为空"
            
            # 执行搜索
            if include_scores:
                # 带分数的搜索
                if filter:
                    results = self.vectorstore.similarity_search_with_score(
                        query, k=k, filter=filter
                    )
                else:
                    results = self.vectorstore.similarity_search_with_score(
                        query, k=k
                    )
                
                if not results:
                    return "没有找到相关文档"
                
                # 格式化带分数的结果
                output = f"🔍 找到 {len(results)} 个相关文档 (查询: '{query}'):\\n\\n"
                
                for i, (doc, score) in enumerate(results, 1):
                    output += f"[文档 {i}] (相似度: {score:.4f})\\n"
                    output += f"内容: {doc.page_content[:200]}"
                    if len(doc.page_content) > 200:
                        output += "..."
                    output += f"\\n元数据: {doc.metadata}\\n"
                    output += "-" * 60 + "\\n"
            else:
                # 普通搜索
                if filter:
                    results = self.vectorstore.similarity_search(
                        query, k=k, filter=filter
                    )
                else:
                    results = self.vectorstore.similarity_search(query, k=k)
                
                if not results:
                    return "没有找到相关文档"
                
                # 格式化结果
                output = f"🔍 找到 {len(results)} 个相关文档 (查询: '{query}'):\\n\\n"
                
                for i, doc in enumerate(results, 1):
                    output += f"[文档 {i}]\\n"
                    output += f"内容: {doc.page_content[:200]}"
                    if len(doc.page_content) > 200:
                        output += "..."
                    output += f"\\n元数据: {doc.metadata}\\n"
                    output += "-" * 60 + "\\n"
            
            return output
            
        except Exception as e:
            return f"搜索失败：{e}"
    
    async def _answer_question(self, question: str, context_k: int, 
                             include_sources: bool, temperature: float) -> str:
        """基于知识库回答问题"""
        try:
            if not question.strip():
                return "错误：问题不能为空"
            
            # 搜索相关文档
            docs = self.vectorstore.similarity_search_with_score(
                question, k=context_k
            )
            
            if not docs:
                return "❌ 知识库中没有找到相关信息来回答这个问题"
            
            # 构建上下文
            context_parts = []
            sources = []
            
            for i, (doc, score) in enumerate(docs, 1):
                context_parts.append(f"[上下文 {i}]: {doc.page_content}")
                
                # 收集来源信息
                source_info = doc.metadata.get("source", f"文档块 {i}")
                if "filename" in doc.metadata:
                    source_info = doc.metadata["filename"]
                sources.append(f"{source_info} (相似度: {score:.3f})")
            
            context = "\\n\\n".join(context_parts)
            
            # 构建提示词
            prompt = f"""基于以下上下文信息回答问题。请给出准确、有用的回答。如果上下文中没有足够的信息来完整回答问题，请明确说明。

上下文信息：
{context}

问题：{question}

请基于上下文信息提供详细的回答："""
            
            # 设置温度
            self.llm.temperature = temperature
            
            # 生成答案
            response = await self.llm.ainvoke(prompt)
            
            # 构建完整回答
            answer = f"🤖 **回答**\\n\\n{response.content}\\n\\n"
            
            if include_sources:
                answer += f"📚 **信息来源** (基于 {len(docs)} 个相关文档):\\n"
                for i, source in enumerate(sources, 1):
                    answer += f"  {i}. {source}\\n"
            
            # 添加搜索统计
            answer += f"\\n🔍 **检索统计**\\n"
            answer += f"  - 查询问题: {question}\\n"
            answer += f"  - 检索到的文档数量: {len(docs)}\\n"
            answer += f"  - 最高相似度: {docs[0][1]:.3f}\\n"
            answer += f"  - 回答温度: {temperature}\\n"
            
            return answer
            
        except Exception as e:
            return f"回答问题失败：{e}"
    
    async def _list_documents(self, limit: int, 
                            filter: Optional[Dict]) -> str:
        """列出知识库中的文档"""
        try:
            # 获取文档
            collection = self.vectorstore._collection
            
            # 构建查询参数
            query_params = {"limit": limit}
            if filter:
                query_params["where"] = filter
            
            results = collection.get(**query_params)
            
            if not results['documents']:
                return "知识库为空"
            
            # 分析文档
            documents = results['documents']
            metadatas = results['metadatas']
            
            output = f"📚 知识库文档列表 (显示前 {len(documents)} 个):\\n\\n"
            
            # 按源文件分组
            source_groups = {}
            for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
                source = metadata.get("source", metadata.get("filename", "未知来源"))
                if source not in source_groups:
                    source_groups[source] = []
                source_groups[source].append((doc, metadata, i))
            
            # 显示分组信息
            for source, items in source_groups.items():
                output += f"📄 **{source}** ({len(items)} 个文档块)\\n"
                
                for doc, metadata, idx in items[:3]:  # 每个源最多显示3个块
                    chunk_info = ""
                    if "chunk_index" in metadata:
                        chunk_info = f" [块 {metadata['chunk_index'] + 1}/{metadata.get('total_chunks', '?')}]"
                    
                    output += f"  {idx + 1}.{chunk_info} {doc[:100]}"
                    if len(doc) > 100:
                        output += "..."
                    output += "\\n"
                
                if len(items) > 3:
                    output += f"  ... 还有 {len(items) - 3} 个块\\n"
                
                output += "\\n"
            
            # 统计信息
            total_chars = sum(len(doc) for doc in documents)
            avg_chars = total_chars // len(documents) if documents else 0
            
            output += f"📊 **统计信息**\\n"
            output += f"  - 总文档块数: {len(documents)}\\n"
            output += f"  - 不同来源数: {len(source_groups)}\\n"
            output += f"  - 总字符数: {total_chars:,}\\n"
            output += f"  - 平均块大小: {avg_chars} 字符\\n"
            
            return output
            
        except Exception as e:
            return f"列出文档失败：{e}"
    
    async def _delete_documents(self, filter: Dict, confirm: bool) -> str:
        """删除文档"""
        try:
            if not confirm:
                return "❌ 删除操作需要确认。请设置 confirm=true"
            
            if not filter:
                return "❌ 删除操作需要提供过滤条件以确保安全"
            
            # 先查询要删除的文档
            collection = self.vectorstore._collection
            to_delete = collection.get(where=filter)
            
            if not to_delete['ids']:
                return f"没有找到匹配条件的文档: {filter}"
            
            # 执行删除
            collection.delete(where=filter)
            
            # 持久化
            self.vectorstore.persist()
            
            return f"✅ 成功删除 {len(to_delete['ids'])} 个文档\\n" + \\\n",
                   f"删除条件: {filter}"
            
        except Exception as e:
            return f"删除文档失败：{e}"
    
    async def _get_detailed_stats(self) -> str:
        """获取详细统计信息"""
        try:
            collection = self.vectorstore._collection
            results = collection.get()
            
            if not results['documents']:
                return "📊 知识库统计信息\\n\\n❌ 知识库为空"
            
            documents = results['documents']
            metadatas = results['metadatas']
            
            # 基础统计
            total_docs = len(documents)
            total_chars = sum(len(doc) for doc in documents)
            avg_chars = total_chars // total_docs if total_docs > 0 else 0
            
            # 按来源统计
            sources = {}
            extensions = {}
            chunk_sizes = []
            
            for doc, metadata in zip(documents, metadatas):
                # 来源统计
                source = metadata.get("source", metadata.get("filename", "未知"))
                sources[source] = sources.get(source, 0) + 1
                
                # 扩展名统计
                if "file_extension" in metadata:
                    ext = metadata["file_extension"]
                    extensions[ext] = extensions.get(ext, 0) + 1
                
                # 块大小统计
                chunk_sizes.append(len(doc))
            
            # 构建统计报告
            stats = f"📊 **知识库详细统计信息**\\n\\n"
            
            # 基础信息
            stats += f"🔢 **基础统计**\\n"
            stats += f"  - 总文档块数: {total_docs:,}\\n"
            stats += f"  - 总字符数: {total_chars:,}\\n"
            stats += f"  - 平均块大小: {avg_chars} 字符\\n"
            stats += f"  - 最大块大小: {max(chunk_sizes)} 字符\\n"
            stats += f"  - 最小块大小: {min(chunk_sizes)} 字符\\n"
            stats += f"  - 数据库路径: {self.persist_directory}\\n\\n"
            
            # 来源分布
            stats += f"📁 **来源分布** (Top 10)\\n"
            top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]
            for source, count in top_sources:
                percentage = (count / total_docs) * 100
                stats += f"  - {source}: {count} 块 ({percentage:.1f}%)\\n"
            if len(sources) > 10:
                stats += f"  ... 还有 {len(sources) - 10} 个来源\\n"
            stats += "\\n"
            
            # 文件类型分布
            if extensions:
                stats += f"📄 **文件类型分布**\\n"
                for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_docs) * 100
                    stats += f"  - {ext or '无扩展名'}: {count} 块 ({percentage:.1f}%)\\n"
                stats += "\\n"
            
            # 系统信息
            stats += f"⚙️ **系统信息**\\n"
            stats += f"  - 嵌入模型: sentence-transformers/all-MiniLM-L6-v2\\n"
            stats += f"  - 向量维度: 384\\n"
            stats += f"  - 数据库类型: Chroma\\n"
            
            return stats
            
        except Exception as e:
            return f"获取统计信息失败：{e}"
    
    def _get_database_schema(self) -> str:
        """获取数据库模式信息"""
        try:
            schema = f"🗄️ **向量数据库模式信息**\\n\\n"
            
            schema += f"**基础配置**\\n"
            schema += f"  - 数据库类型: ChromaDB\\n"
            schema += f"  - 持久化目录: {self.persist_directory}\\n"
            schema += f"  - 嵌入函数: HuggingFaceEmbeddings\\n"
            schema += f"  - 模型名称: sentence-transformers/all-MiniLM-L6-v2\\n"
            schema += f"  - 向量维度: 384\\n\\n"
            
            schema += f"**数据结构**\\n"
            schema += f"  - 文档内容: page_content (text)\\n"
            schema += f"  - 向量嵌入: embeddings (float[384])\\n"
            schema += f"  - 元数据字段:\\n"
            schema += f"    • source: 文档来源\\n"
            schema += f"    • filename: 文件名\\n"
            schema += f"    • file_extension: 文件扩展名\\n"
            schema += f"    • file_size: 文件大小\\n"
            schema += f"    • chunk_index: 块索引\\n"
            schema += f"    • total_chunks: 总块数\\n"
            schema += f"    • chunk_size: 块大小\\n"
            schema += f"    • 自定义元数据...\\n\\n"
            
            schema += f"**支持的操作**\\n"
            schema += f"  - similarity_search: 向量相似度搜索\\n"
            schema += f"  - similarity_search_with_score: 带分数的搜索\\n"
            schema += f"  - add_documents: 添加文档\\n"
            schema += f"  - delete: 删除文档\\n"
            schema += f"  - get: 获取文档\\n"
            schema += f"  - persist: 持久化数据\\n"
            
            return schema
            
        except Exception as e:
            return f"获取数据库模式失败：{e}"
    
    async def run(self):
        """运行MCP服务器"""
        print("\\n🎯 启动RAG MCP服务器...")
        print("📡 等待客户端连接...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions()
            )

async def main():
    """主函数"""
    print("🚀 RAG系统MCP服务器")
    print("=" * 50)
    print("📚 功能: 文档管理、向量检索、智能问答")
    print("🔧 技术栈: LangChain + Chroma + OpenAI")
    print("=" * 50)
    
    # 创建并运行服务器
    server = RAGMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())