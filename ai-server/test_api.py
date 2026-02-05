import requests
import json


def print_section(title):
    """섹션 구분자 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_health():
    """Health check 엔드포인트 테스트"""
    print_section("1. Health Check")

    response = requests.get("http://localhost:8000/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")


def test_chat():
    """채팅 엔드포인트 테스트"""
    print_section("2. Chat Endpoint (RAG)")

    chat_data = {
        "query": "강남에서 회식하기 좋은 한식당 추천해줘",
        "lat": 37.5665,
        "lng": 126.9780,
        "budget": 50000,
        "k": 3
    }

    print(f"Request Data:")
    print(json.dumps(chat_data, ensure_ascii=False, indent=2))
    print()

    try:
        response = requests.post("http://localhost:8000/api/v1/chat", json=chat_data)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nAnswer:")
            print(data.get('answer', 'No answer'))

            print(f"\nSearch Results ({len(data.get('search_results', []))}):")
            for i, result in enumerate(data.get('search_results', []), 1):
                print(f"\n  {i}. {result.get('name', 'N/A')}")
                print(f"     Category: {result.get('category', 'N/A')}")
                print(f"     Location: {result.get('location', 'N/A')}")
                print(f"     Price: {result.get('price', 'N/A')}원")
                print(f"     Rating: {result.get('rating', 'N/A')}")
                print(f"     Score: {result.get('score', 0):.4f}")

            print(f"\nMetadata:")
            print(json.dumps(data.get('metadata', {}), ensure_ascii=False, indent=2))
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Error: {str(e)}")


def test_search():
    """검색 전용 엔드포인트 테스트"""
    print_section("3. Search Endpoint (No LLM)")

    params = {
        "query": "이탈리안",
        "lat": 37.5665,
        "lng": 126.9780,
        "budget": 30000,
        "k": 5,
        "search_type": "hybrid"
    }

    print(f"Request Params:")
    print(json.dumps(params, ensure_ascii=False, indent=2))
    print()

    try:
        response = requests.get("http://localhost:8000/api/v1/search", params=params)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            print(f"\nSearch Results ({len(data.get('results', []))}):")
            for i, result in enumerate(data.get('results', []), 1):
                result_data = result.get('data', {})
                print(f"\n  {i}. {result_data.get('name', 'N/A')}")
                print(f"     Category: {result_data.get('category', 'N/A')}")
                print(f"     Location: {result_data.get('location', 'N/A')}")
                print(f"     Price: {result_data.get('price', 'N/A')}원")
                print(f"     Score: {result.get('score', 0):.4f}")

            print(f"\nMetadata:")
            print(json.dumps(data.get('metadata', {}), ensure_ascii=False, indent=2))
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Error: {str(e)}")


def test_docs():
    """API 문서 URL 출력"""
    print_section("4. API Documentation")
    print("Swagger UI: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
    print("OpenAPI JSON: http://localhost:8000/openapi.json")


if __name__ == "__main__":
    print("\n🚀 AI Backend API Test Suite")
    print("=" * 80)

    try:
        test_health()
        test_chat()
        test_search()
        test_docs()

        print("\n" + "=" * 80)
        print("✅ All tests completed!")
        print("=" * 80 + "\n")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server.")
        print("Please make sure the server is running on http://localhost:8000")
        print("\nStart server with:")
        print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
