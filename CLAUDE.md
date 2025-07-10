# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude Code 特殊要求

### 语言要求
- **所有回复必须使用中文**：包括代码注释、解释说明、错误信息等
- **Git 提交信息必须使用中文**：提交标题和描述都使用中文
- **文档和注释使用中文**：所有新创建的文档、代码注释都使用中文

### Git 提交规范
- **提交信息格式要求**：
  ```
  feat: 添加RAG检索增强功能
  
  - 实现向量数据库集成
  - 优化文档分块策略
  - 添加混合搜索支持
  
  🤖 Generated with [Claude Code](https://claude.ai/code)
  
  Co-authored-by: Claude Code <claude-code@anthropic.com>
  ```
- **必须包含 Co-author 信息**：每个提交都要包含 `Co-authored-by: Claude Code <claude-code@anthropic.com>`
- **使用中文提交类型**：
  - `feat`: 新功能
  - `fix`: 修复bug
  - `docs`: 文档更新
  - `style`: 代码格式调整
  - `refactor`: 重构代码
  - `test`: 测试相关
  - `chore`: 构建工具或辅助工具的变动

### 命令执行权限
- **常规 Linux 命令可直接执行**：
  - 文件操作：`ls`, `cd`, `cp`, `mv`, `mkdir`, `touch`, `cat`, `less`, `grep`, `find`
  - 文本处理：`sed`, `awk`, `sort`, `uniq`, `head`, `tail`, `wc`
  - 系统信息：`ps`, `top`, `df`, `du`, `free`, `whoami`, `pwd`
  - 网络工具：`ping`, `curl`, `wget`
  - 开发工具：`git status`, `git log`, `git diff`, `npm list`, `pip list`

- **需要确认的重要命令**：
  - 删除操作：`rm -rf`, `rmdir`
  - 系统级操作：`sudo`, `su`, `chmod 777`, `chown`
  - 网络配置：`iptables`, `netstat`, `ss`
  - 进程管理：`kill`, `killall`, `pkill`
  - 包管理：`apt install`, `yum install`, `npm install -g`
  - 数据库操作：`mysql`, `psql`, `mongo`
  - 服务管理：`systemctl`, `service`

### 个人开发偏好
- **代码风格**：使用4个空格缩进，不使用Tab
- **函数命名**：使用动词开头，如 `获取用户信息()`, `处理文档()`
- **错误处理**：优先使用 try-except，提供中文错误信息
- **日志格式**：使用中文日志信息，便于调试
- **注释语言**：所有代码注释使用中文
- **变量命名**：使用英文，但注释说明使用中文
- **函数设计**：单个函数不超过50行，职责单一
- **导入顺序**：标准库 → 第三方库 → 本地模块，每组之间空一行
- **字符串处理**：优先使用 f-string 格式化，避免使用 % 格式化
- **文件路径**：使用 `pathlib.Path` 而不是 `os.path`
- **配置管理**：使用 `.env` 文件管理环境变量，敏感信息不写入代码
- **依赖管理**：使用 `requirements.txt` 锁定版本，重要依赖添加中文注释说明用途

### 文档和注释偏好
- **函数文档**：所有函数必须有中文docstring，说明参数、返回值、异常
- **类文档**：类的作用、主要方法、使用示例都用中文描述
- **复杂逻辑**：超过5行的复杂逻辑必须添加中文注释解释
- **TODO标记**：使用中文 `# TODO: 待实现功能描述` 格式
- **代码示例**：在文档中提供中文注释的完整代码示例

### 测试和质量保证
- **测试覆盖**：重要函数必须有对应的测试用例
- **测试命名**：测试函数使用中文描述，如 `test_用户登录_成功场景()`
- **断言信息**：断言失败时提供中文错误信息
- **测试数据**：使用中文测试数据，更贴近实际使用场景
- **性能测试**：关键算法需要添加性能测试和基准测试

### 调试和日志偏好
- **调试信息**：使用中文debug信息，便于定位问题
- **日志级别**：开发环境使用DEBUG，生产环境使用INFO
- **异常捕获**：捕获异常时记录中文上下文信息
- **打印调试**：临时调试可以使用print，但正式代码必须使用logging
- **错误追踪**：重要错误必须记录完整的中文错误堆栈

