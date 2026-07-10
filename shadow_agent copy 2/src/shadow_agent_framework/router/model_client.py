"""
Model Client — calls LLM APIs (OpenAI, Anthropic, Azure, local).
"""

import os # Added for environment variable access
import asyncio
import logging
from typing import Optional

from shadow_agent_framework.config.settings import ModelConfig
from ..models.schemas import InferenceRequest, InferenceResponse, RequestStatus

logger = logging.getLogger(__name__)


class ModelClient:
    """
    Unified client for calling different LLM providers.
    
    Supports: OpenAI, Anthropic, Azure OpenAI, and local endpoints.
    Uses LangChain's chat model integrations under the hood.
    """

    def __init__(self):
        self._clients: dict = {}

    def _get_client(self, model_config: ModelConfig):
        """Get or create a LangChain chat model client for the given config."""
        cache_key = f"{model_config.provider}:{model_config.model_id}"

        if cache_key in self._clients:
            return self._clients[cache_key]

        api_key = model_config.api_key
        gemini_api_key = os.environ.get(model_config.gemini_api_key_env) if model_config.gemini_api_key_env else None

        if model_config.provider == "openai":
            from langchain_openai import ChatOpenAI

            client = ChatOpenAI(
                model=model_config.model_id,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                openai_api_key=api_key,
                openai_api_base=model_config.api_base,
                request_timeout=model_config.timeout_seconds,
                **model_config.extra_params,
            )
        elif model_config.provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            if not gemini_api_key:
                raise ValueError("Gemini API key not found in environment variables.")
            client = ChatGoogleGenerativeAI(
                model=model_config.model_id,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                google_api_key=gemini_api_key,
                convert_system_message_to_human=True,
                request_timeout=model_config.timeout_seconds,
                **model_config.extra_params,
            )
        elif model_config.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            client = ChatAnthropic(
                model=model_config.model_id,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                anthropic_api_key=api_key,
                **model_config.extra_params,
            )
        elif model_config.provider == "azure":
            from langchain_openai import AzureChatOpenAI

            client = AzureChatOpenAI(
                azure_deployment=model_config.model_id,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                api_key=api_key,
                azure_endpoint=model_config.api_base or "",
                request_timeout=model_config.timeout_seconds,
                **model_config.extra_params,
            )
        else:
            # Fallback: generic OpenAI-compatible endpoint
            from langchain_openai import ChatOpenAI

            client = ChatOpenAI(
                model=model_config.model_id,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                openai_api_key=api_key or "dummy",
                openai_api_base=model_config.api_base or "http://localhost:8000/v1",
                request_timeout=model_config.timeout_seconds,
                **model_config.extra_params,
            )

        self._clients[cache_key] = client
        return client

    async def call(
        self, model_config: ModelConfig, request: InferenceRequest
    ) -> InferenceResponse:
        """
        Call a model with the given inference request.
        
        Uses LangChain's async invocation for non-blocking calls.
        """
        try:
            client = self._get_client(model_config)

            # Convert messages to LangChain message format
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

            lc_messages = []
            for msg in request.messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))
                else:
                    lc_messages.append(HumanMessage(content=content))

            # Invoke the model asynchronously
            response = await client.ainvoke(lc_messages)

            # Extract usage if available
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = {
                    "prompt_tokens": response.usage_metadata.get("input_tokens", 0),
                    "completion_tokens": response.usage_metadata.get("output_tokens", 0),
                    "total_tokens": response.usage_metadata.get("total_tokens", 0),
                }

            return InferenceResponse(
                request_id=request.request_id,
                model_name=model_config.name,
                model_id=model_config.model_id,
                content=response.content,
                usage=usage,
                status=RequestStatus.COMPLETED,
                raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
            )

        except Exception as e:
            logger.error(f"Model call failed for {model_config.name}: {e}")
            return InferenceResponse(
                request_id=request.request_id,
                model_name=model_config.name,
                model_id=model_config.model_id,
                status=RequestStatus.FAILED,
                error=str(e),
            )
