# src/vectorstore/chroma_store.py

import os
import streamlit as st
from typing import List
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

# --- Configuration for this file ---
load_dotenv() # <-- Add this to load .env variables
PERSIST_DIR = "./chroma_db"
# Load the embedding model name from the .env file
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text") # <-- Changed this line
COLLECTION_NAME = "student_ai_notes"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

class ChromaStore:
    """A wrapper class for ChromaDB to manage vector storage and retrieval."""

    def __init__(self):
        """Initializes the ChromaStore."""
        self.embedding_function = OllamaEmbeddings(model=EMBED_MODEL)
        self.vectorstore = Chroma(
            persist_directory=PERSIST_DIR,
            collection_name=COLLECTION_NAME,
            embedding_function=self.embedding_function,
        )

    def add_documents(self, documents: List[Document], user_id: str):
        """Splits documents and adds them to the vectorstore."""
        if not documents:
            return

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)

        for chunk in chunks:
            if chunk.metadata is None:
                chunk.metadata = {}
            chunk.metadata['user_id'] = user_id
        
        self.vectorstore.add_documents(chunks)
        self.vectorstore.persist()

    def as_retriever(self, search_kwargs: dict):
        """Returns the vectorstore configured as a retriever."""
        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)

@st.cache_resource
def get_vectorstore() -> ChromaStore:
    """Returns a singleton instance of the ChromaStore."""
    return ChromaStore()