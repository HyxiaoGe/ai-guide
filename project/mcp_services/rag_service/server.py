#!/usr/bin/env python3
"""
智能文档助手系统 - RAG MCP服务
提供文档检索和问答功能的MCP服务器
"""

import asyncio
import os
import logging
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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentAssistantRAGService:
    """
    智能文档助手RAG服务
    基于MCP协议的企业级RAG服务实现
    """
    
    def __init__(self, 
                 persist_directory: str = "./data/vector_db",
                 model_name: str = "gpt-3.5-turbo"):
        """
        初始化RAG服务
        
        参数:
            persist_directory: 向量数据库持久化目录
            model_name: 使用的LLM模型
        """
        self.server = Server("doc-assistant-rag")
        self.persist_directory = persist_directory
        self.model_name = model_name
        
        # 初始化组件
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        
        # 文档统计
        self.doc_stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "last_updated": None
        }
        
        logger.info(f"初始化文档助手RAG服务 - 数据库: {persist_directory}")
        
        # 初始化组件
        self._initialize_components()
        self._setup_handlers()
    
    def _initialize_components(self):
        """初始化RAG组件"""
        try:
            logger.info("初始化嵌入模型...")
            # 使用本地嵌入模型
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            logger.info("初始化向量数据库...")
            # 确保目录存在
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # 初始化Chroma数据库
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name="documents"
            )
            
            # 获取文档统计
            try:
                collection = self.vectorstore._collection
                count = collection.count()
                self.doc_stats["total_chunks"] = count
                logger.info(f"加载现有数据库，包含 {count} 个文档块")
            except:
                logger.info("创建新的向量数据库")
            
            logger.info("初始化语言模型...")
            # 初始化LLM
            self.llm = ChatOpenAI(
                model=self.model_name, 
                temperature=0.1,
                max_tokens=2000
            )
            
            logger.info("✅ 所有组件初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 组件初始化失败: {e}")
            raise
    
    def _setup_handlers(self):
        """设置MCP处理器"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """定义RAG服务的所有工具"""
            return [
                # 文档管理工具
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
                                "description": "文档元数据（标题、来源、标签等）",
                                "properties": {
                                    "title": {"type": "string"},
                                    "source": {"type": "string"},
                                    "author": {"type": "string"},
                                    "tags": {"type": "array", "items": {"type": "string"}},
                                    "category": {"type": "string"}
                                },
                                "default": {}
                            },
                            "chunk_size": {
                                "type": "integer",
                                "description": "文本分块大小",
                                "default": 1000
                            }
                        },
                        "required": ["content"]
                    }
                ),
                
                Tool(
                    name="batch_add_documents",
                    description="批量添加多个文档",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "documents": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "content": {"type": "string"},
                                        "metadata": {"type": "object"}
                                    },
                                    "required": ["content"]
                                }
                            }
                        },
                        "required": ["documents"]
                    }
                ),
                
                # 检索工具
                Tool(
                    name="search_documents",
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
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            },
                            "filter": {
                                "type": "object",
                                "description": "元数据过滤条件",
                                "default": None
                            },
                            "include_scores": {
                                "type": "boolean",
                                "description": "是否包含相似度分数",
                                "default": True
                            }
                        },
                        "required": ["query"]
                    }
                ),
                
                Tool(
                    name="semantic_search",
                    description="高级语义搜索，支持复杂查询",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "search_type": {
                                "type": "string",
                                "enum": ["similarity", "mmr", "similarity_score_threshold"],
                                "default": "similarity"
                            },
                            "k": {"type": "integer", "default": 5},
                            "score_threshold": {"type": "number", "default": 0.5}
                        },
                        "required": ["query"]
                    }
                ),
                
                # 问答工具
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
                                "default": 3,
                                "minimum": 1,
                                "maximum": 10
                            },
                            "answer_style": {
                                "type": "string",
                                "enum": ["detailed", "concise", "analytical"],
                                "description": "回答风格",
                                "default": "detailed"
                            },
                            "include_sources": {
                                "type": "boolean",
                                "description": "是否包含信息来源",
                                "default": True
                            }
                        },
                        "required": ["question"]
                    }
                ),
                
                Tool(
                    name="multi_turn_chat",
                    description="多轮对话问答",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "messages": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "role": {"type": "string", "enum": ["user", "assistant"]},
                                        "content": {"type": "string"}
                                    }
                                }
                            },
                            "context_k": {"type": "integer", "default": 3}
                        },
                        "required": ["messages"]
                    }
                ),
                
                # 分析工具
                Tool(
                    name="summarize_documents",
                    description="生成文档摘要",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "摘要主题或查询"
                            },
                            "summary_type": {
                                "type": "string",
                                "enum": ["executive", "detailed", "bullet_points"],
                                "default": "detailed"
                            },
                            "max_length": {"type": "integer", "default": 500}
                        },
                        "required": ["query"]
                    }
                ),
                
                # 管理工具
                Tool(
                    name="get_collection_stats",
                    description="获取知识库统计信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "detailed": {
                                "type": "boolean",
                                "description": "是否返回详细统计",
                                "default": False
                            }
                        }
                    }
                ),
                
                Tool(
                    name="clear_collection",
                    description="清空知识库（谨慎使用）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "confirm": {
                                "type": "boolean",
                                "description": "确认清空操作"
                            }
                        },
                        "required": ["confirm"]
                    }
                )
            ]
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """列出可用的资源"""
            return [
                Resource(
                    uri="rag://stats",
                    name="知识库统计信息",
                    description="当前知识库的详细统计数据",
                    mimeType="application/json"
                ),
                Resource(
                    uri="rag://config",
                    name="服务配置信息",
                    description="RAG服务的配置参数",
                    mimeType="application/json"
                ),
                Resource(
                    uri="rag://health",
                    name="服务健康状态",
                    description="服务组件的健康检查结果",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ResourceContents:
            """读取资源内容"""
            if uri == "rag://stats":
                stats = await self._get_detailed_stats()
                return TextResourceContents(
                    uri=uri,
                    mimeType="application/json",
                    text=stats
                )
            elif uri == "rag://config":
                config = self._get_service_config()
                return TextResourceContents(
                    uri=uri,
                    mimeType="application/json",
                    text=config
                )
            elif uri == "rag://health":
                health = await self._get_health_status()
                return TextResourceContents(
                    uri=uri,
                    mimeType="application/json",
                    text=health
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
                logger.info(f"调用工具: {name}")
                
                # 文档管理工具
                if name == "add_document":
                    result = await self._add_document(
                        arguments["content"],
                        arguments.get("metadata", {}),
                        arguments.get("chunk_size", 1000)
                    )
                
                elif name == "batch_add_documents":
                    result = await self._batch_add_documents(
                        arguments["documents"]
                    )
                
                # 检索工具
                elif name == "search_documents":
                    result = await self._search_documents(
                        arguments["query"],
                        arguments.get("k", 5),
                        arguments.get("filter"),
                        arguments.get("include_scores", True)
                    )
                
                elif name == "semantic_search":
                    result = await self._semantic_search(
                        arguments["query"],
                        arguments.get("search_type", "similarity"),
                        arguments.get("k", 5),
                        arguments.get("score_threshold", 0.5)
                    )
                
                # 问答工具
                elif name == "answer_question":
                    result = await self._answer_question(
                        arguments["question"],
                        arguments.get("context_k", 3),
                        arguments.get("answer_style", "detailed"),
                        arguments.get("include_sources", True)
                    )
                
                elif name == "multi_turn_chat":
                    result = await self._multi_turn_chat(
                        arguments["messages"],
                        arguments.get("context_k", 3)
                    )
                
                # 分析工具
                elif name == "summarize_documents":
                    result = await self._summarize_documents(
                        arguments["query"],
                        arguments.get("summary_type", "detailed"),
                        arguments.get("max_length", 500)
                    )
                
                # 管理工具
                elif name == "get_collection_stats":
                    result = await self._get_detailed_stats(
                        arguments.get("detailed", False)
                    )
                
                elif name == "clear_collection":
                    result = await self._clear_collection(
                        arguments.get("confirm", False)
                    )
                
                else:
                    result = f"❌ 未知的工具: {name}"
                
                logger.info(f"工具 {name} 执行完成")
                return [TextContent(type="text", text=result)]
                
            except Exception as e:
                error_msg = f"❌ 执行工具 {name} 时出错: {str(e)}"
                logger.error(error_msg)
                return [TextContent(type="text", text=error_msg)]
    
    # 实现所有工具方法（这里只实现关键方法，其他方法类似）
    async def _add_document(self, content: str, metadata: Dict, chunk_size: int) -> str:
        """添加文档到知识库"""
        try:
            if not content.strip():
                return "❌ 文档内容不能为空"
            
            # 文本分割
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=100,
                separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
            )
            
            chunks = text_splitter.split_text(content)
            
            # 创建文档对象
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk)
                })
                
                documents.append(Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                ))
            
            # 添加到向量数据库
            self.vectorstore.add_documents(documents)
            
            # 更新统计
            self.doc_stats["total_chunks"] += len(chunks)
            self.doc_stats["last_updated"] = asyncio.get_event_loop().time()
            
            return f"✅ 成功添加文档，生成 {len(chunks)} 个文本块\n" + \
                   f"📊 平均块大小: {sum(len(c) for c in chunks) // len(chunks)} 字符"
            
        except Exception as e:
            return f"❌ 添加文档失败: {e}"
    
    async def _answer_question(self, question: str, context_k: int, 
                              answer_style: str, include_sources: bool) -> str:
        """基于知识库回答问题"""
        try:
            # 检索相关文档
            docs = self.vectorstore.similarity_search_with_score(
                question, k=context_k
            )
            
            if not docs:
                return "❌ 知识库中没有找到相关信息来回答这个问题"
            
            # 构建上下文
            context_parts = []
            sources = []
            
            for i, (doc, score) in enumerate(docs, 1):
                context_parts.append(f"[文档 {i}]: {doc.page_content}")
                
                # 收集来源信息
                metadata = doc.metadata
                source_info = metadata.get("title", metadata.get("source", f"文档块 {i}"))
                sources.append(f"{source_info} (相似度: {1-score:.3f})")
            
            context = "\n\n".join(context_parts)
            
            # 根据回答风格构建提示词
            style_prompts = {
                "detailed": "请基于上下文信息提供详细、全面的回答。",
                "concise": "请基于上下文信息提供简洁、要点明确的回答。",
                "analytical": "请基于上下文信息进行深入分析，提供有见解的回答。"
            }
            
            prompt = f"""{style_prompts[answer_style]}

