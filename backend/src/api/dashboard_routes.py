from fastapi import APIRouter, Query, HTTPException
from src.services.query_service import QueryService
from src.services.document_service import DocumentService
from src.schemas.dashboard_schema import StatsResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

query_service = QueryService()
document_service = DocumentService()

@router.get("/stats/{user_id}", response_model=StatsResponse)
async def get_status_by_user_id(user_id: str):
    """Get stats by user id."""
    try:
        query_session_count = await query_service.get_total_query_sessions_by_user_id(user_id)
        document_count = await document_service.get_total_documents_by_user_id(user_id)

        total_embeddings = 10

        return StatsResponse(
            query_count=query_session_count,
            document_count=document_count,
            total_documents=1,
            total_chunks=10,
            total_embeddings=total_embeddings,
            total_pages=2,
            dimensionality=384,
            disk_usage_mb=total_embeddings * 384 * 4 / (1024 * 1024),
            health_status="Healthy",
            last_updated="2024-06-01T12:00:00Z"
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user stats.")