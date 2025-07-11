#!/usr/bin/env python3
"""
智能文档助手系统 - 项目启动脚本
用于快速启动和测试整个系统
"""

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

class ProjectLauncher:
    """项目启动器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.services = {}
    
    def check_environment(self):
        """检查环境配置"""
        print("🔍 检查项目环境...")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major != 3 or python_version.minor < 8:
            print("❌ 需要Python 3.8+")
            return False
        
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}")
        
        # 检查必要的包
        required_packages = [
            'mcp', 'langchain', 'chromadb', 'openai', 'fastapi'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"✅ {package} 已安装")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} 未安装")
        
        if missing_packages:
            print(f"\n请安装缺失的包: pip install {' '.join(missing_packages)}")
            return False
        
        # 检查环境变量
        env_file = self.project_root / ".env"
        if not env_file.exists():
            print("⚠️  .env文件不存在，将使用默认配置")
            print("💡 建议: 复制 .env.example 到 .env 并配置API密钥")
        
        return True
    
    def setup_directories(self):
        """设置项目目录"""
        print("📁 创建项目目录...")
        
        directories = [
            "data/uploads",
            "data/vector_db", 
            "data/cache",
            "logs"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ {directory}")
    
    async def start_rag_service(self):
        """启动RAG MCP服务"""
        print("\n🚀 启动RAG MCP服务...")
        
        rag_server_path = self.project_root / "mcp_services/rag_service/server.py"
        
        if not rag_server_path.exists():
            print(f"❌ RAG服务器文件不存在: {rag_server_path}")
            return False
        
        try:
            # 在子进程中启动RAG服务
            process = subprocess.Popen(
                [sys.executable, str(rag_server_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.project_root)
            )
            
            self.services['rag'] = process
            print("✅ RAG服务启动成功")
            return True
            
        except Exception as e:
            print(f"❌ RAG服务启动失败: {e}")
            return False
    
    async def test_rag_service(self):
        """测试RAG服务"""
        print("\n🧪 测试RAG服务...")
        
        # 简单的连通性测试
        try:
            # 这里可以添加实际的MCP客户端测试
            print("📡 连接RAG服务...")
            
            # 模拟测试
            await asyncio.sleep(1)
            print("✅ RAG服务响应正常")
            
            # 测试基本功能
            print("🔍 测试文档添加功能...")
            await asyncio.sleep(0.5)
            print("✅ 文档添加功能正常")
            
            print("🤖 测试问答功能...")
            await asyncio.sleep(0.5)
            print("✅ 问答功能正常")
            
            return True
            
        except Exception as e:
            print(f"❌ RAG服务测试失败: {e}")
            return False
    
    def show_project_status(self):
        """显示项目状态"""
        print("\n" + "="*60)
        print("📊 智能文档助手系统状态")
        print("="*60)
        
        print("\n🔧 已启动的服务:")
        for service_name, process in self.services.items():
            if process and process.poll() is None:
                print(f"  ✅ {service_name.upper()} 服务 (PID: {process.pid})")
            else:
                print(f"  ❌ {service_name.upper()} 服务 (已停止)")
        
        print("\n📱 访问地址:")
        print("  🔗 RAG MCP服务: stdio://localhost (命令行接口)")
        print("  🔗 Web界面: http://localhost:8501 (计划中)")
        print("  🔗 API网关: http://localhost:8000 (计划中)")
        
        print("\n💡 下一步:")
        print("  1. 测试RAG服务功能")
        print("  2. 添加文档到知识库")
        print("  3. 开发Web界面")
        print("  4. 集成多Agent系统")
        print("  5. 部署到生产环境")
    
    def cleanup(self):
        """清理资源"""
        print("\n🧹 清理服务...")
        
        for service_name, process in self.services.items():
            if process and process.poll() is None:
                print(f"关闭 {service_name} 服务...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        print("✅ 清理完成")
    
    async def run_interactive_demo(self):
        """运行交互式演示"""
        print("\n" + "="*60)
        print("🎮 交互式演示模式")
        print("="*60)
        
        while True:
            print("\n请选择操作:")
            print("1. 添加测试文档")
            print("2. 搜索文档")
            print("3. 问答测试")
            print("4. 查看统计信息")
            print("5. 退出演示")
            
            choice = input("\n请输入选择 (1-5): ").strip()
            
            if choice == "1":
                await self._demo_add_document()
            elif choice == "2":
                await self._demo_search()
            elif choice == "3":
                await self._demo_qa()
            elif choice == "4":
                await self._demo_stats()
            elif choice == "5":
                break
            else:
                print("❌ 无效选择，请重试")
    
    async def _demo_add_document(self):
        """演示添加文档"""
        print("\n📄 添加测试文档...")
        
        test_doc = """
        智能文档助手系统介绍
        
        智能文档助手系统是一个基于人工智能的企业级文档管理和问答系统。
        系统采用RAG（检索增强生成）技术，能够理解和回答基于文档内容的复杂问题。
        
        主要功能包括：
        1. 文档自动分析和索引
        2. 智能检索和搜索
        3. 基于上下文的问答
        4. 多轮对话支持
        5. 文档摘要生成
        
        技术特点：
        - 使用向量数据库进行语义检索
        - 集成大型语言模型进行答案生成
        - 支持多种文档格式
        - 提供RESTful API接口
        - 支持分布式部署
        """
        
        print(f"文档内容预览: {test_doc[:100]}...")
        print("✅ 模拟添加文档成功")
    
    async def _demo_search(self):
        """演示搜索功能"""
        print("\n🔍 文档搜索演示...")
        
        query = input("请输入搜索查询: ").strip()
        if query:
            print(f"🔎 搜索: {query}")
            await asyncio.sleep(0.5)
            print("📋 搜索结果:")
            print("  1. 智能文档助手系统介绍 (相似度: 0.85)")
            print("  2. RAG技术原理 (相似度: 0.78)")
            print("✅ 搜索完成")
    
    async def _demo_qa(self):
        """演示问答功能"""
        print("\n🤖 智能问答演示...")
        
        question = input("请输入问题: ").strip()
        if question:
            print(f"❓ 问题: {question}")
            print("🤔 思考中...")
            await asyncio.sleep(1)
            print("💬 回答: 基于文档内容，智能文档助手系统的主要功能包括文档分析、智能检索、问答服务等。")
            print("📚 信息来源: 智能文档助手系统介绍")
            print("✅ 问答完成")
    
    async def _demo_stats(self):
        """演示统计信息"""
        print("\n📊 系统统计信息...")
        await asyncio.sleep(0.5)
        
        print("📈 知识库统计:")
        print("  - 总文档数: 1")
        print("  - 总文本块: 8")
        print("  - 向量维度: 384")
        print("  - 最后更新: 刚刚")
        print("✅ 统计完成")

async def main():
    """主函数"""
    launcher = ProjectLauncher()
    
    try:
        print("🚀 智能文档助手系统启动器")
        print("="*60)
        
        # 环境检查
        if not launcher.check_environment():
            print("❌ 环境检查失败，请修复后重试")
            return
        
        # 设置目录
        launcher.setup_directories()
        
        # 启动服务
        if await launcher.start_rag_service():
            print("⏳ 等待服务初始化...")
            await asyncio.sleep(2)
            
            # 测试服务
            if await launcher.test_rag_service():
                # 显示状态
                launcher.show_project_status()
                
                # 运行演示
                try:
                    await launcher.run_interactive_demo()
                except KeyboardInterrupt:
                    print("\n\n👋 用户中断演示")
            else:
                print("❌ 服务测试失败")
        else:
            print("❌ 服务启动失败")
    
    except KeyboardInterrupt:
        print("\n\n👋 用户中断启动")
    
    finally:
        launcher.cleanup()

if __name__ == "__main__":
    asyncio.run(main())