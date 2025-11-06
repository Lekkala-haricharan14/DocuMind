import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

# Import your custom modules
from ingestion.document_loader import load_docs, load_article_docs
from vectorstore.chroma_store import get_vectorstore
from utils.auth import google_oauth_login
from utils.db import get_db_manager
from rag.chain import create_rag_chain


# -------------------------------------------------------------
# ✅ Page Configuration
# -------------------------------------------------------------
st.set_page_config(
    page_title="Student AI Notes",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Student AI Notes")

# -------------------------------------------------------------
# ✅ Google Login
# -------------------------------------------------------------
user_info = google_oauth_login()

if user_info:

    user_id = user_info.get("email", "unknown_user")
    st.sidebar.success(f"Logged in as {user_info.get('name', user_id)}")

    # -------------------------------------------------------------
    # ✅ App State Initialization
    # -------------------------------------------------------------
    db_manager = get_db_manager()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "retriever" not in st.session_state:
        vectorstore = get_vectorstore()
        st.session_state.retriever = vectorstore.as_retriever(
            search_kwargs={"filter": {"user_id": user_id}}
        )

    if "rag_chain" not in st.session_state:
        st.session_state.rag_chain = create_rag_chain(
            st.session_state.retriever
        )

    # -------------------------------------------------------------
    # ✅ Sidebar: Upload Documents
    # -------------------------------------------------------------
    with st.sidebar:
        st.header("📥 Upload Your Study Materials")

        uploaded_files = st.file_uploader(
            "Upload Documents (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )

        article_url = st.text_input("Or enter an article URL")

        if st.button("Process Documents"):
            with st.spinner("Processing..."):
                all_docs = []

                if uploaded_files:
                    all_docs.extend(load_docs(uploaded_files))

                if article_url:
                    all_docs.extend(load_article_docs([article_url]))

                if all_docs:
                    vectorstore = get_vectorstore()
                    vectorstore.add_documents(all_docs, user_id=user_id)

                    # Update retriever
                    st.session_state.retriever = vectorstore.as_retriever(
                        search_kwargs={"filter": {"user_id": user_id}}
                    )

                    # Rebuild RAG chain
                    st.session_state.rag_chain = create_rag_chain(
                        st.session_state.retriever
                    )

                    st.success("✅ Documents processed successfully!")

                else:
                    st.warning("⚠️ No documents were provided.")

        # ---------------------------------------------------------
        # ✅ AI Tools
        # ---------------------------------------------------------
        st.header("✨ AI Tools")
        if st.button("Generate Summary"):
            st.session_state.run_task = "summary"
        if st.button("Create Practice Questions"):
            st.session_state.run_task = "questions"

    # -------------------------------------------------------------
    # ✅ Chat Interface
    # -------------------------------------------------------------
    st.header("💬 Chat With Your Documents")

    # Display previous chat messages
    for message in st.session_state.messages:
        role = "ai" if isinstance(message, AIMessage) else "human"
        with st.chat_message(role):
            st.markdown(message.content)

    # -------------------------------------------------------------
    # ✅ Handle task-based prompts
    # -------------------------------------------------------------
    task_prompt = None
    if st.session_state.get("run_task"):
        task = st.session_state.pop("run_task")

        if task == "summary":
            task_prompt = "Summarize the key points and important concepts from the uploaded documents."

        elif task == "questions":
            task_prompt = (
                "Generate 5 important exam-style questions from the uploaded documents, "
                "along with detailed answers."
            )

    # -------------------------------------------------------------
    # ✅ Chat input (manual or task)
    # -------------------------------------------------------------
    user_input = st.chat_input("Ask something...") or task_prompt

    if user_input:

        # Log human message
        st.session_state.messages.append(HumanMessage(content=user_input))

        with st.chat_message("human"):
            st.markdown(user_input)

        # ---------------------------------------------------------
        # ✅ RAG response (LangChain 0.3.x style)
        # ---------------------------------------------------------
        with st.chat_message("ai"):
            with st.spinner("Thinking..."):
                
                response = st.session_state.rag_chain({
                    "input": user_input,
                    "chat_history": st.session_state.messages[:-1]
                })

                answer = response.get("answer", "I couldn't find enough information to answer that.")                
                st.markdown(answer)

        # Log AI message
        st.session_state.messages.append(AIMessage(content=answer))

        # Save to DB
        db_manager.save_chat(user_id, user_input, answer)

        st.rerun()

    # -------------------------------------------------------------
    # ✅ Past Chat History
    # -------------------------------------------------------------
    with st.expander("🕘 View Your Recent Chat History"):
        history = db_manager.get_user_history(user_id, limit=10)
        if not history:
            st.caption("No chat history found.")
        else:
            for item in reversed(history):
                st.info(f"**Q:** {item['question']}\n\n**A:** {item['answer']}")
                st.caption(f"_{item['timestamp']}_")

else:
    st.info("Please log in with Google to use the app.")
