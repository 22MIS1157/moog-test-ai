"""
MoogTestAI — RAG Retriever Module

Provides a semantic search retriever that queries the ChromaDB vector store
for context relevant to a user's question or an agent's internal query.
"""

from langchain_chroma import Chroma

from src.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    RETRIEVER_TOP_K,
    get_embeddings,
)


def get_retriever(top_k: int = RETRIEVER_TOP_K):
    """
    Load the persisted ChromaDB vector store and return a LangChain retriever.

    Args:
        top_k: Number of top matching chunks to retrieve per query.

    Returns:
        A LangChain retriever instance.
    """
    embeddings = get_embeddings()
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
    )
    return vectorstore.as_retriever(search_kwargs={"k": top_k})


def retrieve_context(query: str, top_k: int = RETRIEVER_TOP_K) -> str:
    """
    Retrieve relevant document chunks for a given query and return them
    as a single formatted context string.

    Args:
        query: The search query (natural language).
        top_k: Number of results to retrieve.

    Returns:
        A formatted string containing the retrieved context chunks.
    """
    retriever = get_retriever(top_k=top_k)
    docs = retriever.invoke(query)

    if not docs:
        return "No relevant documents found in the knowledge base."

    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        doc_type = doc.metadata.get("type", "unknown")
        context_parts.append(
            f"--- Chunk {i} [Source: {source}, Type: {doc_type}] ---\n{doc.page_content}"
        )

    return "\n\n".join(context_parts)
