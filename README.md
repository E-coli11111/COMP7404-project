# COMP7404-project

## Environment Setup

This project requires Python 3.11 or higher. It is recommended to use a virtual environment to manage dependencies.

To set up the environment, follow these steps:

```
pip install -r requirements.txt
```

## Generation Pipeline

User input natural language input will be processed using the following steps:

1. Tool introduction and problem setting: Introduce what tools can be used and the propose of the task
2. Retrieve the relevant problem: few-shot prompting
3. Iterative reasoning:
   1. CoT Generation
   2. SQL Generation
   3. SQL Execution
   4. Result Display
   5. Next iteration
  
Here is an example:
