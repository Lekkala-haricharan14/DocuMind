import os
import streamlit as st
from typing import List
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# ✅ Updated Embedding import (Ollama embeddings still supported)
from langchain_community.embeddings import OllamaEmbeddings

load_dotenv()

PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "student_ai_notes"

# Embedding model used for Ollama (local)
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


class ChromaStore:
    """Wrapper class for Chroma vector database."""

    def __init__(self):
        """Initialize Chroma with embeddings."""
        self.embedding_function = OllamaEmbeddings(model=EMBED_MODEL)

        self.vectorstore = Chroma(
            persist_directory=PERSIST_DIR,
            collection_name=COLLECTION_NAME,
            embedding_function=self.embedding_function,
        )

    def add_documents(self, documents: List[Document], user_id: str):
        """Split and add documents to ChromaDB with user metadata."""
        if not documents:
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

        chunks = splitter.split_documents(documents)

        # ✅ Add user_id metadata
        for chunk in chunks:
            chunk.metadata = chunk.metadata or {}
            chunk.metadata["user_id"] = user_id

        # ✅ Add to Chroma
        self.vectorstore.add_documents(chunks)

        # ✅ Persist DB state
        self.vectorstore.persist()

    def as_retriever(self, search_kwargs: dict):
        """Return a retriever instance."""
        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)


@st.cache_resource
def get_vectorstore() -> ChromaStore:
    """Return a cached ChromaStore instance."""
    return ChromaStore()
