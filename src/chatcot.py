import os
import json
import re
import pandas as pd
import src.settings as settings
from openai import OpenAI
from src.models import ChatBreakdownResult
from src.agent import SQLAgent, Calculator
from src.process import *

if settings.TYPE == "sql":
    from .prompts.sql import *
    AGENT = SQLAgent(
        **settings.CONFIG["database"]
    )
    extract_func = extract_sql_queries
    
elif settings.TYPE == "math":
    from .prompts.math import *
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
    stream=False,
    **kwargs
):
    response = client.chat.completions.create(
        model=model,
        messages=history,
        response_format={"type": "json_object"} if json_schema else None,
        extra_body={"enable_thinking": enable_thinking},
        stream=stream,
        **kwargs
    )
    
    if stream:
        return response
    
    if json_schema:
        json_schema.model_validate_json(response.choices[0].message.content)

    return response.choices[0].message.content

def chatcot(query, stream=False):
    chat_history = [
        {"role": "system", "content": initial_prompt(AGENT)},
        {"role": "assistant", "content": "Yes, I understand the task."},
        {"role": "user", "content": problem_prompt(query)},
    ]

    last_response = ""
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
            chat_history.append(
                {"role": "user", "content": retrieve_information_prompt(query, retrieved_texts)})  # TODO: modify prompt

    for step in range(settings.MAX_STEPS):

        response = chat(
            history=chat_history,
            model=settings.LLM_NAME,
            client=CLIENT,
            stream=stream
        )

        # process stream content
        if stream:
            response_content = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    response_content += content

                    yield {
                        "type": "reasoning",
                        "content": content,
                        "step": step + 1
                    }
        else:
            response_content = response
            yield {
                "type": "reasoning",
                "content": response_content,
                "step": step + 1
            }

        chat_history.append({"role": "assistant", "content": response_content})
        last_response = response_content

        # check end condition
        if "End" in response_content:
            yield {
                "type": "final",
                "content": "Reasoning completed",
                "step": step + 1
            }
            break

        queries = extract_func(response_content)

        if not queries:
            error_msg = empty_query_prompt()
            chat_history.append({"role": "user", "content": error_msg})
            yield {
                "type": "error",
                "content": f"{error_msg}",
                "step": step + 1
            }
            continue
        elif len(queries) > 1:
            error_msg = multiple_queries_prompt()
            chat_history.append({"role": "user", "content": error_msg})
            yield {
                "type": "error",
                "content": f"{error_msg}",
                "step": step + 1
            }
            continue

        # execute the query
        try:
            q = queries[0]
            yield {
                "type": "action",
                "content": f"Executing: {q}",
                "step": step + 1
            }
            result = AGENT.execute(q)

            result_prompt = step_prompt(result) if not result.startswith("Error") else error_prompt(result)
            chat_history.append({"role": "user", "content": result_prompt})

            yield {
                "type": "result",
                "content": f"Result: {result}",
                "step": step + 1
            }

        except Exception as e:
            yield {
                "type": "error",
                "content": f"Execution error: {str(e)}",
                "step": step + 1
            }

    yield {
        "type": "final",
        "content": last_response
    }

    with open("chat_history.json", "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=4)
        
 