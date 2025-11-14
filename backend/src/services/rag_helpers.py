"""Helper functions for RAG services."""
from fastapi import HTTPException
import src.helper_functions as helper_functions
from src.schemas.chat_schema import ChatRequest
from src.config import settings
import logging

logger = logging.getLogger(__name__)

def build_context(results, request) -> str:
    """Build context from query results"""
    all_chunks = []
    for res in results:
        doc_name = res["document"]["filename"]
        for group in res["relevant_chunks"]:
            # for filename, text, score, doc_id, page, reranked_value in group:
            for item in group:
                # all_chunks.append((text, score, doc_name, page))
                all_chunks.append({
                    "document_name": item["document_name"],
                    "answer": item["answer"],
                    "similarity_score": item["similarity_score"],
                    "document_id": item["document_id"],
                    "page_number": item["page_number"]
                })
    
    # top_chunks = sorted(all_chunks, key=lambda x: x[1], reverse=True)[:request.top_k]
    top_chunks = sorted(all_chunks, key=lambda x: x["similarity_score"], reverse=True)[:request.top_k]

    context = "\n".join(
        # f"- (score={score:.4f}, doc={doc_name.split('/')[-1]}, page={page}) {text}"
        # for text, score, doc_name, page in top_chunks
        f"- (score={item['similarity_score']:.4f}, doc={item['document_name'].split('/')[-1]}, page={item['page_number']}) {item['answer']}"
        for item in top_chunks
    )

    return context

def build_context_db(results, request) -> str:
    """Build context from query results from db"""
    all_chunks = []
    for res in results:
        for item in res["relevant_chunks"]:
            all_chunks.append({
                "document_name": item["document_name"],
                "answer": item["answer"],
                "similarity_score": item["similarity_score"],
                "document_id": item["document_id"],
                "page_number": item["page_number"]
            })
    
    top_chunks = sorted(all_chunks, key=lambda x: x["similarity_score"], reverse=True)[:request.top_k]

    context = "\n".join(
        f"- (score={item['similarity_score']:.4f}, doc={item['document_name'].split('/')[-1]}, page={item['page_number']}) {item['answer']}"
        for item in top_chunks
    )

    return context

def format_history(history: list) -> str:
    """Format history to be passed to context"""
    formatted_history = ""
    for turn in history:
        formatted_history += f"User: {turn.query}\nAssistant: {turn.response}\n"
    return formatted_history


async def get_query_output(request, context, results, history) -> dict:
    """Generate final output for a RAG query."""
    if request.with_llm_response:
        try:
            formatted_history = format_history(history)
            prompt_template = helper_functions.get_rag_prompt_template()
            prompt = prompt_template.format(history=formatted_history, question=request.query, context=context)

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
            "context": context,
        }
    
async def get_full_document(document) -> dict:
    """
    Construct and return full document
    """
    try:
        doc = {
            "id": document.id,
            "metadata": {
                "filename": document.filename,
                "created_at": document.created_at
            },
            "content": [],
            "pages": document.pages
        }
        
        for page in document.pages:
            
            page_content = {
                "page_number": page.page_number,
                "text": page.text,
                "chunks": [],
                "embedding": []
            }
            
            for embedding in page.embeddings:
                page_content["chunks"].append(embedding.chunk_text)
                page_content["embedding"].append(embedding.embedding)

            doc["content"].append(page_content)
        return doc
    except Exception as e:
        logger.error(f"Error occurred getting full document: {e}")
        return {}