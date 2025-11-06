import os
import tempfile
import streamlit as st
from typing import List
from langchain_core.documents import Document

# ✅ Updated loaders for LC 0.3.x
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    WebBaseLoader
)

# ✅ New text splitters (old splitters deprecated)
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ✅ Shared text splitter (recommended LC way)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=150,
)


def load_docs(uploaded_files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> List[Document]:
    """Loads and splits various document types from uploaded files."""
    
    all_docs = []

    for uploaded_file in uploaded_files:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()

        # Write to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            # ✅ Select loader based on extension
            if file_extension == ".pdf":
                loader = PyPDFLoader(tmp_file_path)

            elif file_extension == ".docx":
                loader = Docx2txtLoader(tmp_file_path)

            elif file_extension == ".txt":
                loader = TextLoader(tmp_file_path)

            else:
                st.warning(f"Unsupported file type: {file_extension}. Skipping.")
                continue

            # ✅ Load raw documents (no split)
            raw_docs = loader.load()

            # ✅ Split using LC 0.3.x splitter
            docs = text_splitter.split_documents(raw_docs)

            all_docs.extend(docs)

        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")

        finally:
            os.remove(tmp_file_path)

    return all_docs



def load_article_docs(urls: List[str]) -> List[Document]:
    """Loads and splits content from a list of article URLs."""

    try:
        loader = WebBaseLoader(
            web_paths=urls,
            continue_on_failure=True, 
        )

        raw_docs = loader.load()

        # ✅ Apply text splitter
        docs = text_splitter.split_documents(raw_docs)

        return docs

    except Exception as e:
        st.error(f"An error occurred while loading articles: {e}")
        return []
