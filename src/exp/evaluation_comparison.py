import json
import settings
import threading
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from src.chatcot import chatcot
from src.process import extract_math_result, extract_normal_math_result
from normal_cot import normal_cot
import time
import matplotlib.pyplot as plt
import numpy as np

process = None

class EvaluationThread(threading.Thread):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.result = None

    def run(self):
        self.result = evaluate_model(self.path)

def evaluate_model(dataset):
    correct_count = 0
    total_attempted = 0
    
    for item in tqdm(dataset, desc="Evaluating"):
        try:
            if not isinstance(item, dict) or 'problem' not in item or 'real_answer' not in item:
                print(f"Skipping invalid item: {item}")
                continue
                
            llm_answer = extract_math_result(chatcot(item['problem']))
            if llm_answer is None:
                print(f"No answer extracted for problem: {item['problem']}")
                continue
                
            # standardized answer comparison
            def normalize_answer(ans):
                if isinstance(ans, str):
                    ans = ans.lower().strip()
                    # removed redundant units and symbols
                    ans = re.sub(r"[^\d.eE+-]", "", ans)
                return str(ans)
                
            item['llm_answer'] = llm_answer
            item['correct'] = (normalize_answer(item['real_answer']) == normalize_answer(llm_answer))
            
            if item['correct']:
                correct_count += 1
            total_attempted += 1
            
        except Exception as e:
            print(f"Error processing item {item.get('problem', 'unknown')}: {str(e)}")
            continue
            
    return {
        'correct_count': correct_count,
        'total_attempted': total_attempted,
        'accuracy': correct_count / total_attempted if total_attempted > 0 else 0
    } 

def main():
    
    eval_path = settings.EVAL_DATASET
    with open(eval_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)[101 :200] #test
    queries = [item["problem"] for item in dataset]
    reference_answers = [item["real_answer"] for item in dataset]
    
    # comparison using multiple threads
    def process_query(query_ref_pair):
        query, real_answer = query_ref_pair
        results = {}
        
        # evaluate chatcot
        chatcot_res = evaluate_pass_at_k(query, k=3, method="chatcot")
        chatcot_answer = extract_math_result(chatcot(query))
        
        # evaluate normal_cot
        normal_res = evaluate_pass_at_k(query, k=3, method="normal_cot")
        normal_answer = extract_normal_math_result(normal_cot(query))
        
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

    # using thread pool
    with ThreadPoolExecutor(max_workers=settings.EVAL_WORKER) as executor:
        futures = [executor.submit(process_query, (query, ref)) 
                 for query, ref in zip(queries, reference_answers)]
        
        results_compare = []
        for future in tqdm(as_completed(futures), total=len(queries)):
            results_compare.append(future.result())
    # summarize the results
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
    """compute pass@k"""
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

            # validation
            if method == "chatcot":
                extracted = extract_math_result(result)
            elif method == "normal_cot":
                extracted = extract_normal_math_result(result)
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
    
    # evaluate ChatCoT
    chatcot_correct = 0
    for query, real_answer in zip(queries, reference_answers):
        res = evaluate_pass_at_k(query, k, "chatcot")
        results["chatcot"]["pass@k"].append(res["pass@k"])
        results["chatcot"]["avg_time"].append(res["avg_time"])
        
        # accuracy evaluation
        llm_answer = extract_math_result(chatcot(query))
        if str(real_answer).strip() == str(llm_answer).strip():
            chatcot_correct += 1
    
    results["chatcot"]["accuracy"] = chatcot_correct / len(queries)
    
    # evaluate Normal CoT
    normal_correct = 0
    for query, real_answer in zip(queries, reference_answers):
        res = evaluate_pass_at_k(query, k, "normal_cot")
        results["normal_cot"]["pass@k"].append(res["pass@k"])
        results["normal_cot"]["avg_time"].append(res["avg_time"])
        
        llm_answer = extract_normal_math_result(normal_cot(query))
        if str(real_answer).strip() == str(llm_answer).strip():
            normal_correct += 1
    
    results["normal_cot"]["accuracy"] = normal_correct / len(queries)
    
    return results

def plot_comparison(results):

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
    
    # Pass@k comparison
    ax1.bar(labels, pass_at_k)
    ax1.set_title('Average Pass@k')
    ax1.set_ylim(0, 1)
    
    # accuracy comparison
    ax2.bar(labels, accuracies)
    ax2.set_title('Accuracy')
    ax2.set_ylim(0, 1)
    
    # time comparison
    ax3.bar(labels, avg_times)
    ax3.set_title('Average Time (s)')
    
    plt.tight_layout()
    plt.savefig('comparison_results.png')
    plt.show()
# a small test of normal-cot
def test_normal_cot():
    test_query = "calculate: 2 + 2 * 3"
    print("\n==normal_cot_test===")
    raw_response = normal_cot(test_query)
    print(f"raw_response: {raw_response}")
    extracted = extract_math_result(raw_response)
    print(f"extraction: {extracted}")
    print(f"whether get point: {extracted is not None and extracted != 'Error'}")

if __name__ == "__main__":
    main()
    #test_normal_cot()
