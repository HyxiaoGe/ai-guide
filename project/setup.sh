#!/bin/bash
# 智能文档助手系统 - 环境设置脚本

echo "🚀 开始设置智能文档助手系统..."

# 创建项目目录结构
echo "📁 创建项目目录结构..."
mkdir -p mcp_services/{rag_service,file_service,tools_service}
mkdir -p api_gateway/{routes,middleware}
mkdir -p workflows
mkdir -p agents
mkdir -p frontend
mkdir -p docker
mkdir -p tests
mkdir -p data/{uploads,vector_db,cache}

# 创建Python虚拟环境
echo "🐍 创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装基础依赖
echo "📦 安装依赖包..."
pip install --upgrade pip
pip install fastapi uvicorn[standard]
pip install mcp langchain langchain-openai chromadb
pip install langgraph crewai streamlit
pip install python-multipart aiofiles
pip install redis asyncpg psycopg2-binary
pip install prometheus-client python-json-logger

# 创建环境变量文件
echo "🔧 创建环境配置文件..."
cat > .env.example << EOF
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/docassistant
REDIS_URL=redis://localhost:6379/0

# MCP服务配置
MCP_RAG_PORT=8001
MCP_FILE_PORT=8002
MCP_TOOLS_PORT=8003

# API网关配置
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secret-key-here

# 向量数据库配置
CHROMA_PERSIST_DIR=./data/vector_db
CHROMA_COLLECTION_NAME=documents

# 文件存储配置
UPLOAD_DIR=./data/uploads
MAX_FILE_SIZE=10485760  # 10MB

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

# 创建Docker Compose配置
echo "🐳 创建Docker配置..."
cat > docker-compose.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: docuser
      POSTGRES_PASSWORD: docpass
      POSTGRES_DB: docassistant
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U docuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  rag-mcp:
    build:
      context: .
      dockerfile: docker/Dockerfile.mcp
    environment:
      - SERVICE_TYPE=rag
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
    volumes:
      - ./mcp_services/rag_service:/app
      - ./data/vector_db:/data/vector_db
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy

  file-mcp:
    build:
      context: .
      dockerfile: docker/Dockerfile.mcp
    environment:
      - SERVICE_TYPE=file
    volumes:
      - ./mcp_services/file_service:/app
      - ./data/uploads:/data/uploads
    ports:
      - "8002:8002"

  api-gateway:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    environment:
      - DATABASE_URL=postgresql://docuser:docpass@postgres:5432/docassistant
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
    volumes:
      - ./api_gateway:/app
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - rag-mcp
      - file-mcp

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    environment:
      - API_URL=http://api-gateway:8000
    volumes:
      - ./frontend:/app
    ports:
      - "8501:8501"
    depends_on:
      - api-gateway

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: docassistant_network
EOF

# 创建项目requirements.txt
echo "📝 创建requirements.txt..."
cat > requirements.txt << EOF
# 核心框架
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
aiofiles>=23.2.1

# MCP和AI框架
mcp>=1.0.0
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.10
langgraph>=0.2.0
crewai>=0.141.0

# 数据库
asyncpg>=0.29.0
psycopg2-binary>=2.9.9
redis>=5.0.0
chromadb>=0.4.22

# 前端
streamlit>=1.29.0
plotly>=5.18.0

# 工具和实用程序
python-dotenv>=1.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# 监控和日志
prometheus-client>=0.19.0
python-json-logger>=2.0.0

# 开发工具
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.12.0
isort>=5.13.0
EOF

echo "✅ 环境设置完成！"
echo ""
echo "下一步："
echo "1. 复制 .env.example 到 .env 并填写配置"
echo "2. 启动数据库服务: docker-compose up -d postgres redis"
echo "3. 运行 'source venv/bin/activate' 激活虚拟环境"
echo "4. 开始实现第一个MCP服务"