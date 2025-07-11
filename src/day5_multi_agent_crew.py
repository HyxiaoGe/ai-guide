#!/usr/bin/env python3
"""
第5天：多Agent系统实战
通过CrewAI框架构建一个研究写作团队，展示多Agent协作的核心功能
"""

import os
from typing import Dict, List
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"


@tool
def search_tool(query: str) -> str:
    """
    搜索工具 - 模拟网络搜索
    
    参数:
        query: 搜索查询
    
    返回:
        搜索结果摘要
    """
    # 在实际应用中，这里会调用真实的搜索API
    search_results = {
        "人工智能": "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统...",
        "机器学习": "机器学习是人工智能的一个子集，专注于算法和统计模型，使计算机系统能够从数据中学习...",
        "深度学习": "深度学习是机器学习的一个分支，使用人工神经网络来模拟人脑的学习过程...",
        "LangChain": "LangChain是一个开源框架，用于构建基于大型语言模型（LLM）的应用程序...",
        "CrewAI": "CrewAI是一个多Agent协作框架，允许创建一组AI代理来协同工作完成复杂任务..."
    }
    
    # 简单匹配
    for keyword, result in search_results.items():
        if keyword.lower() in query.lower():
            return f"搜索结果：{result}"
    
    return f"关于'{query}'的搜索结果：这是一个相关的技术主题，需要进一步研究。"


