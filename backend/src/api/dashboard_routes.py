from fastapi import APIRouter, Depends

from src.api.deps import get_current_user
from src.config import settings
from src.db.models import User
from src.schemas.dashboard_schema import StatsResponse
from src.services.document_service import DocumentService
from src.services.ollama_client_service import get_llm_client
from src.services.query_service import QueryService

router = APIRouter()

query_service = QueryService()
document_service = DocumentService()


@router.get("/stats", response_model=StatsResponse)
async def get_stats(current_user: User = Depends(get_current_user)):
    """Usage and vector store stats for the current user."""
    user_id = current_user.id

    query_session_count = await query_service.get_total_query_sessions_by_user_id(user_id)
    avg_response_time = await query_service.get_average_response_time_by_user_id(user_id)
    daily_average_response_times = await query_service.get_daily_response_times_by_user_id(user_id)
    daily_query_counts = await query_service.get_daily_query_counts_by_user_id(user_id)

    vector_stats = await document_service.get_vector_store_stats(user_id)
    # Reaching this point means the database answered; the LLM is the remaining dependency to check.
    llm_available = await get_llm_client().is_available()

    return StatsResponse(
        query_count=query_session_count,
        document_count=vector_stats.documents,
        total_documents=vector_stats.documents,
        total_chunks=vector_stats.chunks,
        total_embeddings=vector_stats.chunks,
        total_pages=vector_stats.pages,
        dimensionality=settings.EMBEDDING_DIMENSION,
        disk_usage_mb=round(vector_stats.embedding_bytes / (1024 * 1024), 3),
        health_status="Healthy" if llm_available else "Degraded",
        last_updated=vector_stats.last_updated,
        average_response_time=round(avg_response_time, 2),
        daily_average_response_times=[{"date": str(date), "avg_response_time": round(avg_time, 2)} for date, avg_time in daily_average_response_times],
        daily_query_counts=[{"date": str(date), "query_count": count} for date, count in daily_query_counts]
    )
