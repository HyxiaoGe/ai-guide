#!/usr/bin/env python3
"""
第4天：LangGraph工作流编排实战
通过构建一个文章写作助手，展示LangGraph的核心功能
"""

import os
from typing import TypedDict, Annotated, Sequence, Literal, Dict, Any, List
import operator
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

# 加载环境变量
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"


class ArticleState(TypedDict):
    """
    文章写作工作流的状态定义
    
    这个状态会在所有节点之间传递和更新
    使用TypedDict确保类型安全
    """
    # 基础信息
    topic: str                                      # 文章主题
    article_type: str                               # 文章类型：blog/tutorial/news
    target_audience: str                            # 目标读者
    
    # 写作过程
    outline: List[str]                              # 文章大纲
    research_notes: Annotated[List[str], operator.add]  # 研究笔记（累积）
    draft_sections: Dict[str, str]                  # 各部分草稿
    current_draft: str                              # 当前完整草稿
    
    # 质量控制
    quality_checks: Dict[str, bool]                 # 质量检查项
    revision_suggestions: List[str]                 # 修改建议
    revision_count: int                             # 修订次数
    is_complete: bool                               # 是否完成
    
    # 流程跟踪
    workflow_steps: Annotated[List[str], operator.add]  # 执行步骤记录


class ArticleWorkflow:
    """文章写作工作流系统"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """
        初始化工作流
        
        参数:
            model_name: 使用的LLM模型名称
        """
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.workflow = None
        self.app = None
        
        # 构建工作流
        self._build_workflow()
        
    def _build_workflow(self):
        """构建完整的工作流图"""
        # 创建状态图
        self.workflow = StateGraph(ArticleState)
        
        # 添加所有节点
        self.workflow.add_node("analyze_requirements", self.analyze_requirements)
        self.workflow.add_node("create_outline", self.create_outline)
        self.workflow.add_node("research_topic", self.research_topic)
        self.workflow.add_node("write_sections", self.write_sections)
        self.workflow.add_node("combine_draft", self.combine_draft)
        self.workflow.add_node("quality_check", self.quality_check)
        self.workflow.add_node("revise_article", self.revise_article)
        self.workflow.add_node("finalize_article", self.finalize_article)
        
        # 设置入口点
        self.workflow.set_entry_point("analyze_requirements")
        
        # 添加边（定义执行顺序）
        self.workflow.add_edge("analyze_requirements", "create_outline")
        self.workflow.add_edge("create_outline", "research_topic")
        self.workflow.add_edge("research_topic", "write_sections")
        self.workflow.add_edge("write_sections", "combine_draft")
        self.workflow.add_edge("combine_draft", "quality_check")
        
        # 添加条件边（质量检查后的分支）
        self.workflow.add_conditional_edges(
            "quality_check",
            self.quality_router,  # 路由函数
            {
                "revise": "revise_article",      # 需要修改
                "finalize": "finalize_article"   # 可以完成
            }
        )
        
        # 修改后重新检查
        self.workflow.add_edge("revise_article", "combine_draft")
        
        # 完成
        self.workflow.add_edge("finalize_article", END)
        
        # 编译工作流
        # 添加内存检查点，支持中断和恢复
        memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=memory)
        
    def analyze_requirements(self, state: ArticleState) -> ArticleState:
        """
        分析写作需求
        
        这是工作流的第一步，分析用户提供的信息
        并设置默认值
        """
        print("\n📋 分析写作需求...")
        
        # 确保有基本信息
        topic = state.get("topic", "")
        article_type = state.get("article_type", "blog")
        target_audience = state.get("target_audience", "general")
        
        # 根据文章类型设置初始参数
        if article_type == "tutorial":
            quality_threshold = {"clarity": 0.8, "completeness": 0.9}
        elif article_type == "news":
            quality_threshold = {"accuracy": 0.9, "timeliness": 0.8}
        else:  # blog
            quality_threshold = {"engagement": 0.7, "originality": 0.8}
        
        print(f"  - 主题：{topic}")
        print(f"  - 类型：{article_type}")
        print(f"  - 目标读者：{target_audience}")
        
        return {
            "workflow_steps": ["需求分析完成"],
            "quality_checks": {},
            "revision_count": 0,
            "is_complete": False
        }
    
    def create_outline(self, state: ArticleState) -> ArticleState:
        """
        创建文章大纲
        
        基于主题和类型生成结构化的大纲
        """
        print("\n📝 创建文章大纲...")
        
        prompt = ChatPromptTemplate.from_template("""
        为以下主题创建一个{article_type}类型文章的大纲：
        
        主题：{topic}
        目标读者：{target_audience}
        
        请创建一个包含4-6个主要部分的大纲，每个部分用一句话描述。
        输出格式：
        1. 部分标题 - 简短描述
        2. 部分标题 - 简短描述
        ...
        """)
        
        response = self.llm.invoke(
            prompt.format_messages(
                topic=state["topic"],
                article_type=state["article_type"],
                target_audience=state["target_audience"]
            )
        )
        
        # 解析大纲（简单解析）
        outline_text = response.content
        outline = []
        
        for line in outline_text.split('\n'):
            line = line.strip()
            if line and any(c.isdigit() for c in line[:3]):  # 检查是否以数字开头
                # 提取标题部分
                if ' - ' in line:
                    title = line.split(' - ')[0].strip()
                    title = title.split('. ', 1)[-1] if '. ' in title else title
                    outline.append(title)
        
        # 如果解析失败，使用默认大纲
        if not outline:
            outline = ["引言", "主要内容", "深入分析", "总结"]
        
        print(f"  生成了{len(outline)}个部分的大纲")
        for i, section in enumerate(outline, 1):
            print(f"  {i}. {section}")
        
        return {
            "outline": outline,
            "workflow_steps": ["大纲创建完成"]
        }
    
    def research_topic(self, state: ArticleState) -> ArticleState:
        """
        研究主题
        
        为每个大纲部分收集相关信息
        在实际应用中，这里可以调用搜索API或RAG系统
        """
        print("\n🔍 研究主题资料...")
        
        research_notes = []
        
        for section in state["outline"]:
            # 模拟研究过程
            prompt = f"""
            为文章部分"{section}"提供相关的要点和信息。
            主题：{state['topic']}
            
            请提供2-3个关键要点。
            """
            
            response = self.llm.invoke(prompt)
            note = f"[{section}] {response.content[:200]}..."
            research_notes.append(note)
            print(f"  ✓ 完成 {section} 的研究")
        
        return {
            "research_notes": research_notes,
            "workflow_steps": ["主题研究完成"]
        }
    
    def write_sections(self, state: ArticleState) -> ArticleState:
        """
        撰写各个部分
        
        基于大纲和研究笔记撰写每个部分
        """
        print("\n✍️ 撰写文章各部分...")
        
        draft_sections = {}
        
        for i, section in enumerate(state["outline"]):
            # 获取相关的研究笔记
            relevant_notes = [
                note for note in state.get("research_notes", [])
                if section in note
            ]
            
            prompt = ChatPromptTemplate.from_template("""
            撰写文章的"{section}"部分。
            
            文章主题：{topic}
            文章类型：{article_type}
            目标读者：{target_audience}
            
            参考信息：
            {research_notes}
            
            请撰写200-300字的内容。
            """)
            
            response = self.llm.invoke(
                prompt.format_messages(
                    section=section,
                    topic=state["topic"],
                    article_type=state["article_type"],
                    target_audience=state["target_audience"],
                    research_notes="\n".join(relevant_notes) if relevant_notes else "无"
                )
            )
            
            draft_sections[section] = response.content
            print(f"  ✓ 完成 {section} 的撰写")
        
        return {
            "draft_sections": draft_sections,
            "workflow_steps": ["各部分撰写完成"]
        }
    
    def combine_draft(self, state: ArticleState) -> ArticleState:
        """
        组合完整草稿
        
        将各个部分组合成完整的文章
        """
        print("\n📄 组合完整文章...")
        
        # 创建标题
        title_prompt = f"为关于'{state['topic']}'的{state['article_type']}创建一个吸引人的标题："
        title_response = self.llm.invoke(title_prompt)
        title = title_response.content.strip()
        
        # 组合文章
        article_parts = [f"# {title}\n"]
        
        for section, content in state["draft_sections"].items():
            article_parts.append(f"\n## {section}\n")
            article_parts.append(content)
        
        # 添加结尾（如果需要）
        if state["article_type"] == "tutorial":
            article_parts.append("\n## 下一步\n")
            article_parts.append("希望这个教程对你有帮助！如果有问题，欢迎留言讨论。")
        
        current_draft = "\n".join(article_parts)
        
        print(f"  ✓ 文章组合完成，总长度：{len(current_draft)} 字符")
        
        return {
            "current_draft": current_draft,
            "workflow_steps": ["文章组合完成"]
        }
    
    def quality_check(self, state: ArticleState) -> ArticleState:
        """
        质量检查
        
        检查文章质量并生成修改建议
        """
        print("\n🔍 执行质量检查...")
        
        draft = state["current_draft"]
        revision_count = state.get("revision_count", 0)
        
        # 执行多项检查
        quality_checks = {
            "length": len(draft) > 500,  # 长度检查
            "structure": all(section in draft for section in state["outline"]),  # 结构完整性
            "revision": revision_count > 0  # 至少修改过一次
        }
        
        # 生成修改建议（如果需要）
        revision_suggestions = []
        
        if not quality_checks["length"]:
            revision_suggestions.append("文章过短，需要扩充内容")
        
        if not quality_checks["structure"]:
            revision_suggestions.append("部分章节缺失，需要补充")
        
        # 使用LLM进行内容质量评估
        if revision_count < 2:  # 最多修改2次
            quality_prompt = f"""
            评估以下文章草稿，提供1-2个具体的改进建议：
            
            {draft[:500]}...
            
            改进建议：
            """
            
            suggestions_response = self.llm.invoke(quality_prompt)
            llm_suggestions = suggestions_response.content.strip().split('\n')
            revision_suggestions.extend([s.strip() for s in llm_suggestions if s.strip()][:2])
        
        # 判断是否需要修改
        needs_revision = len(revision_suggestions) > 0 and revision_count < 2
        
        print(f"  检查项目：")
        for check, passed in quality_checks.items():
            print(f"    - {check}: {'✓ 通过' if passed else '✗ 需改进'}")
        
        if revision_suggestions:
            print(f"  修改建议：")
            for suggestion in revision_suggestions:
                print(f"    - {suggestion}")
        
        return {
            "quality_checks": quality_checks,
            "revision_suggestions": revision_suggestions,
            "workflow_steps": ["质量检查完成"]
        }
    
    def quality_router(self, state: ArticleState) -> Literal["revise", "finalize"]:
        """
        质量路由器
        
        根据质量检查结果决定下一步
        这是一个条件函数，返回下一个节点的名称
        """
        suggestions = state.get("revision_suggestions", [])
        revision_count = state.get("revision_count", 0)
        
        # 如果有修改建议且修改次数未超限，则修改
        if suggestions and revision_count < 2:
            return "revise"
        else:
            return "finalize"
    
    def revise_article(self, state: ArticleState) -> ArticleState:
        """
        修改文章
        
        根据建议修改文章
        """
        print("\n📝 修改文章...")
        
        current_draft = state["current_draft"]
        suggestions = state.get("revision_suggestions", [])
        
        # 构建修改提示
        revision_prompt = ChatPromptTemplate.from_template("""
        请根据以下建议修改文章：
        
        修改建议：
        {suggestions}
        
        原文章：
        {draft}
        
        请提供修改后的完整文章。
        """)
        
        response = self.llm.invoke(
            revision_prompt.format_messages(
                suggestions="\n".join(f"- {s}" for s in suggestions),
                draft=current_draft
            )
        )
        
        revised_draft = response.content
        
        # 更新修订次数
        revision_count = state.get("revision_count", 0) + 1
        
        print(f"  ✓ 完成第 {revision_count} 次修改")
        
        return {
            "current_draft": revised_draft,
            "revision_count": revision_count,
            "revision_suggestions": [],  # 清空建议
            "workflow_steps": [f"第{revision_count}次修改完成"]
        }
    
    def finalize_article(self, state: ArticleState) -> ArticleState:
        """
        完成文章
        
        最后的润色和格式化
        """
        print("\n✅ 文章定稿...")
        
        # 可以在这里添加最终的格式化、元数据等
        
        print("  ✓ 文章写作完成！")
        
        return {
            "is_complete": True,
            "workflow_steps": ["文章定稿完成"]
        }
    
    def write_article(
        self, 
        topic: str, 
        article_type: str = "blog",
        target_audience: str = "general"
    ) -> Dict[str, Any]:
        """
        执行完整的文章写作流程
        
        参数:
            topic: 文章主题
            article_type: 文章类型 (blog/tutorial/news)
            target_audience: 目标读者
        
        返回:
            包含文章和执行信息的字典
        """
        # 初始状态
        initial_state = {
            "topic": topic,
            "article_type": article_type,
            "target_audience": target_audience,
            "workflow_steps": [],
            "draft_sections": {},
            "research_notes": [],
            "revision_suggestions": [],
            "quality_checks": {}
        }
        
        # 运行工作流
        # config用于支持中断和恢复
        config = {"configurable": {"thread_id": f"article_{topic[:20]}"}}
        
        result = self.app.invoke(initial_state, config)
        
        return result
    
    def visualize_workflow(self):
        """可视化工作流结构"""
        try:
            print("\n工作流结构图（Mermaid格式）：")
            print(self.app.get_graph().draw_mermaid())
            print("\n提示：将上面的代码复制到 https://mermaid.live 可以看到流程图")
        except Exception as e:
            print(f"无法生成可视化：{e}")


def main():
    """主函数：演示文章写作工作流"""
    print("🚀 LangGraph工作流编排演示：智能文章写作助手")
    print("=" * 60)
    
    # 创建工作流实例
    workflow = ArticleWorkflow()
    
    # 可视化工作流
    workflow.visualize_workflow()
    
    # 测试不同类型的文章
    test_cases = [
        {
            "topic": "如何使用LangGraph构建AI工作流",
            "article_type": "tutorial",
            "target_audience": "Python开发者"
        },
        {
            "topic": "2024年AI技术发展趋势",
            "article_type": "blog",
            "target_audience": "技术爱好者"
        }
    ]
    
    for test_case in test_cases[:1]:  # 演示第一个案例
        print(f"\n\n{'='*60}")
        print(f"📝 开始写作：{test_case['topic']}")
        print(f"   类型：{test_case['article_type']}")
        print(f"   读者：{test_case['target_audience']}")
        print("="*60)
        
        # 执行写作流程
        result = workflow.write_article(**test_case)
        
        # 显示结果
        print(f"\n\n📊 执行统计：")
        print(f"  - 执行步骤：{len(result.get('workflow_steps', []))}")
        print(f"  - 修订次数：{result.get('revision_count', 0)}")
        print(f"  - 是否完成：{'是' if result.get('is_complete') else '否'}")
        
        print(f"\n📋 执行过程：")
        for step in result.get("workflow_steps", []):
            print(f"  ✓ {step}")
        
        print(f"\n📄 最终文章预览：")
        print("-" * 60)
        final_draft = result.get("current_draft", "无内容")
        print(final_draft[:1000] + "..." if len(final_draft) > 1000 else final_draft)
        
        # 显示大纲
        print(f"\n📑 文章结构：")
        for i, section in enumerate(result.get("outline", []), 1):
            print(f"  {i}. {section}")


if __name__ == "__main__":
    main()