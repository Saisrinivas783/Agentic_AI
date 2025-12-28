import os
from dotenv import load_dotenv

load_dotenv()

# Bedrock LLM Configuration
bedrock_model_id = os.getenv("BEDROCK_MODEL_ID", "openai.gpt-oss-120b-1:0")
bedrock_temperature = float(os.getenv("BEDROCK_TEMPERATURE", "0.0"))
bedrock_max_tokens = int(os.getenv("BEDROCK_MAX_TOKENS", "1024"))

# AWS Configuration
aws_default_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
aws_credentials_profile = os.getenv("AWS_CREDENTIALS_PROFILE", "default")
