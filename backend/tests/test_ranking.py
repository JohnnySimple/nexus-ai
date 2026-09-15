from src.services.rag_helpers import build_context, rank_chunks


def chunk(answer: str, similarity: float, rerank: float | None = None, page: int = 1) -> dict:
    return {
        "document_name": "aapl-10k.pdf",
        "answer": answer,
        "similarity_score": similarity,
        "document_id": "doc-1",
        "page_number": page,
        "rerank_score": rerank,
    }


def test_rank_orders_by_similarity_highest_first_and_truncates():
    ranked = rank_chunks([chunk("low", 0.2), chunk("high", 0.9), chunk("mid", 0.5)], top_k=2)

    assert [c["answer"] for c in ranked] == ["high", "mid"]


def test_rerank_score_takes_precedence_over_similarity():
    ranked = rank_chunks([chunk("close", 0.9, rerank=-3.0), chunk("relevant", 0.6, rerank=4.2)], top_k=2)

    assert [c["answer"] for c in ranked] == ["relevant", "close"]


def test_context_preserves_rank_order():
    context = build_context([chunk("best", 0.91, page=4), chunk("next", 0.55, page=9)])

    assert context.splitlines() == [
        "- (score=0.9100, doc=aapl-10k.pdf, page=4) best",
        "- (score=0.5500, doc=aapl-10k.pdf, page=9) next",
    ]
