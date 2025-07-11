#!/bin/bash
# 启动Web界面

echo "🚀 启动智能文档助手Web界面..."

# 激活虚拟环境
source venv/bin/activate

# 检查环境变量
if ! grep -q "sk-" .env 2>/dev/null; then
    echo "⚠️  请先在 .env 文件中配置 OPENAI_API_KEY"
    echo "编辑命令: nano .env"
    exit 1
fi

# 检查MCP服务是否运行
echo "🔍 检查MCP服务状态..."
if ! ps aux | grep -v grep | grep -q "mcp_services/rag_service/server.py"; then
    echo "⚠️  MCP服务未运行，请先在另一个终端运行: ./start.sh"
    echo "💡 提示: 需要同时运行MCP服务和Web界面"
    read -p "是否在后台启动MCP服务？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 在后台启动MCP服务..."
        nohup python mcp_services/rag_service/server.py > logs/mcp_server.log 2>&1 &
        echo "✅ MCP服务已在后台启动 (PID: $!)"
        sleep 3
    else
        exit 1
    fi
fi

# 启动Streamlit
echo "🌐 启动Web界面..."
echo "🔗 访问地址: http://localhost:8501"
echo "🔧 使用 Ctrl+C 停止服务"

# 加载环境变量并启动
export $(cat .env | grep -v '^#' | xargs)
streamlit run frontend/app.py \
    --server.port 8501 \
    --server.address localhost \
    --server.headless true \
    --browser.gatherUsageStats false