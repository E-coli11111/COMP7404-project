import numpy as np
import faiss
import sentence_transformers
import json
import os

import src.settings as settings
from models import FaissTextModel

class FaissVectorSearcher:
    def __init__(self, dimension, emb_name='all-MiniLM-L6-v2'):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.data = []
        self.next_id = 0
        self.emb = sentence_transformers.SentenceTransformer(emb_name)
        
    def add_texts(self, texts):
        vectors = self.emb.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        
        vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        
        self.index.add(vectors)
        
        # Convert texts to FaissTextModel and store IDs
        for text in texts:
            text_model = FaissTextModel(id=self.next_id, text=text)
            self.data.append(text_model)
            self.next_id += 1
            
    def search(self, query_vector, top_k=5):
        if self.index.ntotal == 0:
            raise RuntimeError("Empty index. Please add vectors before searching.")
        
        if isinstance(query_vector, list):
            query_vector = np.array(query_vector, dtype=np.float32)
        query_vector = np.ascontiguousarray(query_vector, dtype=np.float32).reshape(1, -1)
        
        distances, indices = self.index.search(query_vector, top_k)
        
        results = []
        for i in range(top_k):
            idx = indices[0, i]
            if idx >= 0:  
                distance = float(distances[0, i])
                results.append((self.data[idx], distance))
        
        return results
    
    def save_index(self, file_path):
        faiss.write_index(self.index, file_path)
        np.save(file_path + ".ids.npy", np.array(self.data, dtype=object))
    
    def load_index(self, file_path):
        self.index = faiss.read_index(file_path)
        self.data = list(np.load(file_path + ".ids.npy"))
        self.next_id = max(self.data) + 1 if self.data else 0

    
def load_knowledge_base(data_path, load_index=True):
    if load_index:
        retriever = FaissVectorSearcher(settings.EMB_DIM, settings.EMB_NAME)
        try:
            retriever.load_index("faiss_index.faiss")
            return retriever
        except FileNotFoundError:
            print("Faiss index file not found. Please build the index first.")
        
    data = []
    for json_file in os.listdir(data_path):
        if json_file.endswith('.json'):
            file_path = os.path.join(data_path, json_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                text = "\n".join([item['content'] for item in data if 'content' in item])
                
    retriever = FaissVectorSearcher(settings.EMB_DIM, settings.EMB_NAME)
    
    retriever.add_texts([text])
    
    retriever.save_index("faiss_index.faiss")
    
    return retriever
    
if __name__ == "__main__":
    data_path = "data"
    load_knowledge_base(data_path, load_index=True)
    print("Knowledge base loaded and index created.")
    
    # Example usage
    retriever = FaissVectorSearcher(settings.EMB_DIM, settings.EMB_NAME)
    retriever.load_index("faiss_index.faiss")
    
    query = "What is the total number of products?"
    query_vector = retriever.emb.encode(query, convert_to_numpy=True)
    results = retriever.search(query_vector, top_k=5)
    
    for result in results:
        print(f"ID: {result[0]}, Distance: {result[1]}")