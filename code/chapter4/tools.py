import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from serpapi import SerpApiClient

load_dotenv(dotenv_path="../../.config", override=False)


# search工具函数
def search(query: str) -> str:
    """
    Search the query using SerpApi and return the result.
    """
    serpapi_api_key = os.getenv("SERPAPI_API_KEY")
    if not serpapi_api_key:
        raise ValueError("SERPAPI_API_KEY is not set in the environment variables.")

    params = {
        "engine": "google",
        "q": query,
        "api_key": serpapi_api_key,
        "gl": "us",
        "hl": "en",
    }
    client = SerpApiClient(params)
    results = client.get_dict()

    # print(f"Search results for query '{query}': {json.dumps(results, indent=2)}")

    # 智能解析:优先寻找最直接的答案
    if "answer_box_list" in results:
        return "\n".join(results["answer_box_list"])
    if "answer_box" in results and "answer" in results["answer_box"]:
        return results["answer_box"]["answer"]
    if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
        return results["knowledge_graph"]["description"]
    if "organic_results" in results and results["organic_results"]:
        # 如果没有直接答案，则返回前三个有机结果的摘要
        snippets = [
            f"[{i + 1}] {res.get('title', '')}\n{res.get('snippet', '')}"
            for i, res in enumerate(results["organic_results"][:3])
        ]
        return "\n\n".join(snippets)


# 管理工具
class ToolExecutor:
    """
    工具执行器，负责管理和执行工具
    """

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, tool_name: str, description: str, func: callable):
        """
        注册工具
        """
        if tool_name not in self.tools:
            self.tools[tool_name] = {"description": description, "function": func}

        print(f'Tool "{tool_name}" registered successfully.')

    def getTool(self, tool_name: str):
        """
        获取工具
        """
        return self.tools.get(tool_name, {}).get("function")

    def getavailableTools(self):
        """
        获取所有可用工具的格式化描述字符串。
        """
        return "\n".join(
            [f"{name}: {info['description']}" for name, info in self.tools.items()]
        )


if __name__ == "__main__":
    query = "iPhone最新款"

    tool_executor = ToolExecutor()

    # 注册search工具
    tool_executor.registerTool("search", query, search)

    print("Available tools:")
    print(tool_executor.getavailableTools())

    tool_name = "search"

    # 执行search工具
    search_tool = tool_executor.getTool(tool_name)
    if search_tool:
        result = search_tool(query)
        print(f"\nSearch results for query '{query}':\n{result}")
    else:
        print(f'Search "{tool_name}" not found.')
