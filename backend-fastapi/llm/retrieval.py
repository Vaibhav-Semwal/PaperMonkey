"""
Lightweight, fully-local retrieval: ranks passages against a topic using
TF-IDF cosine similarity. No embedding model download, no vector DB - good
enough at this scale (a handful of links per paper).
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def top_passages_for_topic(passages, topic: str, top_k: int = 3):
    if not passages:
        return []
    if len(passages) <= top_k:
        return passages

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(passages + [topic])
        topic_vector = matrix[-1]
        passage_vectors = matrix[:-1]
        scores = cosine_similarity(topic_vector, passage_vectors)[0]
        ranked = sorted(range(len(passages)), key=lambda i: scores[i], reverse=True)
        return [passages[i] for i in ranked[:top_k]]
    except ValueError:
        return passages[:top_k]