# 智能文档助手系统 - 综合实战项目

## 项目目标

构建一个企业级的智能文档助手系统，整合AI Guide课程中学到的所有技术：
- **MCP协议**：标准化的服务接口
- **RAG技术**：智能文档检索和问答
- **LangGraph**：复杂工作流编排
- **Multi-Agent**：多智能体协作
- **LangChain**：基础框架支持

## 系统架构

```
┌────────────────────────────────────────────────────────────────┐
│                        前端应用层                                │
│                  (Streamlit / Gradio)                           │
├────────────────────────────────────────────────────────────────┤
│                      API Gateway                                │
│                  (FastAPI + Auth)                              │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│ MCP Services │  Workflow    │ Agent System │   Storage       │
├──────────────┼──────────────┼──────────────┼─────────────────┤
│ RAG MCP      │ LangGraph    │ CrewAI       │ PostgreSQL      │
│ File MCP     │ Orchestrator │ Agents       │ Redis           │
│ Tools MCP    │ State Mgmt   │ Coordinator  │ Vector DB       │
└──────────────┴──────────────┴──────────────┴─────────────────┘
```

## 核心功能

1. **智能文档管理**
   - 上传和解析多种格式文档（PDF、Word、Markdown）
   - 自动提取和索引文档内容
   - 智能分类和标签管理

2. **高级检索问答**
   - 基于RAG的精准检索
   - 多轮对话理解
   - 引用来源追踪

3. **自动化工作流**
   - 文档摘要生成
   - 报告自动撰写
   - 知识图谱构建

4. **多Agent协作**
   - 研究Agent：深度分析文档
   - 写作Agent：生成高质量内容
   - 审核Agent：质量把关

## 技术栈

- **后端框架**: FastAPI + Uvicorn
- **MCP实现**: Python MCP SDK
- **向量数据库**: ChromaDB / Weaviate
- **LLM**: OpenAI GPT-4 / Claude
- **工作流**: LangGraph
- **Agent框架**: CrewAI
- **前端**: Streamlit / Gradio
- **部署**: Docker + Docker Compose
- **监控**: Prometheus + Grafana

## 项目结构

```
project/
├── mcp_services/          # MCP服务
│   ├── rag_service/      # RAG服务
│   ├── file_service/     # 文件管理服务
│   └── tools_service/    # 工具服务
├── api_gateway/          # API网关
│   ├── main.py
│   ├── auth.py
│   └── routes/
├── workflows/            # LangGraph工作流
│   ├── document_flow.py
│   └── research_flow.py
├── agents/              # Multi-Agent系统
│   ├── research_crew.py
│   └── writing_crew.py
├── frontend/            # 前端应用
│   └── streamlit_app.py
├── docker/              # Docker配置
│   ├── Dockerfile
│   └── docker-compose.yml
└── tests/               # 测试套件
```

## 实施步骤

### 第一阶段：基础设施（Day 1-2）
1. 搭建项目结构
2. 配置Docker环境
3. 实现基础MCP服务
4. 设置数据库连接

### 第二阶段：核心服务（Day 3-4）
1. 实现RAG MCP服务
2. 构建文件管理系统
3. 创建工具服务
4. 集成向量数据库

### 第三阶段：工作流程（Day 5-6）
1. 设计LangGraph工作流
2. 实现文档处理流程
3. 构建查询响应系统
4. 添加状态管理

### 第四阶段：智能Agent（Day 7-8）
1. 创建专业Agent团队
2. 实现Agent协作机制
3. 集成到工作流中
4. 优化协作效率

### 第五阶段：系统集成（Day 9-10）
1. 构建API网关
2. 实现认证授权
3. 创建前端界面
4. 系统集成测试

### 第六阶段：优化部署（Day 11-12）
1. 性能优化
2. 添加监控告警
3. 容器化部署
4. 编写文档

## 快速开始

```bash
# 1. 克隆项目
cd ~/ai-guide/project

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 添加你的API密钥

# 4. 启动MCP服务
python mcp_services/start_all.py

# 5. 启动API网关
uvicorn api_gateway.main:app --reload

# 6. 启动前端
streamlit run frontend/streamlit_app.py
```

## 部署指南

### 本地开发
```bash
# 使用Docker Compose
docker-compose up -d
```

### 生产部署
```bash
# 构建镜像
docker build -t doc-assistant .

# 使用Kubernetes
kubectl apply -f k8s/
```

## 项目亮点

1. **技术整合**：将课程所有技术有机结合
2. **生产就绪**：考虑了实际部署需求
3. **可扩展性**：模块化设计，易于扩展
4. **最佳实践**：遵循企业级开发标准

## 下一步计划

- [ ] 添加更多文档格式支持
- [ ] 实现多语言处理
- [ ] 集成更多LLM模型
- [ ] 优化检索算法
- [ ] 添加知识图谱功能

## 许可证

MIT License