def initial_prompt(*args, **kwargs) -> str:
    return f"""
You will be given a request to solve a problem. Please think step by step and provide your answer in a clear and concise manner.

Please complete the task step by step, breaking it down into smaller steps. Each step you are allowed to write an equation that can be solved.

We use sympy to solve the equation, so you can use any function from sympy to help you solve the problem.

Please pay attention to the following rules:
    1. Please write the equation in the format of a json, like this:
    ```json
    {{
        "variable": "x y",
        "equations": ["x + y = 1", "x - y = 2"],
        "target": "x y"
    }}
    ```
    2. If you think the task is complete, please respond with "End. Answer: <your_answer>" without any other words, (<your answer> should one single number). Otherwise, you can continue to write more equations.

Do you understand the task? If so, please respond with "Yes, I understand the task."
""".strip()

def problem_prompt(query, *args, **kwargs) -> str:
    return f"""
Problem: {query}
Let's think step by step. What we should do for the first step?.
""".strip()

def step_prompt(equation, *args, **kwargs) -> str:
    return f"""
Now we execute the equation and get the result. The result is a solution to the equation.
{equation}
If this result useful? If so, what is the next step? If not, can you rework on it.
""".strip()

def error_prompt(msg, *args, **kwargs) -> str:
    return f"There's an error in your code with the following error message: {msg}. Can you rework on it"

def retrieve_information_prompt(query, results, *args, **kwargs) -> str:
    retrieved_texts = '\n\n'.join(results)
    return f"""
Problem: {query}
""".strip()

def empty_query_prompt(*args, **kwargs) -> str:
    return "No equations found. Please provide a valid equation."

def multiple_queries_prompt(*args, **kwargs) -> str:
    return "Multiple equations found. Please provide only one equation."