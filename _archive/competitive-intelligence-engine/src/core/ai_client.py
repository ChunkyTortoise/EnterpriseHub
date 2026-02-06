"""
Unified LLM Client - Multi-provider support for Gemini and Claude.

Provides a consistent interface for interacting with different LLM providers,
including direct SDK access and LangChain compatibility.
"""
import asyncio
import httpx
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generator, Optional, Union, AsyncGenerator, List, TYPE_CHECKING

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

# Import LangChain models only for type checking
if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

logger = get_logger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    CLAUDE = "claude"
    PERPLEXITY = "perplexity"


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    provider: LLMProvider
    model: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    tokens_used: Optional[int] = None  # Legacy support (sum of in + out)
    finish_reason: Optional[str] = None


class LLMClient:
    """
    Unified LLM client supporting multiple providers.

    Provides a consistent interface for Gemini and Claude APIs.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the LLM client.

        Args:
            provider: LLM provider ("gemini" or "claude"). Defaults to settings.
            model: Specific model name. Defaults to settings.
            api_key: Optional API key for multi-tenancy.
        """
        provider_val = provider or settings.default_llm_provider
        self.provider = LLMProvider(provider_val)
        self.api_key = api_key

        # Set default models
        if model:
            self.model = model
        elif self.provider == LLMProvider.GEMINI:
            self.model = settings.gemini_model
        elif self.provider == LLMProvider.PERPLEXITY:
            self.model = settings.perplexity_model
        else:
            self.model = settings.claude_model

        # Initialize provider client (Lazy initialization)
        self._client = None
        self._async_client = None

    def _init_client(self) -> None:
        """Initialize the provider-specific client."""
        if self._client is not None:
            return

        if self.provider == LLMProvider.GEMINI:
            self._init_gemini()
        elif self.provider == LLMProvider.PERPLEXITY:
            self._init_perplexity()
        else:
            self._init_claude()

    def _init_async_client(self) -> None:
        """Initialize the provider-specific async client."""
        if self._async_client is not None:
            return
            
        if self.provider == LLMProvider.CLAUDE:
            from anthropic import AsyncAnthropic
            api_key = self.api_key or settings.anthropic_api_key
            self._async_client = AsyncAnthropic(api_key=api_key)
        elif self.provider == LLMProvider.GEMINI:
            # Gemini's main client handles async via generate_content_async
            self._init_gemini()
            self._async_client = self._client
        elif self.provider == LLMProvider.PERPLEXITY:
            self._init_perplexity()
            self._async_client = self._client

    def _init_gemini(self) -> None:
        """Initialize Google Gemini client."""
        api_key = self.api_key or settings.google_api_key
        if not api_key:
            logger.warning("GOOGLE_API_KEY not set")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._client = genai.GenerativeModel(self.model)
            logger.info(f"Gemini client initialized with model: {self.model}")
        except ImportError:
            logger.error("google-generativeai not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    def _init_claude(self) -> None:
        """Initialize Anthropic Claude client."""
        api_key = self.api_key or settings.anthropic_api_key
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set")
            return

        try:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=api_key)
            logger.info(f"Claude client initialized with model: {self.model}")
        except ImportError:
            logger.error("anthropic not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Claude: {e}")

    def _init_perplexity(self) -> None:
        """Initialize Perplexity (OpenAI-compatible) client."""
        api_key = self.api_key or settings.perplexity_api_key
        if not api_key:
            logger.warning("PERPLEXITY_API_KEY not set")
            return

        try:
            # Perplexity uses OpenAI-compatible API
            self._client = httpx.Client(
                base_url="https://api.perplexity.ai",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30.0
            )
            logger.info(f"Perplexity client initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity: {e}")

    def is_available(self) -> bool:
        """Check if the client is properly initialized."""
        self._init_client()
        return self._client is not None

    def get_langchain_model(self, **kwargs) -> "BaseChatModel":
        """
        Returns a LangChain-compatible chat model instance.
        """
        temperature = kwargs.get("temperature", 0.0)
        
        if self.provider == LLMProvider.GEMINI:
            from langchain_google_genai import ChatGoogleGenerativeAI
            if not settings.google_api_key:
                 raise ValueError("GOOGLE_API_KEY not found in settings")
            return ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=settings.google_api_key,
                temperature=temperature,
                convert_system_message_to_human=True,
                **{k: v for k, v in kwargs.items() if k != "temperature"}
            )
        elif self.provider == LLMProvider.CLAUDE:
            from langchain_anthropic import ChatAnthropic
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in settings")
            return ChatAnthropic(
                model=self.model,
                anthropic_api_key=settings.anthropic_api_key,
                temperature=temperature,
                **{k: v for k, v in kwargs.items() if k != "temperature"}
            )
        raise ValueError(f"Unsupported provider: {self.provider}")

    def chat_sync(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Chat-style synchronous generation.
        """
        prompt = messages[-1]["content"]
        history = messages[:-1]
        return self.generate(
            prompt=prompt,
            system_prompt=system,
            history=history,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Chat-style asynchronous generation.
        """
        prompt = messages[-1]["content"]
        history = messages[:-1]
        return await self.agenerate(
            prompt=prompt,
            system_prompt=system,
            history=history,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        response_schema: Optional[Any] = None,
        cached_content: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM (Synchronous)."""
        if not self.is_available():
            raise RuntimeError(f"{self.provider.value} client not initialized")

        if self.provider == LLMProvider.GEMINI:
            return self._generate_gemini(
                prompt, system_prompt, history, max_tokens, temperature, 
                response_schema=response_schema, cached_content=cached_content, 
                tools=tools, **kwargs
            )
        elif self.provider == LLMProvider.PERPLEXITY:
            return self._generate_perplexity(prompt, system_prompt, history, max_tokens, temperature)
        else:
            return self._generate_claude(prompt, system_prompt, history, max_tokens, temperature)

    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        response_schema: Optional[Any] = None,
        cached_content: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM (Asynchronous)."""
        self._init_async_client()
        if not self._async_client:
            raise RuntimeError(f"{self.provider.value} async client not initialized")

        if self.provider == LLMProvider.GEMINI:
            # Gemini history handling
            full_prompt = f"{system_prompt}\n\n" if system_prompt else ""
            if history:
                for msg in history:
                    full_prompt += f"{msg['role']}: {msg['content']}\n"
            full_prompt += f"user: {prompt}"
            
            gen_config = {"max_output_tokens": max_tokens, "temperature": temperature}
            
            if response_schema:
                gen_config["response_mime_type"] = "application/json"
                gen_config["response_schema"] = response_schema

            # Create model instance with tools if provided
            import google.generativeai as genai
            model = genai.GenerativeModel(model=self.model, tools=tools)
            
            if cached_content:
                from google.generativeai import caching
                cache = caching.CachedContent.get(cached_content)
                response = await model.generate_content_async(
                    full_prompt,
                    generation_config=gen_config,
                    cached_content=cache
                )
            else:
                response = await model.generate_content_async(
                    full_prompt,
                    generation_config=gen_config
                )
            
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', None) if hasattr(response, 'usage_metadata') else None
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', None) if hasattr(response, 'usage_metadata') else None
            
            return LLMResponse(
                content=response.text,
                provider=self.provider,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                tokens_used=(input_tokens + output_tokens) if input_tokens and output_tokens else None,
                finish_reason=response.candidates[0].finish_reason.name if response.candidates else None
            )
        elif self.provider == LLMProvider.PERPLEXITY:
            return await self._agenerate_perplexity(prompt, system_prompt, history, max_tokens, temperature)
        else:
            messages = history.copy() if history else []
            messages.append({"role": "user", "content": prompt})
            
            response = await self._async_client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "You are a helpful AI assistant.",
                messages=messages
            )
            
            input_tokens = response.usage.input_tokens if hasattr(response, 'usage') else None
            output_tokens = response.usage.output_tokens if hasattr(response, 'usage') else None
            
            return LLMResponse(
                content=response.content[0].text,
                provider=self.provider,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                tokens_used=(input_tokens + output_tokens) if input_tokens and output_tokens else None,
                finish_reason=response.stop_reason
            )

    async def generate_strategic_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Generate a high-level strategic response using Claude 3.5 Sonnet.
        Tailored for CEO and Executive decision support.
        """
        system_prompt = """
        You are the Strategic Intelligence AI for a Global Fortune 500 company.
        Your goal is to provide high-stakes, actionable strategic advice based on competitive intelligence.
        Focus on:
        - ROI Impact
        - Risk Mitigation
        - Long-term competitive advantage
        - Regulatory compliance
        
        Keep responses concise, executive-focused, and ready for immediate implementation.
        """
        
        # Ensure we use Claude 3.5 Sonnet for strategic tasks if available
        original_model = self.model
        if self.provider == LLMProvider.CLAUDE:
            self.model = "claude-3-5-sonnet-20241022"
            
        try:
            response = await self.agenerate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2, # Low temperature for consistent strategic advice
                max_tokens=1024
            )
            return response.content
        finally:
            self.model = original_model

    async def astream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream response chunks from the LLM (Asynchronous).
        """
        self._init_async_client()
        if not self._async_client:
            raise RuntimeError(f"{self.provider.value} async client not initialized")
            
        if self.provider == LLMProvider.GEMINI:
             full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
             response = await self._async_client.generate_content_async(full_prompt, stream=True)
             async for chunk in response:
                 if chunk.text:
                     yield chunk.text
        else:
            async with self._async_client.messages.stream(
                model=self.model,
                max_tokens=2048,
                system=system_prompt or "You are a helpful AI assistant.",
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                async for text in stream.text_stream:
                    yield text

    def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        history: Optional[list[dict[str, str]]],
        max_tokens: int,
        temperature: float,
        response_schema: Optional[Any] = None,
        cached_content: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Gemini."""
        full_prompt = f"{system_prompt}\n\n" if system_prompt else ""
        if history:
            for msg in history:
                full_prompt += f"{msg['role']}: {msg['content']}\n"
        full_prompt += f"user: {prompt}"

        gen_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature
        }
        
        if response_schema:
            gen_config["response_mime_type"] = "application/json"
            gen_config["response_schema"] = response_schema

        import google.generativeai as genai
        model = genai.GenerativeModel(model=self.model, tools=tools)
        
        if cached_content:
            from google.generativeai import caching
            cache = caching.CachedContent.get(cached_content)
            response = model.generate_content(
                full_prompt,
                generation_config=gen_config,
                cached_content=cache
            )
        else:
            response = model.generate_content(
                full_prompt,
                generation_config=gen_config
            )

        input_tokens = getattr(response.usage_metadata, 'prompt_token_count', None) if hasattr(response, 'usage_metadata') else None
        output_tokens = getattr(response.usage_metadata, 'candidates_token_count', None) if hasattr(response, 'usage_metadata') else None

        return LLMResponse(
            content=response.text,
            provider=self.provider,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tokens_used=(input_tokens + output_tokens) if input_tokens and output_tokens else None,
            finish_reason=response.candidates[0].finish_reason.name if response.candidates else None
        )

    def create_context_cache(
        self,
        content: str,
        display_name: str,
        ttl_minutes: int = 60,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Create a Gemini context cache for large datasets.
        
        Args:
            content: The text content to cache.
            display_name: Human-readable name for the cache.
            ttl_minutes: Time-to-live in minutes.
            system_instruction: Optional system instruction to bake into the cache.
            
        Returns:
            The name of the created cache (e.g., 'cachedContents/xyz').
        """
        if self.provider != LLMProvider.GEMINI:
            raise ValueError("Context caching is only supported for Gemini")
            
        import google.generativeai as genai
        from google.generativeai import caching
        import datetime
        
        # Ensure genai is configured
        api_key = self.api_key or settings.google_api_key
        genai.configure(api_key=api_key)
        
        cache = caching.CachedContent.create(
            model=self.model,
            display_name=display_name,
            system_instruction=system_instruction,
            contents=[content],
            ttl=datetime.timedelta(minutes=ttl_minutes),
        )
        
        logger.info(f"Created Gemini context cache: {cache.name} ({display_name})")
        return cache.name

    def _generate_claude(
        self,
        prompt: str,
        system_prompt: Optional[str],
        history: Optional[list[dict[str, str]]],
        max_tokens: int,
        temperature: float
    ) -> LLMResponse:
        """Generate response using Claude."""
        messages = history.copy() if history else []
        messages.append({"role": "user", "content": prompt})

        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "You are a helpful AI assistant.",
            messages=messages
        )

        input_tokens = response.usage.input_tokens if hasattr(response, 'usage') else None
        output_tokens = response.usage.output_tokens if hasattr(response, 'usage') else None

        return LLMResponse(
            content=response.content[0].text,
            provider=self.provider,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tokens_used=(input_tokens + output_tokens) if input_tokens and output_tokens else None,
            finish_reason=response.stop_reason
        )

    def _generate_perplexity(
        self,
        prompt: str,
        system_prompt: Optional[str],
        history: Optional[list[dict[str, str]]],
        max_tokens: int,
        temperature: float
    ) -> LLMResponse:
        """Generate response using Perplexity (OpenAI-compatible)."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        response = self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens")
        output_tokens = usage.get("completion_tokens")

        return LLMResponse(
            content=content,
            provider=self.provider,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tokens_used=(input_tokens + output_tokens) if input_tokens and output_tokens else None,
            finish_reason=data["choices"][0].get("finish_reason")
        )

    async def _agenerate_perplexity(
        self,
        prompt: str,
        system_prompt: Optional[str],
        history: Optional[list[dict[str, str]]],
        max_tokens: int,
        temperature: float
    ) -> LLMResponse:
        """Generate response using Perplexity asynchronously."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        api_key = self.api_key or settings.perplexity_api_key
        async with httpx.AsyncClient(
            base_url="https://api.perplexity.ai",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        ) as client:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens")
        output_tokens = usage.get("completion_tokens")

        return LLMResponse(
            content=content,
            provider=self.provider,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tokens_used=(input_tokens + output_tokens) if input_tokens and output_tokens else None,
            finish_reason=data["choices"][0].get("finish_reason")
        )

    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream response chunks from the LLM."""
        if not self.is_available():
            raise RuntimeError(f"{self.provider.value} client not initialized")

        if self.provider == LLMProvider.GEMINI:
            yield from self._stream_gemini(prompt, system_prompt)
        else:
            yield from self._stream_claude(prompt, system_prompt)

    def _stream_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str]
    ) -> Generator[str, None, None]:
        """Stream response from Gemini."""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = self._client.generate_content(full_prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text

    def _stream_claude(
        self,
        prompt: str,
        system_prompt: Optional[str]
    ) -> Generator[str, None, None]:
        """Stream response from Claude."""
        with self._client.messages.stream(
            model=self.model,
            max_tokens=2048,
            system=system_prompt or "You are a helpful AI assistant.",
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text


def get_available_providers() -> Dict[str, bool]:
    """Check which LLM providers are available."""
    providers = {}
    providers["gemini"] = bool(settings.google_api_key)
    providers["claude"] = bool(settings.anthropic_api_key and settings.anthropic_api_key.startswith("sk-ant-"))
    providers["perplexity"] = bool(settings.perplexity_api_key)
    return providers


def get_llm_client() -> LLMClient:
    """Get a default LLM client instance."""
    # TODO: Implement proper singleton or factory pattern
    return LLMClient(provider=LLMProvider.CLAUDE)
# Backward compatibility alias
AIClient = LLMClient

