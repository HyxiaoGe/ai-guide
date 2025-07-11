#!/bin/bash
# 运行简化版Web界面

echo "🚀 启动智能文档助手Web界面（简化版）..."

# 激活虚拟环境
source venv/bin/activate

# 检查环境变量
if ! grep -q "sk-" .env 2>/dev/null; then
    echo "⚠️  请先在 .env 文件中配置 OPENAI_API_KEY"
    echo "编辑命令: nano .env"
    exit 1
fi

# 加载环境变量
export $(cat .env | grep -v '^#' | xargs)

# 启动Streamlit
echo "🌐 启动Web界面..."
echo "🔗 访问地址: http://localhost:8501"
echo "🔧 使用 Ctrl+C 停止服务"
echo ""
echo "💡 这是简化版界面，直接使用RAG功能，无需MCP服务"

streamlit run frontend/simple_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false