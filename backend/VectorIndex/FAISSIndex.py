import os
import json
import numpy as np
import faiss


class FAISSIndex:
    """
    Singleton wrapper for FAISS vector similarity index.
    Uses IndexFlatIP (Inner Product) since embeddings are L2-normalized,
    making Inner Product equivalent to Cosine Similarity.
    """
    _instance = None
    _index = None
    _id_mapping: list[int] = []
    _dim: int = 0
    _is_built: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def build(self, embeddings: np.ndarray, db_ids: list[int]):
        """
        Build FAISS index from embeddings array and corresponding database IDs.

        Args:
            embeddings: numpy array of shape (N, D) with L2-normalized vectors
            db_ids: list of database record IDs corresponding to each embedding
        """
        if len(embeddings) == 0:
            raise ValueError("Cannot build index from empty embeddings")

        self._dim = embeddings.shape[1]
        self._id_mapping = list(db_ids)

        self._index = faiss.IndexFlatIP(self._dim)
        self._index.add(embeddings.astype(np.float32))
        self._is_built = True

        print(f"[INFO ] FAISS index built: {len(db_ids)} vectors, dim={self._dim}")

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[tuple[int, float]]:
        """
        Search for k most similar vectors.

        Args:
            query_embedding: numpy array of shape (D,) or (1, D), L2-normalized
            k: number of results to return

        Returns:
            List of (db_id, similarity_score) tuples, sorted by similarity descending.
            Similarity score is cosine similarity (0 to 1 for normalized vectors).
        """
        if not self._is_built or self._index is None:
            raise RuntimeError("FAISS index is not built. Call build() first.")

        query = query_embedding.astype(np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)

        k_actual = min(k, len(self._id_mapping))
        distances, indices = self._index.search(query, k_actual)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            db_id = self._id_mapping[idx]
            results.append((db_id, float(dist)))

        return results

    def add_embedding(self, embedding: np.ndarray, db_id: int):
        """
        Add a single embedding to the existing index.

        Args:
            embedding: numpy array of shape (D,), L2-normalized
            db_id: database record ID for this embedding
        """
        if not self._is_built or self._index is None:
            raise RuntimeError("FAISS index is not built. Call build() first.")

        emb = embedding.astype(np.float32).reshape(1, -1)
        self._index.add(emb)
        self._id_mapping.append(db_id)

    def size(self) -> int:
        """Return number of vectors in the index."""
        return self._index.ntotal if self._index else 0

    def is_built(self) -> bool:
        return self._is_built

    def save(self, directory: str):
        """
        Save FAISS index and ID mapping to disk.

        Args:
            directory: path to save index files
        """
        if not self._is_built or self._index is None:
            raise RuntimeError("FAISS index is not built. Nothing to save.")

        os.makedirs(directory, exist_ok=True)

        index_path = os.path.join(directory, "faiss_index.bin")
        mapping_path = os.path.join(directory, "id_mapping.json")

        faiss.write_index(self._index, index_path)

        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump({
                "id_mapping": self._id_mapping,
                "dim": self._dim
            }, f, indent=2)

        print(f"[INFO ] FAISS index saved to {directory} ({self.size()} vectors)")

    def load(self, directory: str):
        """
        Load FAISS index and ID mapping from disk.

        Args:
            directory: path containing index files
        """
        index_path = os.path.join(directory, "faiss_index.bin")
        mapping_path = os.path.join(directory, "id_mapping.json")

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index file not found: {index_path}")
        if not os.path.exists(mapping_path):
            raise FileNotFoundError(f"ID mapping file not found: {mapping_path}")

        self._index = faiss.read_index(index_path)
        self._dim = self._index.d

        with open(mapping_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._id_mapping = data["id_mapping"]

        self._is_built = True
        print(f"[INFO ] FAISS index loaded from {directory} ({self.size()} vectors, dim={self._dim})")
