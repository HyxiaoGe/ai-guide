#!/usr/bin/env python3
"""
智能文档助手 - Web界面
基于Streamlit的用户友好界面
"""

import streamlit as st
import asyncio
from typing import List, Dict, Any
import json
from datetime import datetime
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

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
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'mcp_connected' not in st.session_state:
    st.session_state.mcp_connected = False
if 'collection_stats' not in st.session_state:
    st.session_state.collection_stats = {"total_documents": 0, "total_chunks": 0}

class MCPClient:
    """MCP客户端封装"""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="python",
            args=["mcp_services/rag_service/server.py"],
            env=None
        )
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用MCP工具"""
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # 调用工具
                    result = await session.call_tool(tool_name, arguments)
                    
                    # 解析结果
                    if hasattr(result, 'content') and len(result.content) > 0:
                        content = result.content[0]
                        if hasattr(content, 'text'):
                            return json.loads(content.text)
                    return result
        except Exception as e:
            st.error(f"MCP调用失败: {str(e)}")
            return None

# 创建客户端实例
mcp_client = MCPClient()

def main():
    """主界面"""
    
    # 标题
    st.title("🤖 智能文档助手")
    st.markdown("基于 MCP + RAG 的企业级文档管理和问答系统")
    
    # 侧边栏
    with st.sidebar:
        st.header("📊 系统状态")
        
        # 连接状态
        if st.session_state.mcp_connected:
            st.success("✅ MCP服务已连接")
        else:
            if st.button("🔌 连接MCP服务"):
                with st.spinner("连接中..."):
                    # 测试连接
                    asyncio.run(test_connection())
        
        # 知识库统计
        st.subheader("📈 知识库统计")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("文档数", st.session_state.collection_stats.get("total_documents", 0))
        with col2:
            st.metric("文档块数", st.session_state.collection_stats.get("total_chunks", 0))
        
        if st.button("🔄 刷新统计"):
            asyncio.run(update_stats())
        
        # 功能选择
        st.header("🔧 功能选择")
        mode = st.radio(
            "选择功能",
            ["📝 文档管理", "🔍 智能搜索", "💬 智能问答", "📊 文档分析"]
        )
    
    # 主界面内容
    if mode == "📝 文档管理":
        document_management()
    elif mode == "🔍 智能搜索":
        intelligent_search()
    elif mode == "💬 智能问答":
        intelligent_qa()
    elif mode == "📊 文档分析":
        document_analysis()

def document_management():
    """文档管理界面"""
    st.header("📝 文档管理")
    
    tab1, tab2, tab3 = st.tabs(["添加文档", "批量导入", "文档列表"])
    
    with tab1:
        st.subheader("添加单个文档")
        
        # 文档内容输入
        doc_content = st.text_area(
            "文档内容",
            height=200,
            placeholder="请输入文档内容..."
        )
        
        # 元数据输入
        col1, col2 = st.columns(2)
        with col1:
            doc_title = st.text_input("标题")
            doc_author = st.text_input("作者")
        with col2:
            doc_source = st.text_input("来源")
            doc_category = st.text_input("分类")
        
        doc_tags = st.text_input("标签（用逗号分隔）")
        
        if st.button("📤 添加文档", type="primary"):
            if doc_content:
                with st.spinner("添加中..."):
                    metadata = {
                        "title": doc_title,
                        "author": doc_author,
                        "source": doc_source,
                        "category": doc_category,
                        "tags": [tag.strip() for tag in doc_tags.split(",") if tag.strip()]
                    }
                    result = asyncio.run(add_document(doc_content, metadata))
                    if result and result.get("success"):
                        st.success(f"✅ 文档添加成功！文档ID: {result.get('document_id')}")
                        st.session_state.documents.append({
                            "id": result.get("document_id"),
                            "title": doc_title or "未命名文档",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    else:
                        st.error("❌ 文档添加失败")
            else:
                st.warning("请输入文档内容")
    
    with tab2:
        st.subheader("批量导入文档")
        
        # 文件上传
        uploaded_files = st.file_uploader(
            "选择文件",
            type=["txt", "md", "json"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.info(f"已选择 {len(uploaded_files)} 个文件")
            
            if st.button("📤 批量导入", type="primary"):
                with st.spinner("导入中..."):
                    documents = []
                    for file in uploaded_files:
                        content = file.read().decode("utf-8")
                        documents.append({
                            "content": content,
                            "metadata": {
                                "title": file.name,
                                "source": "file_upload",
                                "upload_time": datetime.now().isoformat()
                            }
                        })
                    
                    result = asyncio.run(batch_add_documents(documents))
                    if result and result.get("success"):
                        st.success(f"✅ 成功导入 {result.get('added_count')} 个文档")
                        asyncio.run(update_stats())
                    else:
                        st.error("❌ 批量导入失败")
    
    with tab3:
        st.subheader("文档列表")
        
        if st.session_state.documents:
            for doc in st.session_state.documents:
                with st.expander(f"📄 {doc['title']} - {doc['timestamp']}"):
                    st.write(f"文档ID: {doc['id']}")
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if st.button("🗑️ 删除", key=f"del_{doc['id']}"):
                            st.warning("删除功能待实现")
        else:
            st.info("暂无文档")

def intelligent_search():
    """智能搜索界面"""
    st.header("🔍 智能搜索")
    
    # 搜索类型选择
    search_type = st.radio(
        "搜索类型",
        ["语义搜索", "关键词搜索"],
        horizontal=True
    )
    
    # 搜索输入
    query = st.text_input(
        "搜索内容",
        placeholder="输入搜索关键词或问题..."
    )
    
    # 高级选项
    with st.expander("⚙️ 高级选项"):
        top_k = st.slider("返回结果数量", 1, 10, 5)
        score_threshold = st.slider("相关度阈值", 0.0, 1.0, 0.5)
    
    if st.button("🔍 搜索", type="primary"):
        if query:
            with st.spinner("搜索中..."):
                if search_type == "语义搜索":
                    results = asyncio.run(semantic_search(query, top_k))
                else:
                    results = asyncio.run(search_documents(query, top_k))
                
                if results and results.get("results"):
                    st.success(f"找到 {len(results['results'])} 个相关文档")
                    
                    for i, result in enumerate(results["results"]):
                        with st.container():
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"**{i+1}. {result.get('metadata', {}).get('title', '未命名文档')}**")
                                st.write(result.get("content", "")[:300] + "...")
                            with col2:
                                st.metric("相关度", f"{result.get('score', 0):.2f}")
                            st.divider()
                else:
                    st.info("未找到相关文档")
        else:
            st.warning("请输入搜索内容")

def intelligent_qa():
    """智能问答界面"""
    st.header("💬 智能问答")
    
    # 对话历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 用户输入
    if prompt := st.chat_input("请输入您的问题..."):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # 获取AI回答
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                if len(st.session_state.messages) > 1:
                    # 多轮对话
                    response = asyncio.run(multi_turn_chat(
                        prompt,
                        [{"role": m["role"], "content": m["content"]} 
                         for m in st.session_state.messages[:-1]]
                    ))
                else:
                    # 单轮问答
                    response = asyncio.run(answer_question(prompt))
                
                if response and response.get("success"):
                    answer = response.get("answer", "抱歉，我无法回答这个问题。")
                    st.write(answer)
                    
                    # 显示参考文档
                    if response.get("sources"):
                        with st.expander("📚 参考文档"):
                            for source in response["sources"]:
                                st.write(f"- {source}")
                    
                    # 添加AI消息
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("获取回答失败")
    
    # 清除对话按钮
    if st.button("🗑️ 清除对话"):
        st.session_state.messages = []
        st.rerun()

def document_analysis():
    """文档分析界面"""
    st.header("📊 文档分析")
    
    # 文档摘要
    st.subheader("📝 文档摘要生成")
    
    doc_ids = st.text_input(
        "文档ID列表",
        placeholder="输入文档ID，用逗号分隔"
    )
    
    summary_type = st.selectbox(
        "摘要类型",
        ["简短摘要", "详细摘要", "要点提取"]
    )
    
    if st.button("生成摘要", type="primary"):
        if doc_ids:
            with st.spinner("生成中..."):
                doc_id_list = [id.strip() for id in doc_ids.split(",")]
                result = asyncio.run(summarize_documents(doc_id_list, summary_type))
                
                if result and result.get("success"):
                    st.success("✅ 摘要生成成功")
                    st.write(result.get("summary", ""))
                else:
                    st.error("❌ 摘要生成失败")
        else:
            st.warning("请输入文档ID")
    
    # 知识库分析
    st.subheader("📈 知识库分析")
    
    if st.button("🔍 分析知识库"):
        with st.spinner("分析中..."):
            stats = asyncio.run(get_collection_stats())
            
            if stats:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("总文档数", stats.get("total_documents", 0))
                    st.metric("总文档块数", stats.get("total_chunks", 0))
                with col2:
                    st.metric("平均块大小", f"{stats.get('avg_chunk_size', 0):.0f} 字符")
                    st.metric("向量维度", stats.get("embedding_dimension", 0))
                with col3:
                    st.metric("集合名称", stats.get("collection_name", "N/A"))
                    st.metric("持久化目录", stats.get("persist_directory", "N/A"))

# 异步函数封装
async def test_connection():
    """测试MCP连接"""
    try:
        result = await mcp_client.call_tool("get_collection_stats", {})
        if result:
            st.session_state.mcp_connected = True
            await update_stats()
    except Exception as e:
        st.error(f"连接失败: {str(e)}")

async def update_stats():
    """更新统计信息"""
    try:
        result = await mcp_client.call_tool("get_collection_stats", {})
        if result:
            st.session_state.collection_stats = result
    except:
        pass

async def add_document(content: str, metadata: Dict[str, Any]):
    """添加文档"""
    return await mcp_client.call_tool("add_document", {
        "content": content,
        "metadata": metadata
    })

async def batch_add_documents(documents: List[Dict[str, Any]]):
    """批量添加文档"""
    return await mcp_client.call_tool("batch_add_documents", {
        "documents": documents
    })

async def search_documents(query: str, top_k: int = 5):
    """搜索文档"""
    return await mcp_client.call_tool("search_documents", {
        "query": query,
        "top_k": top_k
    })

async def semantic_search(query: str, top_k: int = 5):
    """语义搜索"""
    return await mcp_client.call_tool("semantic_search", {
        "query": query,
        "top_k": top_k
    })

async def answer_question(question: str):
    """回答问题"""
    return await mcp_client.call_tool("answer_question", {
        "question": question
    })

async def multi_turn_chat(message: str, history: List[Dict[str, str]]):
    """多轮对话"""
    return await mcp_client.call_tool("multi_turn_chat", {
        "message": message,
        "history": history
    })

async def summarize_documents(document_ids: List[str], summary_type: str):
    """生成文档摘要"""
    return await mcp_client.call_tool("summarize_documents", {
        "document_ids": document_ids,
        "max_length": 500 if summary_type == "简短摘要" else 1000
    })

async def get_collection_stats():
    """获取知识库统计"""
    return await mcp_client.call_tool("get_collection_stats", {})

if __name__ == "__main__":
    main()