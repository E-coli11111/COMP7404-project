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

# Four functions for compare chatcot and normal_cot  July 4th
def main():
    
    eval_path = settings.EVAL_DATASET
    with open(eval_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)[:200] #test
  
    queries = [item["problem"] for item in dataset]
    reference_answers = [item["real_answer"] for item in dataset]
    
    # 多线程比较方法
    def process_query(query_ref_pair):
        query, real_answer = query_ref_pair
        results = {}
        
        # 评估chatcot
        chatcot_res = evaluate_pass_at_k(query, k=3, method="chatcot")
        chatcot_answer = extract_math_result(chatcot(query))
        
        # 评估normal_cot
        normal_res = evaluate_pass_at_k(query, k=3, method="normal_cot")
        normal_answer = extract_math_result(normal_cot(query))
        
        return {
            "query": query,
            "chatcot": {
                **chatcot_res,
                "correct": str(real_answer).strip() == str(chatcot_answer).strip()
            },
            "normal_cot": {
                **normal_res,
                "correct": str(real_answer).strip() == str(normal_answer).strip()
            }
        }

    # 使用线程池
    with ThreadPoolExecutor(max_workers=settings.EVAL_WORKER) as executor:
        futures = [executor.submit(process_query, (query, ref)) 
                 for query, ref in zip(queries, reference_answers)]
        
        results_compare = []
        for future in tqdm(as_completed(futures), total=len(queries)):
            results_compare.append(future.result())

    # 汇总结果
    final_results = {
        "chatcot": {
            "pass@k": np.mean([x["chatcot"]["pass@k"] for x in results_compare]),
            "accuracy": np.mean([x["chatcot"]["correct"] for x in results_compare]),
            "avg_time": np.mean([x["chatcot"]["avg_time"] for x in results_compare])
        },
        "normal_cot": {
            "pass@k": np.mean([x["normal_cot"]["pass@k"] for x in results_compare]),
            "accuracy": np.mean([x["normal_cot"]["correct"] for x in results_compare]),
            "avg_time": np.mean([x["normal_cot"]["avg_time"] for x in results_compare])
        },
        "details": results_compare
    }

    print("\n===== Final Results =====")
    print(json.dumps(final_results, indent=2, ensure_ascii=False))

    with open("evaluation_results_compare.json", "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    plot_comparison(final_results)

def evaluate_pass_at_k(query, k=3, method="chatcot"):
    """计算pass@k"""
    successes = 0
    total_time = 0
    
    for _ in range(k):
        start_time = time.time()
        try:
            if method == "chatcot":
                result = chatcot(query)
            elif method == "normal_cot":
                result = normal_cot(query)
                #print(f"\n[DEBUG] Normal cot original response: {result}")
                
            elapsed = time.time() - start_time
            total_time += elapsed

            # 更健壮的验证逻辑
            extracted = extract_math_result(result)
            #if method == "normal_cot":
                #print(f"[DEBUG] extracted_result: {extracted}")
            if extracted is not None:
                successes += 1
                
        except Exception as e:
            print(f"Error in evaluation: {str(e)}")
            continue
    #print(f"[DEBUG] normal_cot pass@k: {successes / k}")
    return {
        "pass@k": successes / k if k > 0 else 0,
        "avg_time": total_time / k if k > 0 else 0
    }

def compare_methods(queries, reference_answers, k=3):
    results = {
        "chatcot": {"pass@k": [], "avg_time": [], "accuracy": 0},
        "normal_cot": {"pass@k": [], "avg_time": [], "accuracy": 0}
    }
    
    # 评估ChatCoT
    chatcot_correct = 0
    for query, real_answer in zip(queries, reference_answers):
        res = evaluate_pass_at_k(query, k, "chatcot")
        results["chatcot"]["pass@k"].append(res["pass@k"])
        results["chatcot"]["avg_time"].append(res["avg_time"])
        
        # 准确性评估
        llm_answer = extract_math_result(chatcot(query))
        if str(real_answer).strip() == str(llm_answer).strip():
            chatcot_correct += 1
    
    results["chatcot"]["accuracy"] = chatcot_correct / len(queries)
    
    # 评估Normal CoT
    normal_correct = 0
    for query, real_answer in zip(queries, reference_answers):
        res = evaluate_pass_at_k(query, k, "normal_cot")
        results["normal_cot"]["pass@k"].append(res["pass@k"])
        results["normal_cot"]["avg_time"].append(res["avg_time"])
        
        llm_answer = extract_math_result(normal_cot(query))
        if str(real_answer).strip() == str(llm_answer).strip():
            normal_correct += 1
    
    results["normal_cot"]["accuracy"] = normal_correct / len(queries)
    
    return results
    
def plot_comparison(results):
    import matplotlib.pyplot as plt
    import numpy as np
    
    labels = ['ChatCoT', 'Normal CoT']
    pass_at_k = [
        np.mean(results["chatcot"]["pass@k"]),
        np.mean(results["normal_cot"]["pass@k"])
    ]
    accuracies = [
        results["chatcot"]["accuracy"],
        results["normal_cot"]["accuracy"]
    ]
    avg_times = [
        np.mean(results["chatcot"]["avg_time"]),
        np.mean(results["normal_cot"]["avg_time"])
    ]
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
    # Pass@k 对比
    ax1.bar(labels, pass_at_k)
    ax1.set_title('Average Pass@k')
    ax1.set_ylim(0, 1)
    
    # 准确率对比
    ax2.bar(labels, accuracies)
    ax2.set_title('Accuracy')
    ax2.set_ylim(0, 1)
    
    # 时间对比
    ax3.bar(labels, avg_times)
    ax3.set_title('Average Time (s)')
    
    plt.tight_layout()
    plt.savefig('comparison_results.png')
    plt.show()


if __name__ == "__main__":
    main()
