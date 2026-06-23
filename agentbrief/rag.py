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


_SOCIAL_DOMAINS = [
    "youtube.com", "youtu.be",
    "facebook.com", "instagram.com", "tiktok.com",
    "twitter.com", "x.com",
    "linkedin.com",
    "reddit.com",
    "pinterest.com",
    "twitch.tv",
]

def _is_social_media(url: str) -> bool:
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    domain = domain.removeprefix("www.")
    return any(d in domain for d in _SOCIAL_DOMAINS)

def build_retriever(urls: list[str], query: str):
    docs = []

    urls = [u for u in urls if not _is_social_media(u)]
    print(f"   Scraping de {len(urls)} page(s)...")
    for url in urls:
        print(f"      {url}")
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
        return "Aucun contenu recupere."

    print(f"   Decoupage en chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(docs)

    print(f"   Embeddings via HuggingFace (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    collection_name = f"brief_{uuid.uuid4().hex[:8]}"
    vectorstore = Chroma.from_documents(chunks, embeddings, collection_name=collection_name)

    print(f"   Recherche de similarite (top {SIMILARITY_TOP_K})...")
    results = vectorstore.similarity_search(query, k=SIMILARITY_TOP_K)

    result = "\n\n".join([
        f"Source: {doc.metadata['source']}\n{doc.page_content}"
        for doc in results
    ])

    return result
