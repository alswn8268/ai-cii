from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # AWS Bedrock
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # OpenSearch
    opensearch_host: str = ""
    opensearch_port: int = 9200
    opensearch_user: str = ""
    opensearch_password: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
