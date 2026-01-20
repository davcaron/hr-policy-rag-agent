import os
import pickle

import faiss

from sentence_transformers import SentenceTransformer

from hr_policy_rag_agent.src.chunking import run_chunking_pipeline


class FaissVectorStore:
    def __init__(
        self,
        document_chunks,
        embedding_model_name="all-MiniLM-L6-v2",
        persist_path="data/vectorstore/faiss",
    ):
        self.document_chunks = sorted(document_chunks, key=lambda c: c["id"])
        self.embedding_model_name = embedding_model_name
        self.persist_path = persist_path
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        self.index: faiss.Index | None = None

    def _embed(self, texts):
        return self.embedding_model.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True
        )

    def _validate(self) -> None:
        """
        Ensure FAISS index and document store are in sync.
        """
        if self.index.ntotal != len(self.document_chunks):
            raise RuntimeError("FAISS index and document store are out of sync!")

    def perform_embedding(self):
        texts = [chunk["content"] for chunk in self.document_chunks]
        self.embeddings = self._embed(texts=texts)

    def build_index(self):
        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(self.embeddings)

    def prepare_storage_dir(self):
        os.makedirs(self.persist_path, exist_ok=True)

    def persist_to_storage(self):
        # write index to storage
        faiss.write_index(self.index, f"{self.persist_path}/index.faiss")

        # write document chunks to storage
        with open(f"{self.persist_path}/documents.pkl", "wb") as f:
            pickle.dump(
                {
                    "embedding_model": self.embedding_model_name,
                    "documents": self.document_chunks,
                },
                f,
            )

    def load_index(self):
        self.index = faiss.read_index(os.path.join(self.persist_path, "index.faiss"))

    def load_document_chunks(self):
        with open(os.path.join(self.persist_path, "documents.pkl"), "rb") as f:
            data = pickle.load(f)
            if data["embedding_model"] != self.embedding_model_name:
                raise ValueError(
                    f"Embedding model mismatch: {data['embedding_model']}"
                    f"!= {self.embedding_model_name}"
                )

    def load_data(self):
        self.load_index()
        self.load_document_chunks()
        self._validate()

    def similarity_search(self, query, k):
        if self.index is None or not self.document_chunks:
            raise RuntimeError("Vector store is not loaded or built.")

        query_embedding = self._embed([query])
        _, indices = self.index.search(query_embedding, k)

        return [self.document_chunks[i] for i in indices[0] if i != -1]
