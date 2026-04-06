import os
from datetime import datetime


def _get_client():
    import chromadb

    host = os.getenv("CHROMA_HOST", "chromadb")
    port = int(os.getenv("CHROMA_PORT", "8000"))
    return chromadb.HttpClient(host=host, port=port)


def _get_collection():
    client = _get_client()
    return client.get_or_create_collection("autocrew_results")


def store_result(task_id: str, input_task: str, final_output: str) -> None:
    """Store a completed task result in ChromaDB for future RAG retrieval."""
    try:
        from openai import OpenAI

        oai = OpenAI()
        response = oai.embeddings.create(
            model="text-embedding-3-small",
            input=final_output[:8000],
        )
        embedding = response.data[0].embedding

        collection = _get_collection()
        collection.upsert(
            ids=[task_id],
            embeddings=[embedding],
            documents=[final_output[:2000]],
            metadatas=[{
                "task_id": task_id,
                "input_task": input_task[:500],
                "created_at": datetime.utcnow().isoformat(),
            }],
        )
    except Exception:
        pass


def search_similar(query: str, n_results: int = 3) -> list[dict]:
    """Search ChromaDB for similar past research results."""
    try:
        from openai import OpenAI

        oai = OpenAI()
        response = oai.embeddings.create(
            model="text-embedding-3-small",
            input=query[:8000],
        )
        embedding = response.data[0].embedding

        collection = _get_collection()
        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            output.append({
                "task_id": metadata.get("task_id", ""),
                "input_task": metadata.get("input_task", ""),
                "output_preview": doc[:300],
                "similarity_score": round(1 - distance, 3),
            })

        return output

    except Exception:
        return []
