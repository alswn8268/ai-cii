import boto3
import json
from typing import Optional, Dict, Any
from app.core.config import settings


class BedrockClient:
    """AWS Bedrock 클라이언트 - Claude 모델 사용"""

    def __init__(self):
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        # Claude 3.5 Sonnet 모델 ID
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Bedrock Claude 모델로 응답 생성

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택)
            max_tokens: 최대 토큰 수
            temperature: 온도 (0.0 ~ 1.0)

        Returns:
            생성된 응답 텍스트
        """
        try:
            # Claude 3 메시지 포맷
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }

            # 시스템 프롬프트가 있으면 추가
            if system_prompt:
                body["system"] = system_prompt

            # Bedrock API 호출
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            # 응답 파싱
            response_body = json.loads(response["body"].read())

            # Claude 3 응답 포맷에서 텍스트 추출
            if "content" in response_body and len(response_body["content"]) > 0:
                return response_body["content"][0]["text"]

            return "응답을 생성할 수 없습니다."

        except Exception as e:
            print(f"Bedrock API 오류: {str(e)}")
            raise

    def generate_with_context(
        self,
        user_query: str,
        context: str,
        system_instruction: str = "당신은 친절한 맛집 추천 AI 어시스턴트입니다.",
    ) -> str:
        """
        컨텍스트를 포함한 프롬프트로 응답 생성 (RAG용)

        Args:
            user_query: 사용자 질문
            context: 검색된 컨텍스트 (맛집 정보 등)
            system_instruction: 시스템 지시사항

        Returns:
            생성된 응답
        """
        prompt = f"""다음은 사용자의 질문에 답변하기 위한 관련 정보입니다:

<context>
{context}
</context>

위 정보를 바탕으로 다음 질문에 답변해주세요. 정보에 없는 내용은 추측하지 말고, 주어진 정보 내에서만 답변하세요.

사용자 질문: {user_query}"""

        return self.generate_response(
            prompt=prompt,
            system_prompt=system_instruction,
            temperature=0.5
        )


# 싱글톤 인스턴스
bedrock_client = BedrockClient()
