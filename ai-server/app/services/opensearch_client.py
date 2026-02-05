from opensearchpy import OpenSearch, RequestsHttpConnection
from typing import List, Dict, Any, Optional
import json
from app.core.config import settings


class OpenSearchClient:
    """OpenSearch 벡터 검색 클라이언트"""

    def __init__(self):
        """OpenSearch 클라이언트 초기화"""
        # OpenSearch 연결 설정
        self.client = OpenSearch(
            hosts=[{
                'host': settings.opensearch_host,
                'port': settings.opensearch_port
            }],
            http_auth=(settings.opensearch_user, settings.opensearch_password),
            use_ssl=True,
            verify_certs=False,
            ssl_show_warn=False,
            connection_class=RequestsHttpConnection
        )

        # 인덱스 이름 (맛집 데이터용)
        self.index_name = "restaurants"

    def search_by_vector(
        self,
        query_vector: List[float],
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        벡터 유사도 검색 (k-NN)

        Args:
            query_vector: 쿼리 임베딩 벡터
            k: 반환할 결과 수
            filters: 추가 필터 조건 (예: 위치, 예산 등)

        Returns:
            검색 결과 리스트
        """
        try:
            # k-NN 쿼리 구성
            query = {
                "size": k,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_vector,
                            "k": k
                        }
                    }
                }
            }

            # 필터가 있으면 bool 쿼리로 결합
            if filters:
                query["query"] = {
                    "bool": {
                        "must": [
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_vector,
                                        "k": k
                                    }
                                }
                            }
                        ],
                        "filter": self._build_filters(filters)
                    }
                }

            # 검색 실행
            response = self.client.search(
                index=self.index_name,
                body=query
            )

            # 결과 파싱
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'data': hit['_source']
                }
                results.append(result)

            return results

        except Exception as e:
            print(f"OpenSearch 검색 오류: {str(e)}")
            return []

    def search_by_text(
        self,
        query_text: str,
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        텍스트 키워드 검색

        Args:
            query_text: 검색 쿼리 텍스트
            k: 반환할 결과 수
            filters: 추가 필터 조건

        Returns:
            검색 결과 리스트
        """
        try:
            # 텍스트 검색 쿼리
            query = {
                "size": k,
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["name^3", "description^2", "category", "location"],
                        "type": "best_fields"
                    }
                }
            }

            # 필터 추가
            if filters:
                query["query"] = {
                    "bool": {
                        "must": [query["query"]],
                        "filter": self._build_filters(filters)
                    }
                }

            # 검색 실행
            response = self.client.search(
                index=self.index_name,
                body=query
            )

            # 결과 파싱
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'data': hit['_source']
                }
                results.append(result)

            return results

        except Exception as e:
            print(f"OpenSearch 텍스트 검색 오류: {str(e)}")
            return []

    def _build_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        필터 조건 빌더

        Args:
            filters: 필터 딕셔너리
                - lat, lng, radius: 위치 기반 필터 (km)
                - budget_min, budget_max: 예산 범위 필터
                - category: 카테고리 필터

        Returns:
            OpenSearch 필터 쿼리 리스트
        """
        filter_clauses = []

        # 위치 기반 필터 (geo_distance)
        if 'lat' in filters and 'lng' in filters:
            radius = filters.get('radius', 5)  # 기본 5km
            filter_clauses.append({
                "geo_distance": {
                    "distance": f"{radius}km",
                    "location": {
                        "lat": filters['lat'],
                        "lon": filters['lng']
                    }
                }
            })

        # 예산 범위 필터
        if 'budget_min' in filters or 'budget_max' in filters:
            budget_filter = {"range": {"price": {}}}
            if 'budget_min' in filters:
                budget_filter["range"]["price"]["gte"] = filters['budget_min']
            if 'budget_max' in filters:
                budget_filter["range"]["price"]["lte"] = filters['budget_max']
            filter_clauses.append(budget_filter)

        # 카테고리 필터
        if 'category' in filters:
            filter_clauses.append({
                "term": {"category": filters['category']}
            })

        return filter_clauses

    def hybrid_search(
        self,
        query_text: str,
        query_vector: List[float],
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 (텍스트 + 벡터)

        Args:
            query_text: 검색 텍스트
            query_vector: 쿼리 임베딩 벡터
            k: 반환할 결과 수
            filters: 추가 필터
            alpha: 벡터 검색 가중치 (0~1, 1에 가까울수록 벡터 검색 우선)

        Returns:
            검색 결과 리스트
        """
        # 간단한 하이브리드: 두 검색 결과를 합치고 재정렬
        vector_results = self.search_by_vector(query_vector, k=k*2, filters=filters)
        text_results = self.search_by_text(query_text, k=k*2, filters=filters)

        # 점수 정규화 및 결합
        combined_scores = {}

        for result in vector_results:
            doc_id = result['id']
            combined_scores[doc_id] = {
                'score': result['score'] * alpha,
                'data': result['data']
            }

        for result in text_results:
            doc_id = result['id']
            if doc_id in combined_scores:
                combined_scores[doc_id]['score'] += result['score'] * (1 - alpha)
            else:
                combined_scores[doc_id] = {
                    'score': result['score'] * (1 - alpha),
                    'data': result['data']
                }

        # 점수 기준 정렬
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )

        # 상위 k개 반환
        return [
            {'id': doc_id, 'score': data['score'], 'data': data['data']}
            for doc_id, data in sorted_results[:k]
        ]


# 싱글톤 인스턴스
opensearch_client = OpenSearchClient()
