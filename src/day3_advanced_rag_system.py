#!/usr/bin/env python3
"""
第3天：高级RAG（检索增强生成）系统
集成向量数据库、混合搜索、查询优化等功能
"""

import os
import time
import shutil
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# LangChain相关导入
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.retrievers import BM25Retriever, EnsembleRetriever

# 环境配置
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"


@dataclass
class DocumentChunk:
    """文档块数据类"""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str


class RAGResponse(BaseModel):
    """RAG系统响应模型"""
    answer: str = Field(description="基于检索文档生成的答案")
    confidence: float = Field(description="答案置信度 (0-1)", ge=0, le=1)
    sources: List[str] = Field(description="参考文档来源列表")
    retrieved_chunks: int = Field(description="检索到的文档块数量")
    search_method: str = Field(description="使用的搜索方法")
    has_sufficient_context: bool = Field(description="是否有足够的上下文信息")


class AdvancedRAGSystem:
    """高级RAG系统实现"""
    
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        embedding_model: str = "text-embedding-ada-002",
        chunk_size: int = 300,
        chunk_overlap: int = 50,
        vector_db_type: str = "chroma"
    ):
        """
        初始化RAG系统
        
        参数:
            model_name: 使用的LLM模型
            embedding_model: 嵌入模型
            chunk_size: 文档分块大小
            chunk_overlap: 分块重叠大小
            vector_db_type: 向量数据库类型 ("chroma" 或 "faiss")
        """
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.vector_db_type = vector_db_type
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\\n\\n", "\\n", "。", "！", "？", ";", ",", " ", ""]
        )
        
        # 向量存储
        self.vectorstore = None
        self.bm25_retriever = None
        self.hybrid_retriever = None
        
        # 提示词模板
        self._setup_prompts()
        
        print(f"🤖 RAG系统初始化完成")
        print(f"   LLM: {model_name}")
        print(f"   向量数据库: {vector_db_type}")
        print(f"   分块大小: {chunk_size}")
    
    def _setup_prompts(self):
        """设置提示词模板"""
        
        # 基础RAG提示词
        self.basic_rag_prompt = ChatPromptTemplate.from_template("""
        你是一个专业的AI助手，请基于以下检索到的文档回答用户的问题。
        
        检索到的相关文档:
        {context}
        
        用户问题: {question}
        
        请遵循以下要求：
        1. 基于提供的文档内容回答问题
        2. 如果文档中没有相关信息，请明确说明
        3. 保持回答的准确性和客观性
        4. 可以适当整合多个文档的信息
        
        回答:
        """)
        
        # 高级RAG提示词（结构化输出）
        self.advanced_rag_prompt = ChatPromptTemplate.from_template("""
        你是一个AI专家，请基于检索到的文档回答问题，并提供详细的分析。
        
        检索文档:
        {context}
        
        用户问题: {question}
        
        请分析文档的相关性和信息充分性，并评估答案的置信度。
        
        {format_instructions}
        """)
        
        # 查询优化提示词
        self.query_optimization_prompt = ChatPromptTemplate.from_template("""
        作为查询优化专家，请将用户查询转换为更有效的搜索查询。
        
        原始查询: {query}
        
        请生成3个优化版本：
        1. 添加相关技术术语的具体化查询
        2. 使用同义词和相关概念的扩展查询  
        3. 分解为子问题的结构化查询
        
        输出格式：
        具体化: [查询1]
        扩展: [查询2]
        结构化: [查询3]
        """)
    
    def load_documents(self, documents: List[Dict[str, Any]]) -> List[Document]:
        """
        加载和处理文档
        
        参数:
            documents: 文档列表，每个文档包含content和metadata
        返回:
            处理后的Document对象列表
        """
        print(f"📚 正在加载 {len(documents)} 个文档...")
        
        doc_objects = []
        for i, doc_data in enumerate(documents):
            doc = Document(
                page_content=doc_data["content"].strip(),
                metadata={
                    **doc_data.get("metadata", {}),
                    "doc_id": i,
                    "source": doc_data.get("title", f"Document_{i}")
                }
            )
            doc_objects.append(doc)
        
        # 文档分块
        splits = self.text_splitter.split_documents(doc_objects)
        print(f"📄 文档分块完成: {len(doc_objects)} -> {len(splits)} 块")
        
        return splits
    
    def build_vector_database(self, documents: List[Document], persist_path: str = None):
        """
        构建向量数据库
        
        参数:
            documents: 文档列表
            persist_path: 持久化路径
        """
        print(f"🔨 正在构建{self.vector_db_type.upper()}向量数据库...")
        
        if self.vector_db_type == "chroma":
            if persist_path and os.path.exists(persist_path):
                shutil.rmtree(persist_path)
            
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=persist_path,
                collection_name="rag_collection"
            )
            
        elif self.vector_db_type == "faiss":
            self.vectorstore = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            
            if persist_path:
                self.vectorstore.save_local(persist_path)
        
        # 创建BM25检索器（关键词搜索）
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = 5
        
        # 创建混合检索器
        semantic_retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        self.hybrid_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, semantic_retriever],
            weights=[0.3, 0.7]  # BM25: 30%, 语义搜索: 70%
        )
        
        print(f"✅ 向量数据库构建完成，包含 {len(documents)} 个文档块")
    
    def optimize_query(self, query: str) -> List[str]:
        """
        查询优化：生成多个搜索变体
        
        参数:
            query: 原始查询
        返回:
            优化后的查询列表
        """
        try:
            chain = self.query_optimization_prompt | self.llm | StrOutputParser()
            result = chain.invoke({"query": query})
            
            # 解析结果
            optimized_queries = [query]  # 包含原始查询
            lines = result.strip().split('\\n')
            
            for line in lines:
                if ':' in line:
                    optimized_query = line.split(':', 1)[1].strip()
                    if optimized_query and optimized_query not in optimized_queries:
                        optimized_queries.append(optimized_query)
            
            return optimized_queries[:4]  # 最多返回4个查询
            
        except Exception as e:
            print(f"查询优化失败: {e}")
            return [query]
    
    def retrieve_documents(
        self, 
        query: str, 
        method: str = "hybrid",
        k: int = 5,
        use_query_optimization: bool = False
    ) -> List[Document]:
        """
        检索相关文档
        
        参数:
            query: 查询文本
            method: 检索方法 ("semantic", "bm25", "hybrid")
            k: 返回文档数量
            use_query_optimization: 是否使用查询优化
        返回:
            检索到的文档列表
        """
        if not self.vectorstore:
            raise ValueError("向量数据库未初始化，请先调用build_vector_database")
        
        queries = [query]
        if use_query_optimization:
            queries = self.optimize_query(query)
            print(f"🔍 使用优化查询: {len(queries)} 个变体")
        
        # 收集所有检索结果
        all_docs = []
        doc_scores = {}
        
        for q in queries:
            if method == "semantic":
                docs = self.vectorstore.similarity_search(q, k=k)
            elif method == "bm25":
                docs = self.bm25_retriever.get_relevant_documents(q)[:k]
            elif method == "hybrid":
                docs = self.hybrid_retriever.get_relevant_documents(q)[:k]
            else:
                raise ValueError(f"不支持的检索方法: {method}")
            
            # 计算文档得分（基于出现频次）
            for doc in docs:
                doc_id = doc.metadata.get('source', 'unknown')
                if doc_id in doc_scores:
                    doc_scores[doc_id] += 1
                else:
                    doc_scores[doc_id] = 1
                    all_docs.append(doc)
        
        # 按得分排序并返回top-k
        sorted_docs = sorted(
            all_docs, 
            key=lambda x: doc_scores[x.metadata.get('source', 'unknown')], 
            reverse=True
        )
        
        return sorted_docs[:k]
    
    def format_context(self, documents: List[Document]) -> str:
        """格式化检索到的文档为上下文"""
        if not documents:
            return "没有找到相关文档。"
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', f'文档{i}')
            content = doc.page_content.strip()
            context_parts.append(f"[文档{i}: {source}]\\n{content}")
        
        return "\\n\\n".join(context_parts)
    
    def generate_answer(
        self, 
        query: str, 
        method: str = "hybrid",
        use_advanced: bool = False,
        use_query_optimization: bool = False
    ) -> Dict[str, Any]:
        """
        生成RAG答案
        
        参数:
            query: 用户查询
            method: 检索方法
            use_advanced: 是否使用高级模式（结构化输出）
            use_query_optimization: 是否使用查询优化
        返回:
            包含答案和元信息的字典
        """
        start_time = time.time()
        
        # 检索文档
        documents = self.retrieve_documents(
            query, 
            method=method, 
            k=5,
            use_query_optimization=use_query_optimization
        )
        
        # 格式化上下文
        context = self.format_context(documents)
        
        # 生成答案
        if use_advanced:
            # 使用结构化输出
            parser = PydanticOutputParser(pydantic_object=RAGResponse)
            
            chain = (
                self.advanced_rag_prompt | 
                self.llm | 
                parser
            )
            
            try:
                response = chain.invoke({
                    "context": context,
                    "question": query,
                    "format_instructions": parser.get_format_instructions()
                })
                
                result = {
                    "answer": response.answer,
                    "confidence": response.confidence,
                    "sources": response.sources,
                    "retrieved_chunks": len(documents),
                    "search_method": method,
                    "has_sufficient_context": response.has_sufficient_context,
                    "processing_time": time.time() - start_time,
                    "retrieved_documents": documents
                }
                
            except Exception as e:
                print(f"结构化输出解析失败: {e}")
                # 回退到基础模式
                use_advanced = False
        
        if not use_advanced:
            # 基础模式
            chain = (
                self.basic_rag_prompt |
                self.llm |
                StrOutputParser()
            )
            
            answer = chain.invoke({
                "context": context,
                "question": query
            })
            
            result = {
                "answer": answer,
                "retrieved_chunks": len(documents),
                "search_method": method,
                "processing_time": time.time() - start_time,
                "retrieved_documents": documents,
                "sources": [doc.metadata.get('source', 'Unknown') for doc in documents]
            }
        
        return result
    
    def evaluate_retrieval(self, test_cases: List[Dict]) -> Dict[str, float]:
        """
        评估检索性能
        
        参数:
            test_cases: 测试用例列表，包含query和expected_sources
        返回:
            评估指标字典
        """
        print("📊 开始检索性能评估...")
        
        methods = ["semantic", "bm25", "hybrid"]
        results = {method: {"precision": 0, "recall": 0, "f1": 0} for method in methods}
        
        for method in methods:
            precision_scores = []
            recall_scores = []
            
            for test_case in test_cases:
                query = test_case["query"]
                expected_sources = set(test_case["expected_sources"])
                
                # 检索文档
                retrieved_docs = self.retrieve_documents(query, method=method, k=5)
                retrieved_sources = set([doc.metadata.get('source', '') for doc in retrieved_docs])
                
                # 计算精确率和召回率
                if retrieved_sources:
                    precision = len(expected_sources & retrieved_sources) / len(retrieved_sources)
                    precision_scores.append(precision)
                
                if expected_sources:
                    recall = len(expected_sources & retrieved_sources) / len(expected_sources)
                    recall_scores.append(recall)
            
            # 计算平均指标
            avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0
            avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0
            f1_score = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0
            
            results[method] = {
                "precision": avg_precision,
                "recall": avg_recall,
                "f1": f1_score
            }
            
            print(f"{method.upper()} - P: {avg_precision:.3f}, R: {avg_recall:.3f}, F1: {f1_score:.3f}")
        
        return results


