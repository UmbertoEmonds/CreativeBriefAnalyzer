import uuid
import requests
from bs4 import BeautifulSoup
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_retriever(urls: list[str], query: str):
    # Scraping
    docs = []

    for url in urls:
        print(url)
        try:
            response = requests.get(url, timeout=5)
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator="\n", strip=True)

            if len(text) > 200:
                docs.append(Document(page_content=text, metadata={"source": url}))
        except Exception:
            continue

    if not docs:
        return "Aucun contenu récupéré."

    # Chunking
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    # Embeddings + Chroma
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    collection_name = f"brief_{uuid.uuid4().hex[:8]}"
    vectorstore = Chroma.from_documents(chunks, embeddings, collection_name=collection_name)

    # Research
    results = vectorstore.similarity_search(query, k=5)

    result = "\n\n".join([
        f"Source: {doc.metadata['source']}\n{doc.page_content}"
        for doc in results
    ])

    return result