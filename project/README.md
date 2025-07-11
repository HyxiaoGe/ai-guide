# 智能文档助手 - MCP RAG 系统

基于 MCP (Model Context Protocol) 协议的智能文档检索和问答系统，集成了 RAG、LangChain、ChromaDB 等现代 AI 技术栈。

## 🎯 项目概述

这是一个企业级的智能文档管理和问答系统，使用 MCP 协议实现标准化的 AI 工具调用，为文档检索和智能问答提供统一的接口。

## 🔧 技术栈

- **AI 框架**: LangChain, OpenAI GPT
- **向量数据库**: ChromaDB
- **关系数据库**: PostgreSQL
- **协议**: MCP (Model Context Protocol)
- **后端**: Python, FastAPI
- **部署**: Docker

## ✨ 功能特性

### 📚 当前功能

- **文档管理**: 添加、批量导入、元数据管理
- **智能检索**: 语义搜索、关键词搜索、混合搜索
- **问答系统**: 基于上下文的问答、多轮对话、文档摘要
- **MCP 服务**: 9个核心工具、实时连接监控

### 🔧 核心工具

1. `add_document` - 添加文档到知识库
2. `batch_add_documents` - 批量添加多个文档
3. `search_documents` - 在知识库中搜索相关文档
4. `semantic_search` - 高级语义搜索
5. `answer_question` - 基于知识库回答问题
6. `multi_turn_chat` - 多轮对话问答
7. `summarize_documents` - 生成文档摘要
8. `get_collection_stats` - 获取知识库统计信息
9. `clear_collection` - 清空知识库

## 🚀 快速开始

### 📋 环境要求

- Python 3.10+
- PostgreSQL (可使用现有容器)
- OpenAI API Key

### 🔧 安装步骤

1. **环境设置**
   ```bash
   cd project
   ./setup.sh
   ```

2. **配置 API 密钥**
   ```bash
   nano .env  # 设置 OPENAI_API_KEY
   ```

3. **启动Web界面**
   ```bash
   ./run_web.sh
   ```

4. **或启动MCP服务**
   ```bash
   ./start.sh
   ```

5. **测试环境**
   ```bash
   python test.py
   ```

## 📊 项目结构

```
project/
├── mcp_services/           # MCP服务
│   └── rag_service/        # RAG问答服务
│       └── server.py       # 核心服务器
├── frontend/               # Web前端
│   ├── app.py             # 完整版Web界面 (需要MCP)
│   └── simple_app.py      # 简化版Web界面 (直接RAG)
├── data/                   # 数据存储
│   ├── vector_db/          # 向量数据库
│   ├── uploads/            # 文件上传
│   └── cache/              # 缓存
├── logs/                   # 日志文件
├── .env                    # 环境变量配置
├── docker-compose.yml      # Docker配置
├── requirements.txt        # Python依赖
├── setup.sh               # 环境设置脚本
├── start.sh               # 启动MCP服务
├── run_web.sh             # 启动Web界面 (推荐)
├── start_web.sh           # 启动完整Web界面
└── test.py                # 环境测试脚本
```

## 🏗️ 架构设计

### 数据流

```
MCP客户端 ←→ MCP服务器 ←→ RAG引擎 ←→ 数据库
                                   ├── ChromaDB (向量)
                                   └── PostgreSQL (关系)
```

### 核心组件

- **MCP 协议层**: 标准化的 AI 工具调用接口
- **RAG 引擎**: 检索增强生成系统
- **向量存储**: ChromaDB 本地向量数据库
- **关系数据库**: PostgreSQL 存储结构化数据
- **AI 模型**: OpenAI GPT 进行文本生成和理解

## 🛠️ 使用方式

### 🌐 Web界面 (推荐)

最简单的使用方式，提供用户友好的图形界面：

```bash
./run_web.sh
```

访问 http://localhost:8501 打开Web界面

**功能包括：**
- 📝 文档管理：添加、搜索文档
- 🔍 智能搜索：语义搜索和关键词搜索  
- 💬 智能问答：基于知识库的对话
- 📊 统计信息：实时查看知识库状态

### 🔧 MCP服务

底层MCP协议接口，适合开发集成：

```bash
./start.sh
```

### 客户端连接示例

```python
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# 连接到MCP服务器
server_params = StdioServerParameters(
    command="python",
    args=["mcp_services/rag_service/server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        print(f"可用工具: {len(tools.tools)}")
```

## 📈 监控和日志

系统提供实时的连接监控和操作日志：

- 🔌 客户端连接/断开状态
- 📋 工具调用记录
- 📁 资源访问日志
- ⚠️ 错误和异常追踪

## 🔮 未来规划

- 📁 文件服务 (支持多格式文档)
- 🌐 API 网关 (统一 REST 接口)
- 🖥️ Web 前端 (用户界面)
- 🐳 容器化部署

## 📝 开发说明

### 添加新工具

1. 在 `server.py` 中添加工具定义
2. 实现工具的业务逻辑
3. 添加相应的错误处理和日志

### 配置说明

- `.env`: 环境变量 (API密钥、数据库连接)
- `docker-compose.yml`: 容器配置
- `requirements.txt`: Python 依赖

## 📄 许可证

MIT License