# AI Backend - 맛집 추천 RAG 시스템

AWS Bedrock (Claude)와 OpenSearch를 활용한 맛집 추천 RAG (Retrieval-Augmented Generation) 백엔드 서버입니다.

## 기술 스택

- **FastAPI**: 고성능 웹 프레임워크
- **AWS Bedrock**: Claude 3.5 Sonnet (LLM), Titan Embeddings (임베딩)
- **OpenSearch**: 벡터 검색 및 하이브리드 검색
- **Python 3.11+**

## 프로젝트 구조

```
ai-server/
├── app/
│   ├── main.py                    # FastAPI 애플리케이션
│   ├── core/
│   │   └── config.py             # 환경 변수 설정
│   ├── api/
│   │   └── routes_chat.py        # 채팅 및 검색 엔드포인트
│   └── services/
│       ├── bedrock_client.py     # AWS Bedrock 클라이언트
│       ├── opensearch_client.py  # OpenSearch 클라이언트
│       └── rag_service.py        # RAG 서비스 로직
├── tests/
├── .env                           # 환경 변수
├── requirements.txt               # Python 의존성
└── README.md
```

## 설치 및 실행

### 1. 환경 변수 설정

`.env` 파일에 AWS 및 OpenSearch 정보 입력:

```env
# AWS Bedrock Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# OpenSearch Configuration
OPENSEARCH_HOST=your-opensearch-host
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=your_password
```

### 2. 의존성 설치

```bash
cd ai-server
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
# 개발 모드 (자동 리로드)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 프로덕션 모드
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

서버가 시작되면 다음 URL에서 접근 가능:
- API: http://localhost:8000
- Swagger 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트

### 1. Health Check

```http
GET /health
```

**응답:**
```json
{
  "status": "ok"
}
```

### 2. 맛집 추천 채팅

```http
POST /api/v1/chat
Content-Type: application/json

{
  "query": "강남에서 회식하기 좋은 곳 추천해줘",
  "lat": 37.5665,
  "lng": 126.9780,
  "budget": 50000,
  "k": 5
}
```

**파라미터:**
- `query` (필수): 사용자 질문
- `lat` (선택): 위도
- `lng` (선택): 경도
- `budget` (선택): 예산 (원)
- `k` (선택): 검색할 결과 수 (기본값: 5)

**응답:**
```json
{
  "answer": "강남에서 회식하기 좋은 맛집을 추천드립니다...",
  "search_results": [
    {
      "name": "맛집 이름",
      "category": "한식",
      "location": "서울 강남구",
      "price": 45000,
      "rating": 4.5,
      "score": 0.95
    }
  ],
  "metadata": {
    "query": "강남에서 회식하기 좋은 곳 추천해줘",
    "lat": 37.5665,
    "lng": 126.978,
    "budget": 50000,
    "num_results": 5
  }
}
```

### 3. 맛집 검색 (LLM 응답 없이)

```http
GET /api/v1/search?query=한식&lat=37.5665&lng=126.9780&budget=30000&k=5&search_type=hybrid
```

**파라미터:**
- `query` (필수): 검색 쿼리
- `lat` (선택): 위도
- `lng` (선택): 경도
- `budget` (선택): 예산
- `k` (선택): 결과 수 (기본값: 5)
- `search_type` (선택): vector, text, hybrid (기본값: hybrid)

**응답:**
```json
{
  "results": [... ],
  "metadata": {
    "query": "한식",
    "num_results": 5,
    "search_type": "hybrid"
  }
}
```

## 주요 기능

### 1. RAG (Retrieval-Augmented Generation)

1. **임베딩 생성**: Titan Embeddings V2로 텍스트를 벡터화
2. **벡터 검색**: OpenSearch k-NN으로 유사 맛집 검색
3. **하이브리드 검색**: 벡터 + 텍스트 검색 결합
4. **LLM 생성**: Claude 3.5 Sonnet으로 자연스러운 답변 생성

### 2. 검색 필터

- **위치 기반**: 위도/경도 기반 반경 검색 (기본 5km)
- **예산 기반**: 예산의 ±30% 범위 필터링
- **카테고리**: 음식 카테고리별 필터

### 3. 검색 타입

- **vector**: 의미 기반 벡터 검색
- **text**: 키워드 기반 텍스트 검색
- **hybrid**: 벡터 + 텍스트 결합 (기본값, 추천)

## 테스트

Python 스크립트로 API 테스트:

```bash
python test_api.py
```

또는 cURL:

```bash
# Health check
curl http://localhost:8000/health

# 채팅
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "맛집 추천해줘",
    "lat": 37.5665,
    "lng": 126.9780,
    "budget": 50000
  }'
```

## 개발 가이드

### 새로운 엔드포인트 추가

1. `app/api/` 에 새로운 라우터 파일 생성
2. `app/main.py` 에 라우터 등록

```python
from app.api.new_router import router as new_router
app.include_router(new_router, prefix="/api/v1")
```

### 환경 변수 추가

1. `app/core/config.py` 에 설정 추가
2. `.env` 파일에 값 설정

```python
class Settings(BaseSettings):
    new_setting: str = "default_value"
```

## 주의사항

1. **AWS 자격증명**: `.env` 파일을 git에 커밋하지 마세요
2. **OpenSearch 인증**: SSL 인증서 검증이 비활성화되어 있습니다 (개발용)
3. **비용**: Bedrock 및 OpenSearch 사용량에 따라 AWS 비용 발생

## 다음 단계

- [ ] OpenSearch 인덱스 생성 및 데이터 삽입
- [ ] 에러 핸들링 강화
- [ ] 로깅 시스템 추가
- [ ] 캐싱 시스템 구현
- [ ] 테스트 코드 작성
- [ ] Docker 컨테이너화
- [ ] CI/CD 파이프라인 구축

## 라이선스

MIT License