### 安全和性能偏好
- **输入验证**：所有外部输入必须验证，提供中文错误提示
- **密码处理**：使用bcrypt等安全算法，不明文存储
- **API限流**：重要接口添加速率限制
- **缓存策略**：合理使用缓存，避免重复计算
- **资源清理**：及时关闭文件、数据库连接等资源

### 项目结构偏好
- **目录命名**：使用中文拼音或英文，避免中文目录名
- **文件分类**：工具函数放在 `utils/`，配置文件放在 `config/`
- **模块划分**：按功能模块划分，每个模块职责清晰
- **常量定义**：所有魔法数字和字符串定义为有意义的常量
- **环境隔离**：开发、测试、生产环境严格隔离

## Project Overview

This is `ai-guide`, a comprehensive AI technology learning repository focused on modern AI stack including RAG (Retrieval-Augmented Generation), LangChain, LangGraph, Agent workflows, and MCP (Model Context Protocol). The project serves as both a learning resource and practical implementation guide.

## Repository Structure

- `docs/` - Contains detailed learning plans and documentation
  - `人工智能技术栈：10-14综合学习计划.md` - Comprehensive 10-14 day AI technology learning plan covering RAG, LangChain, LangGraph, multi-agent systems, and MCP integration

## Key Technologies Covered

The repository focuses on these core AI technologies:

1. **RAG (Retrieval-Augmented Generation)**
   - Vector databases (Chroma, FAISS)
   - Document processing and chunking
   - Embedding strategies
   - Hybrid search approaches

2. **LangChain Framework**
   - Core components: Chat Models, Prompt Templates, Output Parsers
   - Memory systems: ConversationBufferMemory, ConversationSummaryMemory
   - Document loaders and text splitters
   - Chain composition patterns

3. **LangGraph Workflows**
   - State management with StateGraph
   - Complex workflow orchestration
   - Conditional branching and loops
   - Human-in-the-loop patterns

4. **Multi-Agent Systems**
   - Agent architecture patterns (Supervisor, Network, Hierarchical, Swarm)
   - CrewAI framework implementation
   - Agent coordination and communication
   - Task distribution strategies

5. **MCP (Model Context Protocol)**
   - Protocol implementation for model-context communication
   - Enterprise system integration
   - Resource exposure and tool registration
   - Security and authentication patterns

## Development Environment

The learning plan includes Python environment setup with these key dependencies:
- `langchain`, `langchain-openai`, `langchain-community`
- `langgraph`
- `chromadb`, `faiss-cpu` for vector storage
- `crewai`, `autogen`, `semantic-kernel` for agent frameworks
- `streamlit`, `gradio` for UI development
- `mem0` for memory management

## Learning Progression

The documentation follows a structured 10-14 day learning path:
- Days 1-3: Foundations (AI Agents, LangChain, RAG)
- Days 4-6: Workflows and Multi-Agent systems
- Days 7-9: Advanced techniques and optimization
- Days 10-12: Comprehensive project implementation
- Days 13-14: Advanced exploration and planning

## Architecture Patterns

Key architectural patterns implemented in this guide:
- **RAG Pipeline**: Document ingestion → Embedding → Vector storage → Retrieval → Generation
- **Multi-Agent Coordination**: Supervisor-based task delegation with specialized agents (researcher, writer, analyzer)
- **Workflow State Management**: TypedDict-based state with message history, task tracking, and result aggregation
- **Memory Systems**: Multi-layered memory (short-term session, long-term persistent, semantic knowledge)

## Integration Points

The guide covers enterprise integration through:
- MCP server implementation for standardized model-context communication
- External system connectors (Google Drive, Slack, GitHub)
- Security and authentication layers
- Production deployment considerations

## Performance Optimization

Advanced topics include:
- Vector index optimization (FAISS, ScaNN)
- Model inference acceleration (vLLM, TensorRT)
- Caching strategies
- Monitoring with LangSmith
- Evaluation frameworks (RAGAS)

This repository serves as both an educational resource and practical implementation guide for building production-ready AI applications using the modern AI technology stack.