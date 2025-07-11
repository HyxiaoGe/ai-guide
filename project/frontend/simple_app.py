#!/usr/bin/env python3
"""
智能文档助手 - 简化Web界面
直接使用RAG功能，不通过MCP
"""

import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

# 直接导入RAG功能
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

# 导入必要的库
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import chromadb

# 页面配置
st.set_page_config(
    page_title="智能文档助手",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'llm' not in st.session_state:
    st.session_state.llm = None

class SimpleRAGSystem:
    """简化的RAG系统"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        
        # 初始化向量数据库
        persist_directory = "./data/vector_db"
        os.makedirs(persist_directory, exist_ok=True)
        
        self.vectorstore = Chroma(
            collection_name="documents",
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )
    
    def add_document(self, content: str, metadata: dict = None):
        """添加文档"""
        try:
            # 分块
            chunks = self.text_splitter.split_text(content)
            
            # 创建文档对象
            documents = []
            for i, chunk in enumerate(chunks):
                doc_metadata = metadata.copy() if metadata else {}
                doc_metadata["chunk_index"] = i
                doc_metadata["total_chunks"] = len(chunks)
                doc_metadata["created_at"] = datetime.now().isoformat()
                
                documents.append(Document(
                    page_content=chunk,
                    metadata=doc_metadata
                ))
            
            # 添加到向量数据库
            ids = self.vectorstore.add_documents(documents)
            
            return {
                "success": True,
                "document_id": metadata.get("title", "untitled"),
                "chunks_added": len(ids)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_documents(self, query: str, top_k: int = 5):
        """搜索文档"""
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=top_k)
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": 1 - score  # 转换为相似度
                })
            
            return {"success": True, "results": formatted_results}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def answer_question(self, question: str, use_context: bool = True):
        """回答问题"""
        try:
            if use_context:
                # 搜索相关文档
                search_results = self.search_documents(question, top_k=3)
                
                if search_results.get("success") and search_results.get("results"):
                    # 构建上下文
                    context = "\n\n".join([
                        f"文档{i+1}: {result['content']}"
                        for i, result in enumerate(search_results["results"])
                    ])
                    
                    # 构建提示词
                    prompt = f"""基于以下文档内容回答问题。如果文档中没有相关信息，请明确说明。

相关文档：
{context}

问题：{question}

请提供准确、相关的回答："""
                else:
                    prompt = f"请回答以下问题：{question}"
            else:
                prompt = question
            
            # 获取回答
            response = self.llm.invoke(prompt)
            
            return {
                "success": True,
                "answer": response.content,
                "sources": [r["metadata"].get("title", "未命名") 
                          for r in search_results.get("results", [])] if use_context else []
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_stats(self):
        """获取统计信息"""
        try:
            # 获取集合信息
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                "total_chunks": count,
                "collection_name": "documents",
                "embedding_model": "text-embedding-3-small"
            }
        except:
            return {
                "total_chunks": 0,
                "collection_name": "documents",
                "embedding_model": "text-embedding-3-small"
            }

# 创建RAG系统实例
@st.cache_resource
def get_rag_system():
    return SimpleRAGSystem()

def main():
    """主界面"""
    
    # 获取RAG系统
    rag = get_rag_system()
    
    # 标题
    st.title("🤖 智能文档助手")
    st.markdown("基于 RAG 的文档管理和问答系统")
    
    # 侧边栏
    with st.sidebar:
        st.header("📊 系统状态")
        
        # 知识库统计
        stats = rag.get_stats()
        st.metric("文档块数", stats.get("total_chunks", 0))
        st.metric("嵌入模型", stats.get("embedding_model", "N/A"))
        
        if st.button("🔄 刷新统计"):
            st.rerun()
        
        # 功能选择
        st.header("🔧 功能选择")
        mode = st.radio(
            "选择功能",
            ["📝 文档管理", "🔍 文档搜索", "💬 智能问答"]
        )
    
    # 主界面内容
    if mode == "📝 文档管理":
        document_management(rag)
    elif mode == "🔍 文档搜索":
        document_search(rag)
    elif mode == "💬 智能问答":
        intelligent_qa(rag)

def document_management(rag):
    """文档管理界面"""
    st.header("📝 文档管理")
    
    # 文档内容输入
    doc_content = st.text_area(
        "文档内容",
        height=200,
        placeholder="请输入文档内容..."
    )
    
    # 元数据输入
    col1, col2 = st.columns(2)
    with col1:
        doc_title = st.text_input("标题", value="")
        doc_author = st.text_input("作者", value="")
    with col2:
        doc_source = st.text_input("来源", value="")
        doc_category = st.text_input("分类", value="")
    
    doc_tags = st.text_input("标签（用逗号分隔）", value="")
    
    if st.button("📤 添加文档", type="primary"):
        if doc_content:
            with st.spinner("添加中..."):
                metadata = {
                    "title": doc_title or "未命名文档",
                    "author": doc_author,
                    "source": doc_source,
                    "category": doc_category,
                    "tags": [tag.strip() for tag in doc_tags.split(",") if tag.strip()]
                }
                
                result = rag.add_document(doc_content, metadata)
                
                if result.get("success"):
                    st.success(f"✅ 文档添加成功！添加了 {result.get('chunks_added')} 个文档块")
                else:
                    st.error(f"❌ 文档添加失败: {result.get('error')}")
        else:
            st.warning("请输入文档内容")
    
    # 示例文档
    with st.expander("📚 添加示例文档"):
        if st.button("添加AI技术介绍"):
            sample_content = """人工智能（AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。

AI的主要技术包括：
1. 机器学习：让计算机从数据中学习模式
2. 深度学习：使用神经网络处理复杂数据
3. 自然语言处理：理解和生成人类语言
4. 计算机视觉：识别和理解图像内容

AI的应用领域非常广泛，包括自动驾驶、医疗诊断、金融分析、智能客服等。"""
            
            result = rag.add_document(sample_content, {
                "title": "AI技术介绍",
                "author": "示例系统",
                "category": "技术文档"
            })
            
            if result.get("success"):
                st.success("✅ 示例文档添加成功！")
                st.rerun()

def document_search(rag):
    """文档搜索界面"""
    st.header("🔍 文档搜索")
    
    # 搜索输入
    query = st.text_input(
        "搜索内容",
        placeholder="输入搜索关键词或问题..."
    )
    
    # 搜索选项
    col1, col2 = st.columns([3, 1])
    with col2:
        top_k = st.number_input("返回结果数", min_value=1, max_value=10, value=5)
    
    if st.button("🔍 搜索", type="primary"):
        if query:
            with st.spinner("搜索中..."):
                results = rag.search_documents(query, top_k)
                
                if results.get("success") and results.get("results"):
                    st.success(f"找到 {len(results['results'])} 个相关文档块")
                    
                    for i, result in enumerate(results["results"]):
                        with st.container():
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                title = result.get("metadata", {}).get("title", "未命名文档")
                                st.markdown(f"**{i+1}. {title}**")
                                st.write(result.get("content", ""))
                                
                                # 显示元数据
                                metadata = result.get("metadata", {})
                                if metadata.get("author"):
                                    st.caption(f"作者: {metadata['author']}")
                                if metadata.get("category"):
                                    st.caption(f"分类: {metadata['category']}")
                            
                            with col2:
                                st.metric("相关度", f"{result.get('score', 0):.2%}")
                            
                            st.divider()
                else:
                    st.info("未找到相关文档")
        else:
            st.warning("请输入搜索内容")

def intelligent_qa(rag):
    """智能问答界面"""
    st.header("💬 智能问答")
    
    # 对话历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant" and message.get("sources"):
                with st.expander("📚 参考来源"):
                    for source in message["sources"]:
                        st.write(f"- {source}")
    
    # 用户输入
    if prompt := st.chat_input("请输入您的问题..."):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # 获取AI回答
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                # 检查是否使用知识库
                use_context = st.sidebar.checkbox("使用知识库", value=True)
                
                result = rag.answer_question(prompt, use_context=use_context)
                
                if result.get("success"):
                    answer = result.get("answer", "抱歉，我无法回答这个问题。")
                    st.write(answer)
                    
                    # 添加AI消息
                    message_data = {"role": "assistant", "content": answer}
                    if result.get("sources"):
                        message_data["sources"] = result["sources"]
                        with st.expander("📚 参考来源"):
                            for source in result["sources"]:
                                st.write(f"- {source}")
                    
                    st.session_state.messages.append(message_data)
                else:
                    st.error(f"获取回答失败: {result.get('error')}")
    
    # 清除对话按钮
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("🗑️ 清除对话"):
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ 请先配置 OPENAI_API_KEY 环境变量")
        st.info("编辑 .env 文件并设置: OPENAI_API_KEY=your-api-key")
        st.stop()
    
    main()