import os
import re
import settings
import pandas as pd
from openai import OpenAI
from prompts import *
from models import ChatBreakdownResult
from agent import SQLAgent

CLIIENT = OpenAI(
    api_key=settings.API_KEY,
    base_url=settings.API_BASE,
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

def chatcot(query, with_retriever=False):
    chat_history = [
        {"role": "system", "content": initial_prompt(AGENT.db_type, AGENT.db_name)},
        {"role": "assistant", "content": "Yes, I understand the task."},
        {"role": "user", "content": problem_prompt(query)},
    ]
    
    if with_retriever:
        from retriever import FaissVectorSearcher
        retriever = FaissVectorSearcher(
            dimension=settings.EMB_DIM, 
            emb_name=settings.EMB_NAME
        )
        
        try:
            retriever.load_index("faiss_index.faiss")
        except FileNotFoundError:
            print("Faiss index file not found. Please build the index first.")
            return "Error: Faiss index file not found."
        
        query_vector = retriever.emb.encode(query, convert_to_numpy=True)
        results = retriever.search(query_vector, top_k=5)
        
        if results:
            retrieved_texts = [retriever.get_vector(result[0]).text for result in results]
            chat_history.append({"role": "user", "content": retrieve_information_prompt(query, retrieved_texts)}) # TODO: modify prompt

    for step in range(settings.MAX_STEPS):
        print(f"Step {step + 1}:")
        response = chat(chat_history, model=settings.LLM_NAME, enable_thinking=False)
        chat_history.append({"role": "assistant", "content": response})
        
        print(f"Assistant: {response}")
        
        if "End" in response:
            return "Task completed."
        
        chat_history.append({"role": "user", "content": response})
        
        sql_queries = extract_sql_queries(response)
        
        if not sql_queries:
            chat_history.append({"role": "user", "content": "No SQL queries found. Please provide a valid SQL query."})
            continue
        elif len(sql_queries) > 1:
            chat_history.append({"role": "user", "content": "Multiple SQL queries found. Please provide only one SQL query."})
            continue
        sql_query = sql_queries[0]
        

        result = AGENT.execute_query(sql_query)
        if isinstance(result, pd.DataFrame):
            chat_history.append({"role": "user", "content": step_prompt([result.to_markdown()])})
        else:
            chat_history.append({"role": "user", "content": error_prompt(result)})

        print(chat_history[-1]["content"])


if __name__ == "__main__":
    # Example usage
    print(chatcot("What is the total number of products?"))
    print(chatcot("List all products with their prices"))
    print(chatcot("Find the name and price of the cheapest product"))       