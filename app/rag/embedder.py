_model = None


def get_embedding_model():
    global _model

    if _model is None:
        print("Loading embedding model...")
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Embedding model loaded.")

    return _model


def create_embeddings(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts)
    return embeddings.tolist()