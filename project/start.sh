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

# 检查现有数据库连接
echo "🗄️  检查PostgreSQL连接..."
if docker exec fusion_postgres psql -U fusion -d docassistant -c "SELECT 1;" &> /dev/null; then
    echo "✅ PostgreSQL连接正常 (使用现有fusion_postgres容器)"
else
    echo "❌ PostgreSQL连接失败，请检查fusion_postgres容器"
    exit 1
fi

# 启动Redis（如果需要）
if command -v docker-compose &> /dev/null; then
    echo "🐳 启动Redis服务..."
    docker-compose up -d redis
    sleep 3
else
    echo "⚠️  Docker Compose 未安装，将使用内存缓存"
fi

# 启动RAG服务
echo "📚 启动RAG MCP服务..."
echo "🔧 使用 Ctrl+C 停止服务"
echo "💡 提示: 这是一个MCP服务器，需要MCP客户端连接"
python mcp_services/rag_service/server.py