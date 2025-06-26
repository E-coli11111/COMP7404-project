def initial_prompt() -> str:
    return f"""
You are a backend software familiar with SQL. You will be given a request to perform a task.

Assume you know nothing about the database schema, but you have access to the database schema and can query it. You will need to use the schema to understand the structure of the data and how to perform the task.

Please complete the task step by step, breaking it down into smaller steps. Each step should be a complete SQL query that can be executed against the database. In each round, you should only generate one step.

Do you understand the task? If so, please respond with "Yes, I understand the task."
""".strip()

def problem_prompt(query) -> str:
    return f"""
Problem: {query} Let's think step by step.
""".strip()

def step_prompt(tables) -> str:
    return f"""
Now we execute the SQL query and get the result. The result is a table with the following columns: {'\n\n'.join(tables)}.
""".strip()