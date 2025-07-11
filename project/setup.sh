#!/bin/bash
# 智能文档助手系统 - 环境设置脚本

echo "🚀 开始设置智能文档助手系统..."

# 检查系统依赖
echo "🔍 检查系统依赖..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先运行: sudo apt install python3"
    exit 1
fi

if ! python3 -m venv --help &> /dev/null; then
    echo "❌ python3-venv 未安装，请先运行: sudo apt install python3-venv"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安装，请先运行: sudo apt install python3-pip"  
    exit 1
fi

echo "✅ 系统依赖检查通过"

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
mkdir -p logs

# 清理可能存在的虚拟环境
if [ -d "venv" ]; then
    echo "🧹 清理旧的虚拟环境..."
    rm -rf venv
fi

# 创建Python虚拟环境
echo "🐍 创建Python虚拟环境..."
python3 -m venv venv

if [ ! -f "venv/bin/activate" ]; then
    echo "❌ 虚拟环境创建失败"
    exit 1
fi

# 激活虚拟环境
echo "⚡ 激活虚拟环境..."
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

# 创建启动脚本
echo "🚀 创建启动脚本..."
cat > start.sh << 'EOF'
#!/bin/bash
# 启动智能文档助手系统

echo "🚀 启动智能文档助手系统..."

# 激活虚拟环境
source venv/bin/activate

# 检查环境变量
if ! grep -q "sk-" .env 2>/dev/null; then
    echo "⚠️  请先在 .env 文件中配置 OPENAI_API_KEY"
    echo "编辑命令: nano .env"
    exit 1
fi

# 启动数据库（如果Docker可用）
if command -v docker-compose &> /dev/null; then
    echo "🐳 启动数据库服务..."
    docker-compose up -d postgres redis
    sleep 5
else
    echo "⚠️  Docker Compose 未安装，将使用内存数据库"
fi

# 启动RAG服务
echo "📚 启动RAG MCP服务..."
python mcp_services/rag_service/server.py
EOF

chmod +x start.sh

# 创建测试脚本
echo "🧪 创建测试脚本..."
cat > test.py << 'EOF'
#!/usr/bin/env python3
"""系统测试脚本"""

import sys
import os

def test_imports():
    """测试关键包导入"""
    print("🧪 测试包导入...")
    
    packages = [
        ("mcp", "MCP"),
        ("langchain", "LangChain"), 
        ("chromadb", "ChromaDB"),
        ("openai", "OpenAI"),
        ("fastapi", "FastAPI"),
        ("streamlit", "Streamlit"),
    ]
    
    success = 0
    for package, name in packages:
        try:
            __import__(package)
            print(f"✅ {name}")
            success += 1
        except ImportError as e:
            print(f"❌ {name}: {e}")
    
    return success == len(packages)

def main():
    print("🔬 智能文档助手系统 - 环境测试")
    print("=" * 50)
    
    if test_imports():
        print("\n🎉 所有依赖包导入成功！")
        print("\n💡 下一步:")
        print("  1. 配置 .env 文件中的 API 密钥")
        print("  2. 运行: ./start.sh")
        return 0
    else:
        print("\n❌ 依赖包测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x test.py

# 复制环境配置文件
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ 环境配置文件已创建，请编辑 .env 文件添加你的API密钥"
else
    echo "✅ .env 文件已存在"
fi

echo ""
echo "✅ 环境设置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 配置API密钥: nano .env"
echo "2. 测试环境: python test.py"
echo "3. 启动系统: ./start.sh"