from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain.retrievers.multi_query import MultiQueryRetriever


def create_rag_chain(retriever):
    """
    RAG chain compatible with LangChain >= 0.3.x.
    Uses multi-query retrieval + chat history + LCEL-style chain.
    """

    # LLM
    llm = ChatGroq(
        model_name="llama-3.1-8b-instant",
        temperature=0.7
    )

    # ✅ Step 1: Multi-query retriever (replaces history-aware retriever)
    mq_retriever = MultiQueryRetriever.from_llm(
        llm=llm,
        retriever=retriever
    )

    # ✅ Step 2: Final QA prompt
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an AI study assistant. Use ONLY the retrieved context below to answer. "
                "If the answer is not in the context, say you don't know.\n\n"
                "{context}"
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    # ✅ Step 3: LCEL RAG function
    def rag_chain(inputs):
        user_input = inputs["input"]
        chat_history = inputs["chat_history"]

        # Retrieve docs
        docs = mq_retriever.get_relevant_documents(user_input)
        context = "\n\n".join(d.page_content for d in docs)

        # Build prompt
        final_prompt = qa_prompt.format(
            context=context,
            chat_history=chat_history,
            input=user_input
        )

        # LLM answer
        response = llm.invoke(final_prompt)

        return {"answer": response.content}

    return rag_chain
