import boto3
import json
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.opensearch_client import opensearch_client
from app.services.bedrock_client import bedrock_client


class EmbeddingClient:
    """임베딩 생성 클라이언트 (Bedrock Titan Embeddings)"""

    def __init__(self):
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        # Titan Embeddings V2 모델
        self.model_id = "amazon.titan-embed-text-v2:0"

    def get_embedding(self, text: str) -> List[float]:
        """
        텍스트를 임베딩 벡터로 변환

        Args:
            text: 임베딩할 텍스트

        Returns:
            임베딩 벡터 (1024차원)
        """
        try:
            body = json.dumps({
                "inputText": text
            })

            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body
            )

            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding")

            return embedding

        except Exception as e:
            print(f"임베딩 생성 오류: {str(e)}")
            raise


class RAGService:
    """RAG (Retrieval-Augmented Generation) 서비스"""

    def __init__(self):
        self.embedding_client = EmbeddingClient()
        self.opensearch = opensearch_client
        self.bedrock = bedrock_client

    def search_restaurants(
        self,
        query: str,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        budget: Optional[int] = None,
        k: int = 5,
        search_type: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """
        맛집 검색

        Args:
            query: 검색 쿼리
            lat: 위도
            lng: 경도
            budget: 예산
            k: 반환할 결과 수
            search_type: 검색 타입 (vector, text, hybrid)

        Returns:
            검색된 맛집 리스트
        """
        # 필터 구성
        filters = {}
        if lat is not None and lng is not None:
            filters['lat'] = lat
            filters['lng'] = lng
            filters['radius'] = 5  # 기본 5km 반경

        if budget is not None:
            # 예산 범위: budget의 ±30%
            filters['budget_min'] = int(budget * 0.7)
            filters['budget_max'] = int(budget * 1.3)

        # 검색 타입에 따라 다른 검색 수행
        if search_type == "vector":
            # 벡터 검색
            query_vector = self.embedding_client.get_embedding(query)
            results = self.opensearch.search_by_vector(
                query_vector=query_vector,
                k=k,
                filters=filters
            )

        elif search_type == "text":
            # 텍스트 검색
            results = self.opensearch.search_by_text(
                query_text=query,
                k=k,
                filters=filters
            )

        else:  # hybrid (기본값)
            # 하이브리드 검색
            query_vector = self.embedding_client.get_embedding(query)
            results = self.opensearch.hybrid_search(
                query_text=query,
                query_vector=query_vector,
                k=k,
                filters=filters,
                alpha=0.6  # 벡터 검색에 약간 더 가중치
            )

        return results

    def generate_answer(
        self,
        user_query: str,
        search_results: List[Dict[str, Any]],
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        budget: Optional[int] = None
    ) -> str:
        """
        검색 결과를 바탕으로 LLM 답변 생성

        Args:
            user_query: 사용자 질문
            search_results: 검색된 맛집 결과
            lat: 사용자 위치 위도
            lng: 사용자 위치 경도
            budget: 사용자 예산

        Returns:
            생성된 답변
        """
        # 검색 결과가 없으면 기본 응답
        if not search_results:
            return "죄송합니다. 조건에 맞는 맛집을 찾을 수 없습니다. 다른 조건으로 다시 검색해보시겠어요?"

        # 컨텍스트 구성
        context = self._build_context(search_results, lat, lng, budget)

        # 시스템 프롬프트
        system_instruction = """당신은 친절하고 전문적인 맛집 추천 AI 어시스턴트입니다.

다음 규칙을 따라주세요:
1. 주어진 맛집 정보만을 바탕으로 추천해주세요
2. 각 맛집의 특징, 메뉴, 가격대를 간단히 설명해주세요
3. 사용자의 위치와 예산을 고려해주세요
4. 친근하고 자연스러운 톤으로 답변해주세요
5. 추천 맛집은 최대 3-5개 정도로 제한해주세요
6. 각 맛집에 대해 간단한 추천 이유를 함께 제공해주세요"""

        # LLM으로 답변 생성
        answer = self.bedrock.generate_with_context(
            user_query=user_query,
            context=context,
            system_instruction=system_instruction
        )

        return answer

    def _build_context(
        self,
        search_results: List[Dict[str, Any]],
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        budget: Optional[int] = None
    ) -> str:
        """
        검색 결과를 LLM용 컨텍스트로 변환

        Args:
            search_results: 검색 결과
            lat: 사용자 위도
            lng: 사용자 경도
            budget: 사용자 예산

        Returns:
            포맷된 컨텍스트 문자열
        """
        context_parts = []

        # 사용자 정보 추가
        if lat and lng:
            context_parts.append(f"사용자 위치: 위도 {lat}, 경도 {lng}")
        if budget:
            context_parts.append(f"사용자 예산: {budget:,}원")

        context_parts.append("\n검색된 맛집 정보:\n")

        # 각 맛집 정보 추가
        for idx, result in enumerate(search_results, 1):
            data = result['data']

            restaurant_info = f"""
{idx}. {data.get('name', '이름 없음')}
   - 카테고리: {data.get('category', '정보 없음')}
   - 위치: {data.get('location', '정보 없음')}
   - 가격대: {data.get('price', '정보 없음')}원
   - 설명: {data.get('description', '설명 없음')}
   - 메뉴: {data.get('menu', '메뉴 정보 없음')}
   - 평점: {data.get('rating', 'N/A')}점
   - 검색 점수: {result['score']:.4f}
"""
            context_parts.append(restaurant_info)

        return "\n".join(context_parts)

    def chat(
        self,
        query: str,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        budget: Optional[int] = None,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        전체 RAG 플로우 실행

        Args:
            query: 사용자 질문
            lat: 위도
            lng: 경도
            budget: 예산
            k: 검색할 결과 수

        Returns:
            답변 및 메타데이터를 포함한 딕셔너리
        """
        try:
            # 1. 맛집 검색
            search_results = self.search_restaurants(
                query=query,
                lat=lat,
                lng=lng,
                budget=budget,
                k=k,
                search_type="hybrid"
            )

            # 2. LLM 답변 생성
            answer = self.generate_answer(
                user_query=query,
                search_results=search_results,
                lat=lat,
                lng=lng,
                budget=budget
            )

            # 3. 응답 구성
            return {
                "answer": answer,
                "search_results": [
                    {
                        "name": r['data'].get('name'),
                        "category": r['data'].get('category'),
                        "location": r['data'].get('location'),
                        "price": r['data'].get('price'),
                        "rating": r['data'].get('rating'),
                        "score": r['score']
                    }
                    for r in search_results
                ],
                "metadata": {
                    "query": query,
                    "lat": lat,
                    "lng": lng,
                    "budget": budget,
                    "num_results": len(search_results)
                }
            }

        except Exception as e:
            print(f"RAG 처리 오류: {str(e)}")
            return {
                "answer": f"처리 중 오류가 발생했습니다: {str(e)}",
                "search_results": [],
                "metadata": {"error": str(e)}
            }


# 싱글톤 인스턴스
rag_service = RAGService()
