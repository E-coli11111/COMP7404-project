import re

def extract_sql_queries(response):
    """
    Extract SQL queries from the response content.
    """
    sql_queries = re.findall(r"```sql\n(.*?)\n```", response, re.DOTALL)
    return [query.strip() for query in sql_queries if query.strip()]

def extract_math_expressions(response):
    """
    Extract mathematical expressions from the response content.
    """
    math_expressions = re.findall(
        r"\{\s*\"variable\"\s*:\s*\".*?\"\s*,\s*\"equations\"\s*:\s*\[.*?\]\s*,\s*\"target\"\s*:\s*\".*?\"\s*\}",
        response, re.DOTALL
    )
    return [expr.strip() for expr in math_expressions if expr.strip()]

def extract_math_result(response):
    """
    Extract the final result from the response content.
    """
    # print("llm response", response)
    match = re.search(r"End\. Answer:\s*(.*)", response)
    if match:
        return match.group(1).strip()
    return None

# An advanced function to extract math result. You can choose one to do test. 
def extract_math_result(response):
    """增强版数学结果提取"""
    if not response or "Error" in response:
        return None
    
    # 情况1：尝试提取 LaTeX 数学表达式（如 \boxed{8}）
    latex_match = re.search(r'\\boxed\{([\d\.]+)\}', response)
    if latex_match:
        return latex_match.group(1)
    
    # 情况2：尝试提取行内计算结果（如 "= 8"）
    result_match = re.search(r'=\s*([\d\.]+)', response)
    if result_match:
        return result_match.group(1)
    
    # 情况3：尝试提取代码块中的纯数字
    code_block_match = re.search(r'```(?:math)?\n.*?([\d\.]+)\n```', response, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1)
    
    return None
