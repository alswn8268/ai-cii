from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.rag_service import rag_service

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    budget: Optional[int] = None
    k: Optional[int] = 5  # 검색할 결과 수


class SearchResult(BaseModel):
    name: str
    category: str
    location: str
    price: int
    rating: float
    score: float


class ChatResponse(BaseModel):
    answer: str
    search_results: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    맛집 추천 채팅 엔드포인트

    Args:
        req: 채팅 요청 (query, lat, lng, budget, k)

    Returns:
        답변, 검색 결과, 메타데이터
    """
    try:
        # RAG 서비스 호출
        result = rag_service.chat(
            query=req.query,
            lat=req.lat,
            lng=req.lng,
            budget=req.budget,
            k=req.k or 5
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/search")
async def search_restaurants(
    query: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    budget: Optional[int] = None,
    k: int = 5,
    search_type: str = "hybrid"
):
    """
    맛집 검색 전용 엔드포인트 (LLM 응답 없이 검색 결과만)

    Args:
        query: 검색 쿼리
        lat: 위도
        lng: 경도
        budget: 예산
        k: 결과 수
        search_type: vector, text, hybrid

    Returns:
        검색 결과 리스트
    """
    try:
        results = rag_service.search_restaurants(
            query=query,
            lat=lat,
            lng=lng,
            budget=budget,
            k=k,
            search_type=search_type
        )

        return {
            "results": results,
            "metadata": {
                "query": query,
                "lat": lat,
                "lng": lng,
                "budget": budget,
                "num_results": len(results),
                "search_type": search_type
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"검색 중 오류가 발생했습니다: {str(e)}"
        )
