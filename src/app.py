import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

# Import your custom modules
from ingestion.document_loader import load_docs, load_article_docs
from vectorstore.chroma_store import get_vectorstore
from utils.auth import google_oauth_login
from utils.db import get_db_manager
from rag.chain import create_rag_chain

# --- Page Configuration ---
st.set_page_config(page_title="Student AI Notes", page_icon="📚", layout="wide")

# --- Main App Logic ---
st.title("📚 Student AI Notes")

# Attempt to log the user in
user_info = google_oauth_login()

# If the user is successfully logged in, show the main app
if user_info:
    user_id = user_info.get("email", "unknown_user")
    st.sidebar.success(f"Logged in as {user_info.get('name', user_id)}")

    # --- State Management & Initialization ---
    db_manager = get_db_manager()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "retriever" not in st.session_state:
        vectorstore = get_vectorstore()
        st.session_state.retriever = vectorstore.as_retriever(
            search_kwargs={'filter': {'user_id': user_id}}
        )
    if "rag_chain" not in st.session_state:
        st.session_state.rag_chain = create_rag_chain(st.session_state.retriever)

    # --- UI: Sidebar for Document Upload & Actions ---
    with st.sidebar:
        st.header("📥 Upload Your Study Materials")
        uploaded_files = st.file_uploader(
            "Upload Documents (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )
        article_url = st.text_input("Or enter an article URL")

        if st.button("Process Documents"):
            with st.spinner("Processing... This may take a moment."):
                all_docs = []
                if uploaded_files:
                    all_docs.extend(load_docs(uploaded_files))
                if article_url:
                    all_docs.extend(load_article_docs([article_url]))

                if all_docs:
                    vectorstore = get_vectorstore()
                    vectorstore.add_documents(documents=all_docs, user_id=user_id)
                    st.session_state.retriever = vectorstore.as_retriever(
                        search_kwargs={'filter': {'user_id': user_id}}
                    )
                    st.session_state.rag_chain = create_rag_chain(st.session_state.retriever)
                    st.success("✅ Documents processed successfully!")
                else:
                    st.warning("⚠️ No documents were provided.")
        
        # --- NEW: Feature Buttons ---
        st.header("✨ AI Tools")
        if st.button("Generate Summary"):
            st.session_state.run_task = "summary"
        if st.button("Create Practice Questions"):
            st.session_state.run_task = "questions"
        # ---------------------------

    # --- UI: Main Chat Interface ---
    st.header("💬 Chat With Your Documents")

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message.type):
            st.markdown(message.content)

    # Check for a task triggered by a button click
    task_prompt = None
    if st.session_state.get("run_task"):
        task = st.session_state.pop("run_task") # Use and remove the task
        if task == "summary":
            task_prompt = "Summarize the key points and main arguments from the provided documents."
        elif task == "questions":
            task_prompt = "Based on the provided documents, generate 5 important questions that could be on a test, along with their answers."
    
    # Handle new user input (from either text input or a button-triggered task)
    prompt = st.chat_input("Ask about your documents...") or task_prompt

    if prompt:
        st.session_state.messages.append(HumanMessage(content=prompt))
        with st.chat_message("human"):
            st.markdown(prompt)

        with st.chat_message("ai"):
            with st.spinner("Thinking..."):
                response = st.session_state.rag_chain.invoke({
                    "input": prompt,
                    "chat_history": st.session_state.messages[:-1]
                })
                answer = response.get("answer", "I could not find an answer.")
                st.markdown(answer)
        
        st.session_state.messages.append(AIMessage(content=answer))
        db_manager.save_chat(user_id, prompt, answer)
        st.rerun()

    # --- UI: Chat History Display ---
    with st.expander("🕘 View Your Recent Chat History"):
        history = db_manager.get_user_history(user_id, limit=10)
        if not history:
            st.caption("No history found.")
        else:
            for item in reversed(history):
                st.info(f"**Q:** {item['question']}\n\n**A:** {item['answer']}")
                st.caption(f"_{item['timestamp']}_")

# If the user is not logged in, show the login message
else:
    st.info("Please log in with Google to use the app.")