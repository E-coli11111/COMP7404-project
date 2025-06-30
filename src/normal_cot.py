# normal_cot.py
from agent import SQLAgent
from prompts import initial_prompt, problem_prompt, error_prompt
from openai import OpenAI
import re
import pandas as pd
import settings

client = OpenAI(api_key="your_api_key", base_url="your_base_url")
agent = SQLAgent(**settings.CONFIG["database"])

def extract_sql_queries(response):
    """提取SQL查询（同chatcot.py）"""
    return re.findall(r"```sql\n(.*?)\n```", response, re.DOTALL)

def normal_cot(query, model="qwen3-8b", max_attempts=5):
    """单次生成完整SQL，支持多次尝试（pass@k）"""
    history = [
        {"role": "system", "content": initial_prompt(agent.db_type, agent.db_name)},
        {"role": "user", "content": problem_prompt(query)}
    ]
    
    for _ in range(max_attempts):
        response = client.chat.completions.create(
            model=model,
            messages=history,
            temperature=0.7  # 增加随机性以支持pass@k
        ).choices[0].message.content
        
        sql_queries = extract_sql_queries(response)
        if not sql_queries:
            continue
        
        result = agent.execute_query(sql_queries[0])
        if isinstance(result, pd.DataFrame):
            return True  # success
    return False  # All attempts failed