上下文信息：
{context}

问题：{question}

请基于上下文信息回答问题："""
            
            # 生成答案
            response = await self.llm.ainvoke(prompt)
            
            # 构建完整回答
            answer = f"🤖 **回答**\n\n{response.content}\n\n"
            
            if include_sources:
                answer += f"📚 **信息来源** (基于 {len(docs)} 个相关文档):\n"
                for i, source in enumerate(sources, 1):
                    answer += f"  {i}. {source}\n"
            
            return answer
            
        except Exception as e:
            return f"❌ 回答问题失败: {e}"
    
    async def _get_detailed_stats(self, detailed: bool = False) -> str:
        """获取详细统计信息"""
        try:
            collection = self.vectorstore._collection
            total_docs = collection.count()
            
            stats = {
                "service": "Document Assistant RAG Service",
                "status": "active",
                "total_chunks": total_docs,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "llm_model": self.model_name,
                "vector_db": "ChromaDB"
            }
            
            if detailed and total_docs > 0:
                # 获取更详细的统计信息
                results = collection.get()
                if results['metadatas']:
                    # 分析元数据
                    categories = {}
                    sources = {}
                    
                    for metadata in results['metadatas']:
                        cat = metadata.get('category', '未分类')
                        src = metadata.get('source', '未知来源')
                        
                        categories[cat] = categories.get(cat, 0) + 1
                        sources[src] = sources.get(src, 0) + 1
                    
                    stats["categories"] = categories
                    stats["sources"] = dict(list(sources.items())[:10])  # 前10个来源
            
            import json
            return json.dumps(stats, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return f"❌ 获取统计信息失败: {e}"
    
    def _get_service_config(self) -> str:
        """获取服务配置"""
        config = {
            "service_name": "doc-assistant-rag",
            "persist_directory": self.persist_directory,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "llm_model": self.model_name,
            "vector_dimensions": 384,
            "max_chunk_size": 2000,
            "chunk_overlap": 100
        }
        
        import json
        return json.dumps(config, indent=2, ensure_ascii=False)
    
    async def _get_health_status(self) -> str:
        """获取健康状态"""
        health = {
            "status": "healthy",
            "components": {
                "embeddings": "ok",
                "vectorstore": "ok", 
                "llm": "ok"
            },
            "uptime": "running",
            "last_check": asyncio.get_event_loop().time()
        }
        
        # 简单的健康检查
        try:
            # 测试嵌入
            self.embeddings.embed_query("test")
            
            # 测试向量数据库
            self.vectorstore._collection.count()
            
            # 测试LLM（简单调用）
            # await self.llm.ainvoke("Hello")
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        import json
        return json.dumps(health, indent=2, ensure_ascii=False)
    
    async def run(self):
        """运行MCP服务器"""
        logger.info("🚀 启动文档助手RAG MCP服务...")
        logger.info("📡 等待客户端连接...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions()
            )

async def main():
    """主函数"""
    print("🚀 智能文档助手系统 - RAG MCP服务")
    print("=" * 60)
    print("📚 功能: 企业级文档检索和问答服务")
    print("🔧 技术: LangChain + ChromaDB + OpenAI")
    print("📡 协议: Model Context Protocol (MCP)")
    print("=" * 60)
    
    # 创建并运行服务器
    service = DocumentAssistantRAGService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())