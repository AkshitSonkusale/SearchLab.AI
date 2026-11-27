import logging
from typing import List
from fastembed import TextEmbedding
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_embedding_model: TextEmbedding = None

def get_embedding_model() -> TextEmbedding:
    """
    Initializes and caches the fastembed TextEmbedding model.
    Loaded once at server startup to prevent memory overhead and latency per request.
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _embedding_model = TextEmbedding(model_name=settings.embedding_model)
        logger.info("Embedding model loaded successfully.")
    return _embedding_model

def embed_texts(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Generates embeddings for a list of text chunks in batches to control memory usage.
    """
    model = get_embedding_model()
    embeddings = list(model.embed(texts, batch_size=batch_size))
    # Convert numpy arrays to Python standard float lists
    return [vec.tolist() for vec in embeddings]

def embed_query(query: str) -> List[float]:
    """
    Generates embedding for a single search question/query.
    """
    model = get_embedding_model()
    embeddings = list(model.embed([query]))
    return embeddings[0].tolist()
