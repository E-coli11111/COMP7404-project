import yaml
import os

def load_config(path='config.yaml'):
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

CONFIG = load_config()

# LLM settings
LLM_NAME = "qwen3-8b"
API_BASE = os.getenv("API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
API_KEY = os.getenv("API_KEY")

EMB_NAME = "all-MiniLM-L6-v2"
EMB_DIM = 384

MAX_STEPS = 20

TYPE = CONFIG.get('type', 'sql').lower()
if TYPE not in ['sql', 'math']:
    raise ValueError(f"Invalid type: {TYPE}. Supported types are 'sql' and 'math'.")

RETRIEVER = CONFIG.get('retriever', {})