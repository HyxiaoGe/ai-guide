#!/usr/bin/env python3
"""
第1天：创建一个简单的AI Agent
这个Agent能够：
1. 进行数学计算
2. 查询天气（模拟）
3. 搜索知识（模拟）
"""

import os
from typing import Optional
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_openai import ChatOpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class SimpleAgent:
    """简单的AI Agent实现"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0):
        """
        初始化Agent
        
        参数:
            model_name: 使用的模型名称
            temperature: 模型创造性参数，0为最确定性
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()]
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self) -> list[Tool]:
        """创建Agent可用的工具"""
        
        def calculator(expression: str) -> str:
            """
            执行数学计算
            
            参数:
                expression: 数学表达式
            返回:
                计算结果或错误信息
            """
            try:
                # 安全评估数学表达式
                allowed_names = {
                    k: v for k, v in __builtins__.items() 
                    if k in ['abs', 'round', 'min', 'max', 'sum', 'pow']
                }
                result = eval(expression, {"__builtins__": {}}, allowed_names)
                return f"计算结果：{result}"
            except Exception as e:
                return f"计算错误：{str(e)}"
        
        def weather_query(city: str) -> str:
            """
            查询天气信息（模拟数据）
            
            参数:
                city: 城市名称
            返回:
                天气信息
            """
            # 模拟的天气数据
            weather_db = {
                "北京": {"天气": "晴", "温度": 25, "湿度": 45, "风力": "3级"},
                "上海": {"天气": "多云", "温度": 22, "湿度": 65, "风力": "2级"},
                "广州": {"天气": "小雨", "温度": 28, "湿度": 80, "风力": "1级"},
                "深圳": {"天气": "阴", "温度": 27, "湿度": 75, "风力": "2级"},
            }
            
            if city in weather_db:
                info = weather_db[city]
                return (f"{city}天气：{info['天气']}，"
                       f"温度{info['温度']}°C，"
                       f"湿度{info['湿度']}%，"
                       f"风力{info['风力']}")
            else:
                return f"抱歉，暂无{city}的天气数据"
        
        def knowledge_search(query: str) -> str:
            """
            搜索知识库（模拟数据）
            
            参数:
                query: 搜索查询
            返回:
                相关知识
            """
            # 模拟的知识库
            knowledge_base = {
                "langchain": "LangChain是一个用于开发由语言模型驱动的应用程序的框架。它提供了一套工具、组件和接口，简化了创建由大型语言模型(LLM)驱动的应用程序的过程。",
                "agent": "AI Agent是一个能够感知环境、做出决策并采取行动的智能系统。它具有自主性、反应性、主动性和社交能力等特征。",
                "rag": "RAG（Retrieval-Augmented Generation）是一种结合了信息检索和生成式AI的技术，通过检索相关文档来增强语言模型的生成能力。",
                "向量数据库": "向量数据库是专门用于存储和检索高维向量数据的数据库系统，常用于语义搜索、推荐系统和AI应用中。"
            }
            
            # 简单的关键词匹配
            query_lower = query.lower()
            for key, value in knowledge_base.items():
                if key.lower() in query_lower:
                    return f"关于{key}的信息：{value}"
            
            return "抱歉，知识库中暂无相关信息"
        
        # 返回工具列表
        return [
            Tool(
                name="Calculator",
                func=calculator,
                description="用于执行数学计算。输入应该是一个有效的数学表达式，如'2+2'或'10*5'"
            ),
            Tool(
                name="WeatherQuery", 
                func=weather_query,
                description="查询中国城市的天气信息。输入应该是城市名称，如'北京'或'上海'"
            ),
            Tool(
                name="KnowledgeSearch",
                func=knowledge_search,
                description="搜索AI相关知识。输入应该是要查询的概念，如'langchain'或'agent'"
            )
        ]
    
    def _create_agent(self):
        """创建并配置Agent"""
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,  # 显示思考过程
            handle_parsing_errors=True,
            max_iterations=5  # 最大迭代次数
        )
    
    def run(self, query: str) -> str:
        """
        运行Agent处理查询
        
        参数:
            query: 用户查询
        返回:
            Agent的回答
        """
        try:
            response = self.agent.run(query)
            return response
        except Exception as e:
            return f"处理出错：{str(e)}"


def main():
    """主函数：演示Agent的使用"""
    print("=== 第1天：简单AI Agent演示 ===\n")
    
    # 创建Agent
    agent = SimpleAgent()
    
    # 测试用例
    test_queries = [
        "北京的天气怎么样？",
        "计算 25 * 4 + 10 的结果",
        "告诉我什么是LangChain",
        "如果上海的温度超过20度，计算100除以5的结果",
        "搜索一下RAG技术的信息，并计算3的4次方"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试 {i} ---")
        print(f"查询: {query}")
        print("\nAgent思考过程:")
        result = agent.run(query)
        print(f"\n最终回答: {result}")
        print("-" * 50)


if __name__ == "__main__":
    main()