import json
from src.schemas.rag_schema import DocumentQueryRequest
from src.services.rag_service import RagService
from src.config import settings
import src.helper_functions as helper_functions
from src.schemas.chat_schema import ChatRequest
import src.services.rag_helpers as rag_helpers


rag_service = RagService()

async def query_docs(request: DocumentQueryRequest):
    """Query documents in the RAG system."""

    yield("data: Querying relevant documents...\n\n")
    results = await rag_service.query_documents(
        query=request.query,
        top_k=request.top_k,
        document_ids=request.document_ids
    )

    yield("data: Retrieving relevant documents.\n\n")
    context = rag_helpers.build_context(results, request)

    yield("data: Augmenting and generating LLM response...\n\n")
    output = await rag_helpers.get_query_output(request, context, results)
    yield f"data: {json.dumps(output)}\n\n"

# async def query_docs(request: DocumentQueryRequest):
#     """Query documents in the RAG system."""
#     yield("data: Querying relevant documents...\n\n")
#     print("data: Querying relevant documents...\n\n")
#     results = await rag_service.query_documents(
#         query=request.query,
#         top_k=request.top_k,
#         document_ids=request.document_ids
#     )

#     yield("data: Retrieving relevant documents.\n\n")
#     print("data: Retrieving relevant documents.\n\n")
#     # sort all the relevant chunks by score and return top_k
#     # all_relevant_chunks = [(chunk_text, score, doc_id, page_num), ...]
#     all_relevant_chunks = []
#     for res in results:
#         all_relevant_chunks.extend(res["relevant_chunks"])
#     all_relevant_chunks = sorted(all_relevant_chunks, key=lambda x: x[1], reverse=True)[:request.top_k]

#     # get top k chunks
#     top_chunks = all_relevant_chunks[:request.top_k]

#     # flatten top_chunks
#     # t_chunks = [chunk for sub in top_chunks for chunk in sub]

#     # results_content = "\n".join(f"- {chunk[0]}" for res in results for chunk in res["relevant_chunks"])
#     context = "\n".join(f"- {chunk[0]}" for res in top_chunks for chunk in res)

#     if request.with_llm_response:
#         try:
#             yield("data: Augmenting and generating LLM response...\n\n")
#             print("data: Augmenting and generating LLM response...\n\n")
#             prompt_template = helper_functions.get_rag_prompt_template()
#             prompt = prompt_template.format(question=request.query, context=context)

#             from src.services.ollama_client_service import OllamaClient
#             ollama_client = OllamaClient()

#             chat_request = ChatRequest(
#                 model=settings.OLLAMA_MODEL_MISTRAL,
#                 messages=[{"role": "user", "content": prompt}]
#             )

#             llm_response = await ollama_client.generate(
#                 {
#                     "model": chat_request.model,
#                     "prompt": prompt
#                 }
#             )

#             payload = {
#                 "query": request.query,
#                 "results": results,
#                 # "results_content": results_content,
#                 "context": context,
#                 "final_prompt": prompt,
#                 "llm_response": llm_response.get("response", "")
#             }
#             yield f"data: {json.dumps(payload)}\n\n"
#         except Exception as e:
#             yield(f"data: LLM response generation failed: {str(e)}\n\n")
#             print(f"data: LLM response generation failed: {str(e)}\n\n")
#             return

#     payload = {
#         "query": request.query,
#         "results": results,
#         # "results_content": results_content,
#         "context": context,
#     }
#     yield f"data: {json.dumps(payload)}\n\n"

#     yield "data: [DONE]\n\n"