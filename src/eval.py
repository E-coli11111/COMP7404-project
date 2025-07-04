import json
import settings
import threading

from tqdm import tqdm
from chatcot import chatcot
from process import extract_math_result

process = None

class EvaluationThread(threading.Thread):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.result = None

    def run(self):
        self.result = evaluate_model(self.path)
        print(f"\nThread {self.name} finished processing {len(self.path)} items.")

def evaluate_model(dataset):
    """
    Evaluate the model on the given dataset.
    
    Args:
        model: The model to evaluate.
        dataset: The dataset to evaluate the model on.
    
    Returns:
        A dictionary containing evaluation metrics.
    """
        
    for item in dataset:
        real_answer = item['real_answer']
        llm_answer = extract_math_result(chatcot(item['problem']))
        del item['retrieval_result']
        del item['chat_and_reason']
        item['llm_answer'] = llm_answer
        item['score'] = (real_answer.strip("$").replace(" ", "") == llm_answer.strip("$").replace(" ", "") if llm_answer is not None else False)
        
        process.update(1)
        # print(f"Problem: {item['problem']}")
        # print(f"Real Answer: {real_answer}")
        # print(f"LLM Answer: {llm_answer}")
    
    with open('evaluation_results.json', 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)
        
    
def main():
    eval_path = settings.EVAL_DATASET
    with open(eval_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)[:200]
    
    global process
    workers = []
    process = tqdm(total=len(dataset), desc="Evaluating", unit="item")
    for i in range(settings.EVAL_WORKER):
        # Split the dataset into equal parts for each worker
        chunk_size = len(dataset) // settings.EVAL_WORKER
        start = i * chunk_size
        # Ensure the last chunk gets any remaining items
        end = (i + 1) * chunk_size if i < settings.EVAL_WORKER - 1 else len(dataset)
        data_chunk = dataset[start:end]
        
        thread = EvaluationThread(data_chunk)
        thread.start()
        workers.append(thread)

    for thread in workers:
        thread.join()
    
    process.close()
    results = {
        'correct_count': sum(1 for item in dataset if item['score']),
        'total_count': len(dataset),
        'accuracy': sum(1 for item in dataset if item['score']) / len(dataset)
    }
    
    print(f"Correct Count: {results['correct_count']}")
    print(f"Total Count: {results['total_count']}")
    print(f"Accuracy: {results['accuracy']:.2%}")
    
    with open('evaluation_results.json', 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)
    
if __name__ == "__main__":
    main()