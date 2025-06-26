import os
import re
import settings
import pandas as pd
from openai import OpenAI
from prompts import *
from models import ChatBreakdownResult
from agent import SQLAgent

CLIIENT = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
)

AGENT = SQLAgent(
    **settings.CONFIG["database"]
)

def chat(
    history, 
    model="qwen3-8b", 
    client=CLIIENT, 
    json_schema=None, 
    enable_thinking=False, 
    **kwargs
):
    response = client.chat.completions.create(
        model=model,
        messages=history,
        response_format={"type": "json_object"} if json_schema else None,
        extra_body={"enable_thinking": enable_thinking},
        **kwargs
    )
    
    if json_schema:
        json_schema.model_validate_json(response.choices[0].message.content)

    return response.choices[0].message.content

def extract_sql_queries(response):
    """
    Extract SQL queries from the response content.
    """
    sql_queries = re.findall(r"```sql\n(.*?)\n```", response, re.DOTALL)
    return [query.strip() for query in sql_queries if query.strip()]

def chatcot(query):
    chat_history = [
        {"role": "system", "content": initial_prompt()},
        {"role": "assistant", "content": "Yes, I understand the task."},
        {"role": "user", "content": problem_prompt(query)},
    ]
    
    while True:
        response = chat(chat_history, model="qwen3-8b", enable_thinking=True)
        chat_history.append({"role": "assistant", "content": response})
        
        if "Let's think step by step" in response:
            continue
        
        if "End" in response:
            break
        
        chat_history.append({"role": "user", "content": response})
        
        sql_queries = extract_sql_queries(response)
        tables = []
        if sql_queries:
            for sql in sql_queries:
                result = AGENT.execute(sql)
                
                if isinstance(result, pd.DataFrame):
                    tables.append(result.to_markdown(index=False))
                    
                else:
                    tables.append("No SQL queries found in the response.")

        chat_history.append({"role": "user", "content": step_prompt(tables)})
        
    return 

print(chatcot("Find the total sales for product X in the last month."))