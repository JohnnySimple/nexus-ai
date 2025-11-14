import requests
import json
import time
from sklearn.metrics import precision_score, recall_score, f1_score
from sentence_transformers import SentenceTransformer, util
import numpy as np

BASE_URL = "http://localhost:8000/rag/query"   # Change this to your running FastAPI URL
QA_FILE = "orion_analytics_qa.json"        # Path to your Q&A file
TOP_K = 5
USE_LLM_RESPONSE = True

with open(QA_FILE, "r") as f:
    qa_data = json.load(f)

limit = len(qa_data)
qa_data = qa_data[:limit]
# print(qa_data)

# Initialize sentence transformer model for semantic similarity
model = SentenceTransformer("all-MiniLM-L6-v2")

results = []
precisions = []
recalls = []
f1s = []
cosine_scores = []

print(f"Testing {len(qa_data)} questions against {BASE_URL}...\n")

for i, item in enumerate(qa_data, 1):
    query = item["question"]
    ground_truth = item["answer"]

    params = {
        "query": query,
        "top_k": TOP_K,
        "with_llm_response": USE_LLM_RESPONSE,
        "document_ids": "3e8d960e-1316-4e5c-a40b-4440212ceeff"
    }

    try:
        start_time = time.time()
        response = requests.get(BASE_URL, params=params)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            if "llm_response" in data and data["llm_response"]:
                answer = data["llm_response"]
            elif "answer" in data:
                answer = data["answer"]
            else:
                answer = str(data)
        else:
            answer = f"ERROR: {response.status_code}"

        # Compute semantic similarity
        sim = util.cos_sim(
            model.encode(answer, convert_to_tensor=True),
            model.encode(ground_truth, convert_to_tensor=True)
        ).item()
        cosine_scores.append(sim)

        # Binary correctness for precision/recall/F1
        correct = 1 if sim > 0.8 else 0  # threshold can be tuned
        predicted = 1
        true_label = 1

        precisions.append(correct)
        recalls.append(correct)
        f1s.append(correct)

        results.append({
            "question": query,
            "expected": ground_truth,
            "answer": answer,
            "similarity": round(sim, 3),
            "latency_sec": round(elapsed, 2)
        })

        print(f"[{i}] Q: {query}")
        print(f"    -> Answer: {answer[:120]}")
        print(f"    -> Similarity: {sim:.3f} | Time: {elapsed:.2f}s\n")

    except Exception as e:
        print(f"[{i}] ERROR: {e}")
        continue


# ======= METRICS =======
precision = np.mean(precisions)
recall = np.mean(recalls)
f1 = np.mean(f1s)
avg_cosine = np.mean(cosine_scores)
avg_latency = np.mean([r["latency_sec"] for r in results])

print("\n====== Evaluation Summary ======")
print(f"Avg Precision: {precision:.3f}")
print(f"Avg Recall:    {recall:.3f}")
print(f"Avg F1-score:  {f1:.3f}")
print(f"Avg Semantic Similarity: {avg_cosine:.3f}")
print(f"Avg Latency per Query:   {avg_latency:.2f}s")

# Optional: save all detailed results
with open("rag_eval_results.json", "w") as f:
    json.dump(results, f, indent=4)

print("\nDetailed results saved to rag_eval_results.json")