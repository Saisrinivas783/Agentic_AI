import os
import logging
from typing import Optional

from langchain_aws import ChatBedrockConverse
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BedrockLLMClient:
    """
    Wrapper for LangChain's ChatBedrockConverse with config-driven initialization.
    """

    def __init__(
        self,
        model_id: str,
        region: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        profile_name: Optional[str] = None,
    ):
        self.model_id = model_id
        self.region = region
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.profile_name = profile_name
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> ChatBedrockConverse:
        """Initialize the AWS Bedrock LLM."""
        try:
            # Determine if we should use credential profile (for local development)
            use_profile = not os.getenv(
                "AWS_EXECUTION_ENV"
            )  # Not running in AWS Lambda/ECS

            llm_kwargs = {
                "model_id": self.model_id,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "region_name": self.region,
            }

            # Add credential profile for local development
            if use_profile and self.profile_name:
                llm_kwargs["credentials_profile_name"] = self.profile_name
                logger.info(
                    f"Using AWS credential profile: {self.profile_name}"
                )
            else:
                logger.info(
                    "Using default AWS credential chain (IAM roles, environment variables, etc.)"
                )

            llm = ChatBedrockConverse(**llm_kwargs)
            logger.info("Successfully initialized Bedrock LLM")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock LLM: {e}")
            raise

    def invoke(self, user_text: str, system_text: Optional[str] = None):
        """Invoke the LLM with user and optional system text."""
        if system_text:
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [SystemMessage(content=system_text), HumanMessage(content=user_text)]
            return self.llm.invoke(messages)
        else:
            return self.llm.invoke(user_text)


def make_llm(
    model: Optional[str] = None,
    region: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    profile_name: Optional[str] = None,
) -> BedrockLLMClient:
    """
    Factory function to create BedrockLLMClient with config defaults.
    If parameters are not provided, loads from environment/config.
    """
    try:
        import config
        
        # Use provided values or fall back to config
        model_id = model or config.bedrock_model_id
        region = region or config.aws_default_region
        temperature = temperature if temperature is not None else config.bedrock_temperature
        max_tokens = max_tokens or config.bedrock_max_tokens
        profile_name = profile_name or config.aws_credentials_profile
        
    except ImportError:
        # Fallback if config module doesn't exist
        model_id = model or "openai.gpt-oss-120b-1:0"
        region = region or "us-east-1"
        temperature = temperature if temperature is not None else 0.0
        max_tokens = max_tokens or 1024
        profile_name = profile_name or "default"

    return BedrockLLMClient(
        model_id=model_id,
        region=region,
        temperature=temperature,
        max_tokens=max_tokens,
        profile_name=profile_name,
    )


if __name__ == "__main__":
    llm_client = make_llm()
    res = llm_client.invoke("Say hello in French.")
    print(res.content)
