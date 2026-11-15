"""Local retrieval for statement descriptions with optional Chroma persistence."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List

from core.config import CHROMA_DB_PATH


def route_intent(question: str) -> str:
    text = question.lower()
    if any(word in text for word in ("transaction", "merchant", "paid", "charge", "where did", "purchase")):
        return "transaction_lookup"
    if any(word in text for word in ("save", "budget", "afford", "reduce", "cut back", "overspend", "advice")):
        return "savings_guidance"
    return "spending_analysis"


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{2,}", text.lower()))


def build_documents(transactions: Iterable[Dict]) -> List[Dict[str, str]]:
    return [{"id": str(index), "text": f"{txn.get('date', '')} | {txn.get('description', '')} | {txn.get('category', 'Uncategorized')} | ₹{abs(float(txn.get('amount', 0))):,.2f}"} for index, txn in enumerate(transactions)]


def retrieve(question: str, transactions: Iterable[Dict], statement_id: str = "", limit: int = 5) -> List[str]:
    """Retrieve from Chroma when available, then fall back to local ranking."""
    if statement_id:
        try:
            import chromadb
            collection = chromadb.PersistentClient(path=CHROMA_DB_PATH).get_collection("statement_transactions")
            result = collection.query(query_texts=[question], n_results=limit, where={"statement_id": statement_id})
            documents = result.get("documents", [[]])[0]
            if documents:
                return documents
        except Exception:
            pass
    query_terms = _tokens(question)
    ranked = []
    for document in build_documents(transactions):
        score = len(query_terms & _tokens(document["text"]))
        if score:
            ranked.append((score, document["text"]))
    return [text for _, text in sorted(ranked, reverse=True)[:limit]]


def persist_to_chroma(transactions: Iterable[Dict], statement_id: str) -> None:
    """Best-effort persistence; the app stays useful if Chroma is unavailable."""
    try:
        import chromadb
        documents = build_documents(transactions)
        if not documents:
            return
        collection = chromadb.PersistentClient(path=CHROMA_DB_PATH).get_or_create_collection("statement_transactions")
        collection.upsert(ids=[f"{statement_id}-{doc['id']}" for doc in documents], documents=[doc["text"] for doc in documents], metadatas=[{"statement_id": statement_id} for _ in documents])
    except Exception:
        return
