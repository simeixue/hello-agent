import ast
import os
import re
from typing import Dict, List

from dotenv import load_dotenv
from llm_client import HelloAgentsLLM
from tools import ToolExecutor, search

load_dotenv(dotenv_path="../../.config", override=False)


PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划,```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""


# Planner类负责生成行动计划，Executor类负责执行计划中的每个步骤。
class Planner:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def plan(self, question: str) -> List[str]:
        """
        根据用户的问题生成一个行动计划。
        """
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        messages = [
            {"role": "system", "content": "你是一个顶级的AI规划专家。"},
            {"role": "user", "content": prompt},
        ]
        print("——————正在生成计划——————")

        response = self.llm_client.think(messages) or ""
        print(f"计划已生成：{response}")

        # 解析LLM输出的列表字符串
        try:
            # 找到```python和```之间的内容
            plan_str = response.split("```python")[1].split("```")[0].strip()
            # 使用ast.literal_eval来安全地执行字符串，将其转换为Python列表
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"❌ 解析计划时出错: {e}")
            print(f"原始响应: {response}")
            return []
        except Exception as e:
            print(f"❌ 解析计划时发生未知错误: {e}")
            return []


EXECUTOR_PROMPT_TEMPLATE = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决“当前步骤”，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对“当前步骤”的回答:
"""


class Executor:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def execute(self, question: str, plan: List[str]) -> str:
        """
        根据计划，逐步执行每个步骤
        """
        history = ""

        print("——————正在执行计划——————")
        for i, step in enumerate(plan):
            print(f"\n-->正在执行步骤 {i + 1}/{len(plan)}: {step}")
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question, plan=plan, history=history, current_step=step
            )
            messages = [
                {"role": "system", "content": "你是一位顶级的AI执行专家。"},
                {"role": "user", "content": prompt},
            ]
            response = self.llm_client.think(messages) or ""

            # 将当前步骤和结果添加到历史中，以便下一步使用
            history += f"步骤 {i + 1}: {step}\n结果: {response}\n"

            print(f"✅ 步骤 {i + 1} 执行完成，结果: {response}")

        # 最终结果是最后一个步骤的结果
        final_result = response
        return final_result


class PlanAndSolveAgent:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
        self.planner = Planner(llm_client)
        self.executor = Executor(llm_client)

    def plan_and_solve(self, question: str) -> str:
        """
        生成计划并执行，返回最终结果
        """
        # 1. 调用规划器生成计划
        plan = self.planner.plan(question)
        if not plan:
            print("❌ 未能生成有效的计划。")
            return "抱歉，我无法生成计划。"

        print(f"生成的计划: {plan}")

        # 2. 调用执行器执行计划
        final_result = self.executor.execute(question, plan)
        return final_result


if __name__ == "__main__":
    question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"

    llm_client = HelloAgentsLLM()
    agent = PlanAndSolveAgent(llm_client)

    final_result = agent.plan_and_solve(question)
    print(f"\n最终结果:\n{final_result}")
