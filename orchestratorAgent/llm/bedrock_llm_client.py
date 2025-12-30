"""
AWS Bedrock LLM client with timeout configuration and retry logic.

This module provides a ChatModels class that handles:
- AWS authentication via environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- Configurable timeouts and retry logic via botocore
- Extended thinking support for Claude 3.5+ models
- Local development with AWS credential profiles (optional)
"""

import logging
from typing import Optional

import boto3
from botocore.config import Config
from langchain_aws import ChatBedrockConverse
from langchain_core.language_models.chat_models import BaseChatModel

from settings import orchestrator_settings

logging.basicConfig(
    level=getattr(logging, orchestrator_settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ChatModels:
    """
    Factory class for creating AWS Bedrock chat models.

    Handles authentication via environment variables, timeout configuration,
    and retry logic.

    Authentication:
        Set these environment variables:
        - AWS_ACCESS_KEY_ID: Your AWS access key
        - AWS_SECRET_ACCESS_KEY: Your AWS secret key
        - AWS_DEFAULT_REGION: AWS region (optional, defaults to settings)
    """

    def __init__(self):
        self.settings = orchestrator_settings
        self._client: Optional[boto3.client] = None

    def _get_boto_config(self) -> Config:
        """
        Create botocore Config with timeout and retry settings.

        Returns:
            Config: Configured botocore Config instance
        """
        return Config(
            read_timeout=self.settings.bedrock_read_timeout,
            connect_timeout=self.settings.bedrock_connect_timeout,
            retries={
                "max_attempts": self.settings.bedrock_max_retries,
                "mode": "adaptive",  # Adaptive retry mode for better handling of throttling
            },
        )

    def _get_bedrock_client(self) -> boto3.client:
        """
        Get or create the Bedrock runtime client.

        Authentication is handled via environment variables:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_SESSION_TOKEN (optional, for temporary credentials)

        Returns:
            boto3.client: Configured Bedrock runtime client
        """
        if self._client is not None:
            return self._client

        boto_config = self._get_boto_config()

        # boto3 automatically reads credentials from environment variables:
        # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
        self._client = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.settings.aws_region,
            config=boto_config,
        )

        logger.info(
            f"Initialized Bedrock client for region: {self.settings.aws_region}"
        )
        return self._client

    def bedrock_model(
        self,
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ChatBedrockConverse:
        """
        Initialize ChatBedrockConverse with configured authentication.

        Authentication is handled via AWS environment variables.

        Args:
            model_id: Bedrock model ID (defaults to settings)
            temperature: LLM temperature (defaults to settings)
            max_tokens: Maximum response tokens (defaults to settings)
            **kwargs: Additional parameters for ChatBedrockConverse

        Returns:
            ChatBedrockConverse: Configured Bedrock chat model instance
        """
        client = self._get_bedrock_client()

        model = ChatBedrockConverse(
            client=client,
            model=model_id or self.settings.bedrock_model_id,
            region_name=self.settings.aws_region,
            temperature=temperature if temperature is not None else self.settings.bedrock_temperature,
            max_tokens=max_tokens or self.settings.bedrock_max_tokens,
            **kwargs,
        )

        logger.info(
            f"Created Bedrock model: {model_id or self.settings.bedrock_model_id}"
        )
        return model

    def bedrock_model_with_extended_thinking(
        self,
        model_id: Optional[str] = None,
        budget_tokens: Optional[int] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ChatBedrockConverse:
        """
        Initialize ChatBedrockConverse with Extended Thinking enabled.

        Extended Thinking allows Claude 3.5+ models to use additional tokens for
        internal reasoning before generating a response, improving quality on
        complex analytical tasks.

        Note: Extended thinking requires temperature=1 and is only supported
        on Claude 3.5 Sonnet and higher models.

        Args:
            model_id: Bedrock model ID (should be Claude 3.5+)
            budget_tokens: Token budget for thinking (defaults to settings)
            max_tokens: Maximum response tokens (defaults to settings)
            **kwargs: Additional parameters for ChatBedrockConverse

        Returns:
            ChatBedrockConverse: Configured Bedrock chat model with extended thinking
        """
        client = self._get_bedrock_client()

        thinking_budget = budget_tokens or self.settings.extended_thinking_budget_tokens
        response_max_tokens = max_tokens or self.settings.extended_thinking_max_tokens

        model = ChatBedrockConverse(
            client=client,
            model=model_id or self.settings.bedrock_model_id,
            region_name=self.settings.aws_region,
            temperature=1,  # Required for extended thinking
            max_tokens=response_max_tokens,
            additional_model_request_fields={
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": thinking_budget,
                }
            },
            **kwargs,
        )

        logger.info(
            f"Created Bedrock model with extended thinking: {model_id or self.settings.bedrock_model_id} "
            f"(budget: {thinking_budget} tokens)"
        )
        return model

    def get_model(
        self,
        model_id: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        """
        Get the appropriate Bedrock model based on settings.

        If extended thinking is enabled in settings, returns a model with
        extended thinking capabilities. Otherwise, returns a standard model.

        Args:
            model_id: Optional model ID override
            **kwargs: Additional parameters for the model

        Returns:
            BaseChatModel: Configured chat model instance
        """
        if self.settings.extended_thinking_enabled:
            return self.bedrock_model_with_extended_thinking(model_id=model_id, **kwargs)
        return self.bedrock_model(model_id=model_id, **kwargs)

    def get_model_for_tool_selection(self, **kwargs) -> BaseChatModel:
        """
        Get a model optimized for tool selection tasks.

        Uses low temperature for deterministic responses.

        Args:
            **kwargs: Additional parameters for the model

        Returns:
            BaseChatModel: Model configured for tool selection
        """
        return self.bedrock_model(
            temperature=0.0,  # Deterministic for consistent tool selection
            **kwargs,
        )

    def get_model_for_conversation(self, **kwargs) -> BaseChatModel:
        """
        Get a model optimized for conversational responses.

        Uses moderate temperature for natural responses.

        Args:
            **kwargs: Additional parameters for the model

        Returns:
            BaseChatModel: Model configured for conversation
        """
        return self.bedrock_model(
            temperature=0.7,  # More creative for conversation
            **kwargs,
        )


# Singleton instance for easy access
_chat_models: Optional[ChatModels] = None


def get_chat_models() -> ChatModels:
    """
    Get the singleton ChatModels instance.

    Returns:
        ChatModels: Shared ChatModels instance
    """
    global _chat_models
    if _chat_models is None:
        _chat_models = ChatModels()
    return _chat_models


# Convenience functions for backwards compatibility
def make_llm(**kwargs) -> BaseChatModel:
    """
    Factory function to create a Bedrock chat model.

    Maintained for backwards compatibility with existing code.

    Args:
        **kwargs: Parameters passed to bedrock_model()

    Returns:
        BaseChatModel: Configured chat model
    """
    return get_chat_models().get_model(**kwargs)


if __name__ == "__main__":
    # Test the client
    chat_models = ChatModels()
    llm = chat_models.get_model()
    response = llm.invoke("Say hello in French.")
    print(f"Response: {response.content}")
