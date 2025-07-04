# normal_cot.py
from agent import SQLAgent
from prompts.math import initial_prompt, problem_prompt, error_prompt
from openai import OpenAI
import re
import pandas as pd
import settings
from dashscope import Generation
import dashscope

client = OpenAI(api_key=settings.API_KEY, base_url=settings.API_BASE, timeout=30.0)
#dashscope.api_key = settings.API_KEY
agent = SQLAgent(**settings.CONFIG["database"])

def extract_sql_queries(response):
    """提取SQL查询（同chatcot.py）"""
    return re.findall(r"```sql\n(.*?)\n```", response, re.DOTALL)

def normal_cot(query, model="qwen3-8b", json_schema=None, enable_thinking=False):
    """单次生成完整SQL，支持多次尝试（pass@k）"""
    messages = [
        {"role": "system", "content": "Solve math problems step by step. "},
        {"role": "user", "content": f"Problem: {query}\nLet's think step by step. "}
    ]
    response = client.chat.completions.create(
        model = model,
        messages = messages, 
        response_format={"type": "json_object"} if json_schema else None,
        extra_body={"enable_thinking": enable_thinking},
        temperature = 0.7
    )
    print("normal_cot API debug:", response)
    return response.choices[0].message.content

#print(normal_cot("List all products with their prices"))
