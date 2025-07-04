import os
import json
import re
import settings
import pandas as pd
from openai import OpenAI
from models import ChatBreakdownResult
from agent import SQLAgent, Calculator
from process import *

if settings.TYPE == "sql":
    from prompts.sql import *
    AGENT = SQLAgent(
        **settings.CONFIG["database"]
    )
    extract_func = extract_sql_queries
    
elif settings.TYPE == "math":
    from prompts.math import *
    AGENT = Calculator()
    extract_func = extract_math_expressions
     
else:    
    raise ValueError(f"Invalid type: {settings.TYPE}. Supported types are 'sql' and 'math'.")

CLIENT = OpenAI(
    api_key=settings.API_KEY,
    base_url=settings.API_BASE,
)

def chat(
    history, 
    model="qwen3-8b", 
    client=CLIENT, 
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

def chatcot(query):
        
    chat_history = [
        {"role": "system", "content": initial_prompt(AGENT)},
        {"role": "assistant", "content": "Yes, I understand the task."},
        {"role": "user", "content": problem_prompt(query)},
    ]
    
    if settings.RETRIEVER.get("enabled", False):
        from retriever import load_knowledge_base
        
        try:
            retriever = load_knowledge_base(
                "./data",
                load_index=False
            )
        except FileNotFoundError:
            print("Faiss index file not found. Please build the index first.")
            return "Error: Faiss index file not found."
        
        query_vector = retriever.emb.encode(query, convert_to_numpy=True)
        results = retriever.search(query_vector, top_k=5)
        
        if results:
            retrieved_texts = [result[0].text for result in results]
            chat_history.append({"role": "user", "content": retrieve_information_prompt(query, retrieved_texts)}) # TODO: modify prompt

    for step in range(settings.MAX_STEPS):
        # print(f"Step {step + 1}:")
        response = chat(chat_history, model=settings.LLM_NAME, enable_thinking=False)
        chat_history.append({"role": "assistant", "content": response})
        
        # print(f"Assistant: {response}")
        
        if "End" in response:
            break
        
        queries = extract_func(response)
        
        if not queries:
            chat_history.append({"role": "user", "content": empty_query_prompt()})
            continue
        elif len(queries) > 1:
            chat_history.append({"role": "user", "content": multiple_queries_prompt()})
            continue
        q = queries[0]
        

        result = AGENT.execute(q)
        if result.startswith("Error"):
            chat_history.append({"role": "user", "content": error_prompt(result)})
        else:
            chat_history.append({"role": "user", "content": step_prompt(result)})

        # print(chat_history[-1]["content"])
        
    with open("chat_history.json", "w", encoding="utf-8") as f:
        # print(len(chat_history))
        json.dump(chat_history[2:], f, ensure_ascii=False, indent=4)
        
    return chat_history[-1]["content"]


if __name__ == "__main__":
    # Example usage
    print(chatcot("What is one plus one?"))
    # print(chatcot("List all products with their prices"))
    # print(chatcot("Find the name and price of the cheapest product"))       