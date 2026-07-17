import os

from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict

load_dotenv(
    dotenv_path="/Users/xue/workspace/learning_demo/hello-agent/.config", override=False
)


class HelloAgentsLLM:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL_ID")
        self.base_url = os.getenv("LLM_BASE_URL")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        if not self.api_key or not self.model or not self.base_url:
            raise ValueError(
                "请确保在 .config 文件中设置了 LLM_API_KEY、LLM_MODEL_ID 和 LLM_BASE_URL。"
            )

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        print(f"正在调用模型：{self.model}")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            # 处理流式响应
            print("✅ 大语言模型响应成功:")
            collected_content = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            print("\n")
            return "".join(collected_content)
        except Exception as e:
            print(f"调用模型时发生错误：{e}")
            return "抱歉，我无法生成回复。"


if __name__ == "__main__":
    agent = HelloAgentsLLM()
    messages = [
        {"role": "system", "content": "你是一个写python脚本的助手"},
        {"role": "user", "content": "请帮我写一个打印Hello, World!的Python脚本"},
    ]
    print("--- 调用LLM ---")
    response = agent.think(messages)
    print("\n\n--- 完整模型响应 ---")
    print(f"模型输出：{response}")
