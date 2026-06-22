"""
RAG retrieval module for the ChatBotLangGraph application.

Scrapes content from URLs, chunks it, embeds it with HuggingFace
all-MiniLM-L6-v2, and performs similarity search via Chroma.
"""
import uuid
import requests
from bs4 import BeautifulSoup
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from agentbrief.config import SCRAPE_TIMEOUT, MIN_TEXT_LENGTH, CHUNK_SIZE, CHUNK_OVERLAP, SIMILARITY_TOP_K


def build_retriever(urls: list[str], query: str):
    """
    Scrape content from a list of URLs, chunk and embed it, then return
    the top-k similarity search results for the given query.

    Uses BeautifulSoup for scraping, RecursiveCharacterTextSplitter for
    chunking, HuggingFace embeddings with all-MiniLM-L6-v2, and Chroma
    as the vector store.

    Args:
        urls: List of URLs to scrape and index.
        query: The search query to retrieve relevant passages.

    Returns:
        str: Concatenated passages with source attribution, or a fallback
             message if no content could be retrieved.
    """
    docs = []

    for url in urls:
        print(url)
        try:
            response = requests.get(url, timeout=SCRAPE_TIMEOUT)
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator="\n", strip=True)

            if len(text) > MIN_TEXT_LENGTH:
                docs.append(Document(page_content=text, metadata={"source": url}))
        except Exception:
            continue

    if not docs:
        return "Aucun contenu récupéré."

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    collection_name = f"brief_{uuid.uuid4().hex[:8]}"
    vectorstore = Chroma.from_documents(chunks, embeddings, collection_name=collection_name)

    results = vectorstore.similarity_search(query, k=SIMILARITY_TOP_K)

    result = "\n\n".join([
        f"Source: {doc.metadata['source']}\n{doc.page_content}"
        for doc in results
    ])

    return result