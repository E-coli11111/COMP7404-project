import numpy as np
import faiss
import sentence_transformers

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
                vector_id = self.ids[idx]
                distance = float(distances[0, i])
                results.append((vector_id, distance))
        
        return results
    
    def save_index(self, file_path):
        faiss.write_index(self.index, file_path)
        np.save(file_path + ".ids.npy", np.array(self.ids))
    
    def load_index(self, file_path):
        self.index = faiss.read_index(file_path)
        self.ids = list(np.load(file_path + ".ids.npy"))
        self.next_id = max(self.ids) + 1 if self.ids else 0

    def get_vector(self, vector_id):
        if vector_id not in self.ids:
            raise ValueError(f"ID {vector_id} not found in the index.")
        
        idx = self.ids.index(vector_id)
        return self.index.reconstruct(idx)

    