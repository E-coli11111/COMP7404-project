# normal_cot.py
from agent import SQLAgent
from openai import OpenAI
import re
import pandas as pd
import settings


client = OpenAI(api_key=settings.API_KEY, base_url=settings.API_BASE, timeout=30.0)
agent = SQLAgent(**settings.CONFIG["database"])

def extract_sql_queries(response):
    """extract sql（same as chatcot.py）"""
    return re.findall(r"```sql\n(.*?)\n```", response, re.DOTALL)

def normal_cot(query, model="qwen3-8b", json_schema=None, enable_thinking=False):
    """single generation, supports multiple attempts（pass@k）"""
    
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
    #print("normal_cot API debug:", response)
    return response.choices[0].message.content

#print(normal_cot("List all products with their prices"))