def create_sample_knowledge_base():
    """创建示例知识库"""
    return [
        {
            "title": "人工智能基础",
            "content": """
            人工智能（Artificial Intelligence, AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的机器和软件。
            AI的主要目标包括学习、推理、感知、语言理解和问题解决。现代AI主要基于机器学习技术，特别是深度学习。
            AI应用广泛，包括自然语言处理、计算机视觉、语音识别、推荐系统、自动驾驶等领域。
            """,
            "metadata": {"category": "基础概念", "keywords": ["人工智能", "AI", "机器学习"]}
        },
        {
            "title": "深度学习技术",
            "content": """
            深度学习是机器学习的一个子集，使用多层神经网络来建模和理解复杂的数据模式。
            卷积神经网络（CNN）主要用于图像处理，在计算机视觉任务中表现卓越。
            循环神经网络（RNN）和长短期记忆网络（LSTM）适合处理序列数据，如文本和时间序列。
            Transformer架构彻底改变了自然语言处理领域，GPT、BERT等大型语言模型都基于此架构。
            """,
            "metadata": {"category": "技术详解", "keywords": ["深度学习", "CNN", "RNN", "Transformer"]}
        },
        {
            "title": "自然语言处理",
            "content": """
            自然语言处理（NLP）是AI的重要分支，致力于让计算机理解和生成人类语言。
            传统NLP技术包括分词、词性标注、命名实体识别、句法分析等基础任务。
            现代NLP主要基于深度学习，特别是Transformer架构的预训练语言模型。
            主要应用包括机器翻译、文本摘要、情感分析、问答系统、对话系统等。
            """,
            "metadata": {"category": "应用领域", "keywords": ["NLP", "自然语言处理", "机器翻译"]}
        }
    ]


