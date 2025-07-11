#!/usr/bin/env python3
"""
第2天：带有记忆的智能对话系统
演示LangChain的Memory系统和高级对话功能
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from pydantic import BaseModel, Field
from langchain.memory import (
    ConversationBufferMemory, 
    ConversationBufferWindowMemory,
    ConversationSummaryMemory
)
from langchain.chains import ConversationChain
from typing import List, Dict, Any

# 加载环境变量
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"


class UserProfile(BaseModel):
    """用户画像模型"""
    name: str = Field(description="用户姓名")
    interests: List[str] = Field(description="兴趣爱好列表")
    profession: str = Field(description="职业")
    learning_goals: List[str] = Field(description="学习目标")
    experience_level: str = Field(description="经验水平：beginner/intermediate/expert")


class AdvancedConversationSystem:
    """高级对话系统 - 集成多种记忆类型"""
    
    def __init__(self, memory_type: str = "buffer"):
        """
        初始化对话系统
        
        参数:
            memory_type: 记忆类型 - "buffer", "window", "summary"
        """
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000
        )
        
        # 根据类型创建不同的记忆系统
        self.memory = self._create_memory(memory_type)
        self.memory_type = memory_type
        
        # 用户画像提取器
        self.profile_parser = PydanticOutputParser(pydantic_object=UserProfile)
        
        # 创建对话链
        self.conversation = self._create_conversation_chain()
        
        print(f"🧠 记忆系统初始化完成：{memory_type}")
    
    def _create_memory(self, memory_type: str):
        """创建指定类型的记忆系统"""
        if memory_type == "buffer":
            return ConversationBufferMemory(
                memory_key="history",
                return_messages=True
            )
        elif memory_type == "window":
            return ConversationBufferWindowMemory(
                k=5,  # 记住最近5轮对话
                memory_key="history",
                return_messages=True
            )
        elif memory_type == "summary":
            return ConversationSummaryMemory(
                llm=self.llm,
                memory_key="history",
                return_messages=True
            )
        else:
            raise ValueError(f"不支持的记忆类型: {memory_type}")
    
    def _create_conversation_chain(self):
        """创建对话链"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            你是一个智能的个人学习助手，具有以下特点：
            
            1. 记忆能力：能记住用户的个人信息、兴趣和学习目标
            2. 个性化回答：根据用户的经验水平调整解释深度
            3. 连贯对话：基于对话历史提供相关建议
            4. 学习指导：为用户制定个性化的学习计划
            
            对话历史：{history}
            
            请根据用户的背景信息提供有针对性的回答。
            """),
            ("human", "{input}")
        ])
        
        return ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=prompt,
            verbose=False
        )
    
    def extract_user_profile(self, conversation_history: str) -> UserProfile:
        """从对话历史中提取用户画像"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            你是一个专业的用户画像分析师。请基于对话历史分析用户信息，并返回JSON格式的数据。

            分析要求：
            1. 仔细阅读对话历史，提取用户的姓名、职业、兴趣等信息
            2. 如果某些信息不明确，请根据上下文合理推测
            3. 如果完全没有提及，请填写"未知"
            4. 必须返回有效的JSON格式，包含所有必需字段

            返回格式示例：
            {{
                "name": "李华",
                "profession": "大学生",
                "interests": ["人工智能", "编程"],
                "learning_goals": ["学习机器学习", "提高编程技能"],
                "experience_level": "beginner"
            }}

            {format_instructions}
            """),
            ("human", "请分析以下对话历史并提取用户画像：\n\n{history}")
        ])
        
        chain = prompt | self.llm | self.profile_parser
        
        try:
            result = chain.invoke({
                "history": conversation_history,
                "format_instructions": self.profile_parser.get_format_instructions()
            })
            return result
        except Exception as e:
            print(f"用户画像提取失败: {e}")
            # 如果解析失败，尝试创建一个默认的用户画像
            try:
                # 简单的fallback：从对话中提取基本信息
                lines = conversation_history.split('\n')
                name = "未知"
                profession = "未知"
                interests = []
                
                for line in lines:
                    if "我是" in line or "我叫" in line:
                        # 简单提取姓名
                        if "我是" in line:
                            parts = line.split("我是")
                            if len(parts) > 1:
                                name_part = parts[1].split("，")[0].split(",")[0].strip()
                                if name_part and len(name_part) < 10:
                                    name = name_part
                        if "我叫" in line:
                            parts = line.split("我叫")
                            if len(parts) > 1:
                                name_part = parts[1].split("，")[0].split(",")[0].strip()
                                if name_part and len(name_part) < 10:
                                    name = name_part
                    
                    if "学生" in line:
                        profession = "学生"
                    elif "专业" in line:
                        profession = "专业学生"
                    
                    if "人工智能" in line or "AI" in line:
                        interests.append("人工智能")
                    if "机器学习" in line or "ML" in line:
                        interests.append("机器学习")
                    if "编程" in line or "程序" in line:
                        interests.append("编程")
                
                # 创建一个简单的字典作为fallback
                fallback_profile = {
                    "name": name,
                    "profession": profession,
                    "interests": interests if interests else ["未知"],
                    "learning_goals": ["提升技能"],
                    "experience_level": "beginner"
                }
                
                return fallback_profile
            except:
                return None
    
    def chat(self, message: str) -> str:
        """进行对话"""
        try:
            response = self.conversation.predict(input=message)
            return response
        except Exception as e:
            return f"对话处理出错：{str(e)}"
    
    def get_memory_info(self) -> Dict[str, Any]:
        """获取记忆系统信息"""
        info = {
            "memory_type": self.memory_type,
            "total_messages": 0,
            "content_preview": ""
        }
        
        if hasattr(self.memory, 'chat_memory') and self.memory.chat_memory.messages:
            info["total_messages"] = len(self.memory.chat_memory.messages)
            
            # 获取记忆内容预览
            if self.memory_type == "summary" and hasattr(self.memory, 'buffer'):
                info["content_preview"] = self.memory.buffer[:200] + "..."
            else:
                # 获取最近的几条消息
                recent_messages = self.memory.chat_memory.messages[-4:]
                content = ""
                for msg in recent_messages:
                    role = "Human" if msg.type == "human" else "AI"
                    content += f"{role}: {msg.content[:50]}...\n"
                info["content_preview"] = content
        
        return info
    
    def clear_memory(self):
        """清空记忆"""
        self.memory.clear()
        print("🗑️ 记忆已清空")


def demonstrate_memory_types():
    """演示不同记忆类型的效果"""
    print("=== 记忆系统对比演示 ===\n")
    
    # 测试对话序列
    test_messages = [
        "你好，我是李华，一名大学计算机专业的学生",
        "我对人工智能特别感兴趣，想深入学习",
        "我已经有Python基础，但对机器学习还比较陌生",
        "你能为我制定一个学习计划吗？",
        "谢谢你的建议，你还记得我是学什么专业的吗？"
    ]
    
    memory_types = ["buffer", "window", "summary"]
    
    for memory_type in memory_types:
        print(f"\n--- {memory_type.upper()} 记忆系统测试 ---")
        
        # 创建系统
        system = AdvancedConversationSystem(memory_type=memory_type)
        
        # 进行对话
        for i, msg in enumerate(test_messages, 1):
            response = system.chat(msg)
            print(f"\n轮次 {i}")
            print(f"用户: {msg}")
            print(f"AI: {response[:150]}...")
            
            # 显示记忆状态
            memory_info = system.get_memory_info()
            print(f"记忆状态: {memory_info['total_messages']} 条消息")
        
        # 显示最终记忆信息
        print(f"\n{memory_type.upper()} 最终记忆内容:")
        memory_info = system.get_memory_info()
        print(f"{memory_info['content_preview']}")
        print("-" * 60)


def interactive_conversation_demo():
    """交互式对话演示"""
    print("\n=== 交互式对话演示 ===")
    print("输入 'quit' 退出，'memory' 查看记忆状态，'clear' 清空记忆，'profile' 分析用户画像")
    
    # 创建对话系统（默认使用window记忆）
    system = AdvancedConversationSystem(memory_type="window")
    
    while True:
        user_input = input("\n你: ").strip()
        
        if user_input.lower() == 'quit':
            print("👋 再见！")
            break
        elif user_input.lower() == 'memory':
            memory_info = system.get_memory_info()
            print(f"\n📊 记忆状态:")
            print(f"类型: {memory_info['memory_type']}")
            print(f"消息数: {memory_info['total_messages']}")
            print(f"内容预览:\n{memory_info['content_preview']}")
            continue
        elif user_input.lower() == 'clear':
            system.clear_memory()
            continue
        elif user_input.lower() == 'profile':
            memory_info = system.get_memory_info()
            if memory_info['total_messages'] > 0:
                profile = system.extract_user_profile(memory_info['content_preview'])
                if profile:
                    print(f"\n👤 用户画像分析:")
                    # 兼容字典和对象两种格式
                    if isinstance(profile, dict):
                        print(f"姓名: {profile.get('name', '未知')}")
                        print(f"职业: {profile.get('profession', '未知')}")
                        print(f"兴趣: {', '.join(profile.get('interests', []))}")
                        print(f"学习目标: {', '.join(profile.get('learning_goals', []))}")
                        print(f"经验水平: {profile.get('experience_level', '未知')}")
                    else:
                        print(f"姓名: {profile.name}")
                        print(f"职业: {profile.profession}")
                        print(f"兴趣: {', '.join(profile.interests)}")
                        print(f"学习目标: {', '.join(profile.learning_goals)}")
                        print(f"经验水平: {profile.experience_level}")
                else:
                    print("用户画像分析失败")
            else:
                print("对话历史不足，无法分析用户画像")
            continue
        
        # 正常对话
        response = system.chat(user_input)
        print(f"\nAI: {response}")


def main():
    """主函数"""
    print("🤖 第2天：LangChain Memory系统演示")
    print("=" * 50)
    
    # 演示不同记忆类型
    demonstrate_memory_types()
    
    # 交互式演示
    try:
        interactive_conversation_demo()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")


if __name__ == "__main__":
    main()