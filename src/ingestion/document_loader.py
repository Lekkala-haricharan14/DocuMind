

import os
import tempfile
import streamlit as st
from typing import List
from langchain_core.documents import Document

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
    WebBaseLoader
)

def load_docs(uploaded_files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> List[Document]:
    """Loads various document types from a list of uploaded files."""
    all_docs = []
    
    for uploaded_file in uploaded_files:
        
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
           
            if file_extension == ".pdf":
                loader = PyPDFLoader(tmp_file_path)
            elif file_extension == ".docx":
                loader = UnstructuredWordDocumentLoader(tmp_file_path)
            elif file_extension == ".txt":
                loader = TextLoader(tmp_file_path)
            else:
                st.warning(f"Unsupported file type: {file_extension}. Skipping.")
                continue

           
            docs = loader.load_and_split()
            all_docs.extend(docs)

        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")
        finally:
          
            os.remove(tmp_file_path)
            
    return all_docs

def load_article_docs(urls: List[str]) -> List[Document]:
    """Loads content from a list of article URLs."""
    all_docs = []
    loader = WebBaseLoader(
        web_paths=urls,
        continue_on_failure=True, 
    )
    
    try:
        loaded_docs = loader.load()
        if loaded_docs:
            all_docs.extend(loaded_docs)
    except Exception as e:
        st.error(f"An error occurred while loading articles: {e}")
        return []

    return all_docs
