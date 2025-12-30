"""
Legacy configuration module - re-exports from settings for backwards compatibility.

DEPRECATED: Use `from settings import orchestrator_settings` instead.
"""

from settings import orchestrator_settings

# Re-export for backwards compatibility
bedrock_model_id = orchestrator_settings.bedrock_model_id
bedrock_temperature = orchestrator_settings.bedrock_temperature
bedrock_max_tokens = orchestrator_settings.bedrock_max_tokens
aws_default_region = orchestrator_settings.aws_region

# Note: aws_credentials_profile is no longer used
# Authentication is now via AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars
