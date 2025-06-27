import yaml
import os

def load_config(path='config.yaml'):
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

CONFIG = load_config()

MODEL_NAME = "qwen3-8b"
API_BASE = os.getenv("API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
API_KEY = os.getenv("API_KEY")

MAX_STEPS = 20