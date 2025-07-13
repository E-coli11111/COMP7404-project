import yaml
import os

def load_config(path='config.yaml'):
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

CONFIG = load_config()

# LLM settings
LLM_NAME = "qwen3-8b" # LLM model name, should be compatible with the API
API_BASE = os.getenv("API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1") # API base URL
API_KEY = os.getenv("API_KEY", "sk-394820080a1b42e28a040ebae4bc8f6f") # API key, can be set via environment variable

EMB_NAME = "all-MiniLM-L6-v2" # Embedding model name, default fetch from Hugging Face, used by the retriever
EMB_DIM = 384 # Embedding dimension, default is 384 for all-MiniLM-L6-v2

MAX_STEPS = 20 # Maximum steps for the LLM to generate a response

TYPE = CONFIG.get('type', 'sql').lower() # Type of task, can be 'sql' or 'math'
if TYPE not in ['sql', 'math']:
    raise ValueError(f"Invalid type: {TYPE}. Supported types are 'sql' and 'math'.")

RETRIEVER = CONFIG.get('retriever', {})

EVAL_DATASET = "data/eval/pa.json" # Path to the evaluation dataset, default is 'data/eval/pa.json'
EVAL_WORKER = 8 # Number of workers for evaluation, default is 8

# Web UI settings
IP = '127.0.0.1' # IP address for the web UI, default is localhost
PORT = 7860 # Port for the web UI, default is 7860