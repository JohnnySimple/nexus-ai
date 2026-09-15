"""Chunk ranking, prompt construction and LLM calls for RAG queries."""
import src.helper_functions as helper_functions
from src.config import settings
from src.services.ollama_client_service import get_llm_client


def rank_chunks(chunks: list[dict], top_k: int) -> list[dict]:
    """Order chunks best-first: by cross-encoder score when reranked, otherwise by cosine similarity."""
    def score(chunk: dict) -> float:
        if chunk.get("rerank_score") is not None:
            return chunk["rerank_score"]
        return chunk["similarity_score"]

    return sorted(chunks, key=score, reverse=True)[:top_k]

def build_context(chunks: list[dict]) -> str:
    """Render ranked chunks as prompt context, keeping their order"""
    return "\n".join(
        f"- (score={item['similarity_score']:.4f}, doc={item['document_name'].split('/')[-1]}, page={item['page_number']}) {item['answer']}"
        for item in chunks
    )

def format_history(history: list) -> str:
    """Format history to be passed to context"""
    formatted_history = ""
    for turn in history:
        formatted_history += f"User: {turn.query}\nAssistant: {turn.response}\n"
    return formatted_history

async def rewrite_query(query: str) -> dict:
    """Rewrite a conversational question into a standalone search query"""
    prompt = helper_functions.get_prompt_rewrite_template().format(question=query)
    llm_response = await get_llm_client().generate(settings.DEFAULT_LLM_MODEL, prompt)

    return {
        "query": query,
        "final_prompt": prompt,
        "llm_response": llm_response
    }

async def generate_answer(query: str, context: str, history: list) -> tuple[str, str]:
    """Build the grounded RAG prompt and generate an answer; returns (prompt, answer)"""
    prompt = helper_functions.get_rag_prompt_template().format(
        history=format_history(history), question=query, context=context
    )
    return prompt, await get_llm_client().generate(settings.DEFAULT_LLM_MODEL, prompt)