def main():
    """主函数：演示RAG系统功能"""
    print("🚀 高级RAG系统演示")
    print("=" * 50)
    
    # 创建RAG系统
    rag_system = AdvancedRAGSystem(
        chunk_size=200,
        chunk_overlap=30,
        vector_db_type="chroma"
    )
    
    # 加载示例文档
    documents_data = create_sample_knowledge_base()
    documents = rag_system.load_documents(documents_data)
    
    # 构建向量数据库
    rag_system.build_vector_database(documents, persist_path="./rag_chroma_db")
    
    # 测试查询
    test_queries = [
        "什么是深度学习？",
        "CNN在计算机视觉中的应用",
        "Transformer架构的特点",
        "NLP有哪些应用场景？"
    ]
    
    print("\\n🧪 RAG系统功能测试")
    print("-" * 30)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\\n--- 测试 {i} ---")
        print(f"查询: {query}")
        
        # 测试不同检索方法
        for method in ["semantic", "hybrid"]:
            print(f"\\n📍 {method.upper()} 方法:")
            
            result = rag_system.generate_answer(
                query, 
                method=method,
                use_advanced=True,
                use_query_optimization=(method == "hybrid")
            )
            
            print(f"答案: {result['answer'][:200]}...")
            if 'confidence' in result:
                print(f"置信度: {result.get('confidence', 0):.2f}")
            print(f"检索文档数: {result['retrieved_chunks']}")
            print(f"处理时间: {result['processing_time']:.2f}s")
            print(f"参考来源: {', '.join(result['sources'][:3])}")
    
    # 简单的交互式演示
    print("\\n💬 交互式问答 (输入 'quit' 退出)")
    print("-" * 30)
    
    while True:
        try:
            user_query = input("\\n你的问题: ").strip()
            if user_query.lower() == 'quit':
                break
            
            if user_query:
                result = rag_system.generate_answer(
                    user_query, 
                    method="hybrid",
                    use_advanced=False,
                    use_query_optimization=True
                )
                
                print(f"\\n🤖 回答: {result['answer']}")
                print(f"📚 参考: {', '.join(result['sources'][:2])}")
        
        except KeyboardInterrupt:
            break
    
    print("\\n👋 演示结束")


if __name__ == "__main__":
    main()