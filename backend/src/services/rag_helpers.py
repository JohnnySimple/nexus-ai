"""Helper functions for RAG services."""
from fastapi import HTTPException
import src.helper_functions as helper_functions
from src.schemas.chat_schema import ChatRequest
from src.config import settings
import logging

logger = logging.getLogger(__name__)

def build_context(results, request) -> str:
    """Build context from query results."""
    # sort all the relevant chunks by score and return top_k
    # all_relevant_chunks = [(chunk_text, score, doc_id, page_num), ...]
    all_relevant_chunks = []
    for res in results:
        all_relevant_chunks.extend(res["relevant_chunks"])
    all_relevant_chunks = sorted(all_relevant_chunks, key=lambda x: x[1], reverse=True)[:request.top_k]

    # get top k chunks
    top_chunks = all_relevant_chunks[:request.top_k]

    context = "\n".join(f"- {chunk[0]}" for res in top_chunks for chunk in res)
    return context


async def get_query_output(request, context, results) -> dict:
    """Generate final output for a RAG query."""
    if request.with_llm_response:
        try:
            prompt_template = helper_functions.get_rag_prompt_template()
            prompt = prompt_template.format(question=request.query, context=context)

            from src.services.ollama_client_service import OllamaClient
            ollama_client = OllamaClient()

            chat_request = ChatRequest(
                model=settings.OLLAMA_MODEL_MISTRAL,
                messages=[{"role": "user", "content": prompt}]
            )

            llm_response = await ollama_client.generate(
                {
                    "model": chat_request.model,
                    "prompt": prompt
                }
            )

            return {
                "query": request.query,
                "results": results,
                # "results_content": results_content,
                "context": context,
                "final_prompt": prompt,
                "llm_response": llm_response.get("response", "")
            }
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"LLM response generation failed: {str(e)}")
    else:
        return {
            "query": request.query,
            "results": results,
            # "results_content": results_content,
            "context": context,
        }