@tool
def file_write_tool(filename: str, content: str) -> str:
    """
    文件写入工具
    
    参数:
        filename: 文件名
        content: 文件内容
    
    返回:
        操作结果
    """
    try:
        # 确保目录存在
        os.makedirs("output", exist_ok=True)
        filepath = os.path.join("output", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"文件 {filename} 写入成功，路径：{filepath}"
    except Exception as e:
        return f"文件写入失败：{e}"


@tool
def analysis_tool(text: str) -> str:
    """
    文本分析工具
    
    参数:
        text: 要分析的文本
    
    返回:
        分析结果
    """
    # 简单的文本分析
    word_count = len(text.split())
    char_count = len(text)
    lines = len(text.split('\n'))
    
    # 检查关键词
    keywords = ["人工智能", "机器学习", "深度学习", "Agent", "AI"]
    found_keywords = [kw for kw in keywords if kw.lower() in text.lower()]
    
    analysis = f"""
文本分析结果：
- 字数：{word_count} 词
- 字符数：{char_count} 字符
- 行数：{lines} 行
- 技术关键词：{', '.join(found_keywords) if found_keywords else '无'}
- 内容质量：{'高质量技术内容' if found_keywords else '需要更多技术细节'}
"""
    
    return analysis.strip()


class ResearchWritingCrew:
    """研究写作团队 - 多Agent协作系统"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """
        初始化研究写作团队
        
        参数:
            model_name: 使用的LLM模型名称
        """
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.agents = self._create_agents()
        self.tasks = []
        self.crew = None
        
    def _create_agents(self) -> Dict[str, Agent]:
        """创建专业化的Agent团队"""
        
        # 研究员Agent - 负责信息收集和初步研究
        researcher = Agent(
            role="资深研究员",
            goal="深入研究指定主题，收集全面准确的信息",
            backstory="""
            你是一位经验丰富的技术研究员，擅长从多个角度深入分析技术主题。
            你有着敏锐的洞察力，能够发现主题的核心要点和发展趋势。
            你的研究总是全面、准确、有深度。
            """,
            verbose=True,
            allow_delegation=False,
            tools=[search_tool],
            llm=self.llm
        )
        
        # 写作专家Agent - 负责内容创作和文章结构
        writer = Agent(
            role="技术写作专家",
            goal="创作高质量、结构清晰的技术文章",
            backstory="""
            你是一位专业的技术写作专家，擅长将复杂的技术概念转化为易懂的文章。
            你的文章结构清晰、逻辑严密、表达准确。
            你特别善于为不同的读者群体调整写作风格和深度。
            """,
            verbose=True,
            allow_delegation=False,
            tools=[file_write_tool],
            llm=self.llm
        )
        
        # 质量分析师Agent - 负责内容审核和优化建议
        analyst = Agent(
            role="内容质量分析师",
            goal="分析内容质量，提供专业的改进建议",
            backstory="""
            你是一位严谨的内容质量分析师，擅长评估技术内容的准确性、完整性和可读性。
            你有着极高的质量标准，能够发现内容中的不足并提供具体的改进建议。
            你的分析总是客观、详细、有建设性。
            """,
            verbose=True,
            allow_delegation=False,
            tools=[analysis_tool],
            llm=self.llm
        )
        
        # 项目协调员Agent - 负责任务协调和流程管理
        coordinator = Agent(
            role="项目协调员",
            goal="协调团队工作，确保项目按计划高质量完成",
            backstory="""
            你是一位经验丰富的项目协调员，擅长管理复杂的协作项目。
            你能够合理分配任务、协调资源、确保团队高效协作。
            你总是关注项目的整体目标，确保最终交付物符合要求。
            """,
            verbose=True,
            allow_delegation=True,  # 协调员可以委派任务
            llm=self.llm
        )
        
        return {
            "researcher": researcher,
            "writer": writer,
            "analyst": analyst,
            "coordinator": coordinator
        }
    
    def create_research_writing_tasks(self, topic: str, article_type: str = "技术博客") -> List[Task]:
        """
        创建研究写作任务序列
        
        参数:
            topic: 研究主题
            article_type: 文章类型
        
        返回:
            任务列表
        """
        # 任务1：深度研究
        research_task = Task(
            description=f"""
            对主题"{topic}"进行深入研究。
            
            具体要求：
            1. 搜集该主题的核心概念和定义
            2. 分析技术背景和发展历程
            3. 识别关键技术特点和优势
            4. 研究当前应用场景和案例
            5. 分析未来发展趋势
            
            输出格式：
            - 结构化的研究报告
            - 包含具体的技术细节
            - 提供准确的信息来源
            """,
            agent=self.agents["researcher"],
            expected_output="全面的技术研究报告，包含核心概念、技术特点、应用场景和发展趋势"
        )
        
        # 任务2：文章撰写
        writing_task = Task(
            description=f"""
            基于研究员的研究成果，撰写一篇关于"{topic}"的{article_type}。
            
            具体要求：
            1. 文章结构清晰，逻辑严密
            2. 语言准确，表达清楚
            3. 内容深度适中，适合目标读者
            4. 包含实际的代码示例或应用案例
            5. 字数控制在1500-2000字
            
            文章结构建议：
            - 引言：介绍主题背景和重要性
            - 核心概念：详细解释关键技术
            - 技术特点：分析优势和特色
            - 应用实践：提供具体案例
            - 总结：归纳要点和展望
            
            请将最终文章保存为Markdown格式文件。
            """,
            agent=self.agents["writer"],
            expected_output="高质量的技术文章，结构清晰，内容准确，保存为Markdown文件",
            context=[research_task]  # 依赖研究任务的输出
        )
        
        # 任务3：质量分析
        analysis_task = Task(
            description=f"""
            对撰写的文章进行全面的质量分析。
            
            分析维度：
            1. 内容准确性：技术信息是否准确
            2. 结构完整性：文章结构是否清晰完整
            3. 逻辑连贯性：论述是否逻辑清晰
            4. 可读性：语言表达是否清楚易懂
            5. 实用性：是否提供有价值的信息
            
            输出要求：
            1. 详细的分析报告
            2. 具体的改进建议
            3. 质量评分（1-10分）
            4. 改进优先级排序
            """,
            agent=self.agents["analyst"],
            expected_output="详细的质量分析报告，包含具体改进建议和质量评分",
            context=[writing_task]  # 依赖写作任务的输出
        )
        
        # 任务4：项目总结
        coordination_task = Task(
            description=f"""
            作为项目协调员，对整个研究写作项目进行总结。
            
            总结内容：
            1. 项目执行情况：各阶段完成质量
            2. 团队协作效果：Agent之间的配合情况
            3. 最终成果评估：文章质量和价值
            4. 改进建议：下次协作的优化方向
            5. 项目亮点：值得肯定的成果
            
            请提供一个简洁而全面的项目总结报告。
            """,
            agent=self.agents["coordinator"],
            expected_output="全面的项目总结报告，包含执行情况、成果评估和改进建议",
            context=[research_task, writing_task, analysis_task]  # 依赖所有前置任务
        )
        
        return [research_task, writing_task, analysis_task, coordination_task]
    
    def execute_project(self, topic: str, article_type: str = "技术博客") -> Dict:
        """
        执行完整的研究写作项目
        
        参数:
            topic: 研究主题
            article_type: 文章类型
        
        返回:
            项目执行结果
        """
        print(f"🚀 启动多Agent研究写作项目")
        print(f"📋 主题：{topic}")
        print(f"📝 类型：{article_type}")
        print("=" * 60)
        
        # 创建任务
        self.tasks = self.create_research_writing_tasks(topic, article_type)
        
        # 创建团队
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            verbose=2,  # 详细输出
            process=Process.sequential  # 顺序执行
        )
        
        # 执行项目
        print("\n🎯 开始执行任务...")
        try:
            result = self.crew.kickoff()
            
            print("\n✅ 项目执行完成！")
            print("=" * 60)
            
            # 返回结果摘要
            return {
                "status": "success",
                "topic": topic,
                "article_type": article_type,
                "agents_count": len(self.agents),
                "tasks_count": len(self.tasks),
                "final_result": result,
                "summary": "多Agent团队成功完成研究写作任务"
            }
            
        except Exception as e:
            print(f"\n❌ 项目执行出错：{e}")
            return {
                "status": "error",
                "error": str(e),
                "topic": topic
            }
    
    def get_agent_info(self) -> Dict:
        """获取Agent团队信息"""
        info = {}
        for name, agent in self.agents.items():
            info[name] = {
                "role": agent.role,
                "goal": agent.goal,
                "tools": [tool.name for tool in getattr(agent, 'tools', [])],
                "allow_delegation": getattr(agent, 'allow_delegation', False)
            }
        return info


def demonstrate_simple_collaboration():
    """演示简单的两Agent协作"""
    print("\n" + "="*60)
    print("🔸 演示1：简单两Agent协作")
    print("="*60)
    
    # 创建简单的LLM实例
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
    
    # 创建研究员
    researcher = Agent(
        role="技术研究员",
        goal="快速研究技术主题并提供要点",
        backstory="你是一位高效的技术研究员，善于快速获取关键信息。",
        verbose=True,
        tools=[search_tool],
        llm=llm
    )
    
    # 创建总结员
    summarizer = Agent(
        role="内容总结员", 
        goal="将研究结果整理成简洁的摘要",
        backstory="你擅长将复杂信息整理成清晰简洁的摘要。",
        verbose=True,
        llm=llm
    )
    
    # 创建任务
    research_task = Task(
        description="研究'RAG技术'的核心概念和应用场景",
        agent=researcher,
        expected_output="RAG技术的核心概念和主要应用场景"
    )
    
    summary_task = Task(
        description="将研究结果整理成200字以内的技术摘要",
        agent=summarizer,
        expected_output="简洁的RAG技术摘要",
        context=[research_task]
    )
    
    # 创建简单团队
    simple_crew = Crew(
        agents=[researcher, summarizer],
        tasks=[research_task, summary_task],
        verbose=2,
        process=Process.sequential
    )
    
    # 执行
    try:
        result = simple_crew.kickoff()
        print(f"\n📋 协作结果：\n{result}")
    except Exception as e:
        print(f"演示出错：{e}")


def main():
    """主函数：演示多Agent系统"""
    print("🚀 CrewAI多Agent系统演示")
    print("=" * 60)
    
    # 演示1：简单协作
    demonstrate_simple_collaboration()
    
    # 演示2：完整的研究写作团队
    print("\n" + "="*60)
    print("🔸 演示2：完整多Agent研究写作团队")
    print("="*60)
    
    # 创建研究写作团队
    crew_system = ResearchWritingCrew()
    
    # 显示团队信息
    print("\n👥 团队成员信息：")
    agent_info = crew_system.get_agent_info()
    for name, info in agent_info.items():
        print(f"\n🤖 {name}:")
        print(f"   角色：{info['role']}")
        print(f"   目标：{info['goal']}")
        print(f"   工具：{', '.join(info['tools']) if info['tools'] else '无'}")
        print(f"   可委派：{'是' if info['allow_delegation'] else '否'}")
    
    # 执行项目
    test_topics = [
        "LangGraph工作流编排技术",
        "向量数据库在RAG系统中的应用"
    ]
    
    for topic in test_topics[:1]:  # 演示第一个主题
        print(f"\n\n📊 执行项目：{topic}")
        result = crew_system.execute_project(topic, "技术教程")
        
        print(f"\n📈 项目结果摘要：")
        print(f"  - 状态：{result['status']}")
        if result['status'] == 'success':
            print(f"  - 主题：{result['topic']}")
            print(f"  - Agent数量：{result['agents_count']}")
            print(f"  - 任务数量：{result['tasks_count']}")
            print(f"  - 摘要：{result['summary']}")
        else:
            print(f"  - 错误：{result.get('error', '未知错误')}")
    
    print("\n" + "="*60)
    print("✅ 多Agent系统演示完成")
    print("💡 提示：检查 output/ 目录查看生成的文件")
    print("="*60)


if __name__ == "__main__":
    main()