import pandas as pd

def initial_prompt(agent, *args, **kwargs) -> str:
    return f"""
You are a backend software familiar with SQL. You will be given a request to perform a task.

Assume you know nothing about the database schema, but you have access to the database schema and can query it. You will need to use the schema to understand the structure of the data and how to perform the task.

Please complete the task step by step, breaking it down into smaller steps. Each step should be a complete SQL query that can be executed against the database. 
In each round, you should only generate one step with one SQL code. Your code will be executed and you can refer to the result to think about the next step

We use {agent.db_type} server and we are inside {agent.db_name} database

Please pay attention to the following rules:
    1. You should not assume any dataset name or table schema
    2. The SQL query should be in the format of a code block, like this:
    ```sql
    SELECT * FROM table_name WHERE condition;
    ```
    3. You should use actual table names and column names in the SQL query, not placeholders. If you are not sure about the table names or column names, you can query the database schema to find out.
    4. If you think the task is complete, please respond with "End". Otherwise
    5. You are allow to use any read-only command, for example, "SELECT", "SHOW"

Do you understand the task? If so, please respond with "Yes, I understand the task."
""".strip()

def problem_prompt(query, *args, **kwargs) -> str:
    return f"""
Problem: {query} 
Let's think step by step. What we should do for the first step?.
""".strip()

def step_prompt(tables, *args, **kwargs) -> str:
    return f"""
Now we execute the SQL query and get the result. The result is a table with the following columns: 

{tables}

If this result useful? If so, what is the next step? If not, can you rework on it.
""".strip()

def error_prompt(msg, *args, **kwargs) -> str:
    return f"There's an error in your code with the following error message: {msg}. Can you rework on it"

def retrieve_information_prompt(query, results, **kwargs) -> str:
    retrieved_texts = '\n\n'.join(results)
    return f"""
Problem: {query} 
Below are some examples: {retrieved_texts}

Please use the above information to help you understand the problem better.
Now, let's think step by step. What we should do for the first step?
""".strip()

def empty_query_prompt(*args, **kwargs) -> str:
    return "No SQL queries found. Please provide a valid SQL query."

def multiple_queries_prompt(*args, **kwargs) -> str:
    return "Multiple SQL queries found. Please provide only one SQL query."