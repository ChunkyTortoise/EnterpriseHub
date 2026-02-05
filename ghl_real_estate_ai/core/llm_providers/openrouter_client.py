"""
OpenRouter API Client for EnterpriseHub.

Provides unified access to multiple LLM providers (Claude, GPT-4, Gemini, Llama, etc.)
through the OpenRouter API with support for cost tracking, fallbacks, and model routing.
"""
import httpx
import json
import logging
from typing import Optional, Dict, Any, List, AsyncIterator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OpenRouterUsage:
    """Usage and cost information from OpenRouter API."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    generation_cost: float = 0.0
    total_cost: float = 0.0
    model: str = ""


class OpenRouterClient:
    """
    OpenRouter API client with streaming support, cost tracking, and automatic fallbacks.
    
    Features:
    - Unified access to 100+ LLM models
    - Automatic cost tracking via response headers
    - Model fallback on errors
    - Streaming and non-streaming responses
    - Compatible with existing LLMClient interface
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(
        self,
        api_key: str,
        default_model: str = "anthropic/claude-3.5-sonnet",
        app_name: str = "EnterpriseHub-Real-Estate-AI",
        fallback_models: Optional[List[str]] = None,
        enable_cost_tracking: bool = True,
        timeout: int = 120
    ):
        """
        Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key
            default_model: Default model in format "provider/model-name"
            app_name: App name for OpenRouter analytics
            fallback_models: List of fallback models to try on error
            enable_cost_tracking: Track costs via response headers
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.default_model = default_model
        self.app_name = app_name
        self.fallback_models = fallback_models or []
        self.enable_cost_tracking = enable_cost_tracking
        self.timeout = timeout
        
        # Track cumulative costs
        self.total_cost = 0.0
        self.request_count = 0
        
        logger.info(
            f"OpenRouter client initialized: model={default_model}, "
            f"fallbacks={len(self.fallback_models)}, cost_tracking={enable_cost_tracking}"
        )
    
    def _get_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get request headers including authentication."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://enterprisehub.ai",  # For rankings
            "X-Title": self.app_name,
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers
    
    def _extract_cost_from_headers(self, headers: httpx.Headers) -> Dict[str, float]:
        """Extract cost information from OpenRouter response headers."""
        try:
            generation_cost = float(headers.get("x-openrouter-generation-cost", 0))
            total_cost = float(headers.get("x-openrouter-total-cost", 0))
            
            if self.enable_cost_tracking:
                self.total_cost += generation_cost
                
            return {
                "generation_cost": generation_cost,
                "total_cost": total_cost
            }
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to extract cost from headers: {e}")
            return {"generation_cost": 0.0, "total_cost": 0.0}
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a completion using OpenRouter API.
        
        Args:
            prompt: User prompt
            model: Model to use (overrides default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Dict with 'content', 'usage', and 'cost' keys
        """
        model_to_use = model or self.default_model
        models_to_try = [model_to_use] + self.fallback_models
        
        for attempt, current_model in enumerate(models_to_try):
            try:
                logger.debug(f"Attempting generation with model: {current_model}")
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": current_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
                
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.BASE_URL}/chat/completions",
                        headers=self._get_headers(),
                        json=payload
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    cost_info = self._extract_cost_from_headers(response.headers)
                    
                    self.request_count += 1
                    
                    # Extract response
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    
                    result = {
                        "content": content,
                        "model": current_model,
                        "usage": OpenRouterUsage(
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            total_tokens=usage.get("total_tokens", 0),
                            generation_cost=cost_info["generation_cost"],
                            total_cost=cost_info["total_cost"],
                            model=current_model
                        ),
                        "raw_response": data
                    }
                    
                    logger.info(
                        f"✓ OpenRouter generation successful: model={current_model}, "
                        f"tokens={usage.get('total_tokens', 0)}, cost=${cost_info['generation_cost']:.4f}"
                    )
                    
                    return result
                    
            except httpx.HTTPError as e:
                logger.warning(
                    f"OpenRouter API error with {current_model} (attempt {attempt + 1}/{len(models_to_try)}): {e}"
                )
                
                if attempt == len(models_to_try) - 1:
                    # Last attempt failed
                    raise Exception(f"All OpenRouter models failed. Last error: {e}")
                else:
                    logger.info(f"Trying fallback model: {models_to_try[attempt + 1]}")
                    continue
                    
            except Exception as e:
                logger.error(f"Unexpected error in OpenRouter generation: {e}")
                if attempt == len(models_to_try) - 1:
                    raise
                continue
        
        raise Exception("OpenRouter generation failed with all available models")
    
    async def generate_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Async version of generate()."""
        model_to_use = model or self.default_model
        models_to_try = [model_to_use] + self.fallback_models
        
        for attempt, current_model in enumerate(models_to_try):
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": current_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.BASE_URL}/chat/completions",
                        headers=self._get_headers(),
                        json=payload
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    cost_info = self._extract_cost_from_headers(response.headers)
                    
                    self.request_count += 1
                    
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    
                    return {
                        "content": content,
                        "model": current_model,
                        "usage": OpenRouterUsage(
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            total_tokens=usage.get("total_tokens", 0),
                            generation_cost=cost_info["generation_cost"],
                            total_cost=cost_info["total_cost"],
                            model=current_model
                        ),
                        "raw_response": data
                    }
                    
            except httpx.HTTPError as e:
                if attempt == len(models_to_try) - 1:
                    raise Exception(f"All OpenRouter models failed. Last error: {e}")
                continue
            except Exception as e:
                if attempt == len(models_to_try) - 1:
                    raise
                continue
        
        raise Exception("OpenRouter generation failed with all available models")
    
    async def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream completions from OpenRouter API.
        
        Args:
            prompt: User prompt
            model: Model to use (overrides default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Yields:
            Content chunks as they arrive
        """
        model_to_use = model or self.default_model
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model_to_use,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=self._get_headers(),
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_requests": self.request_count,
            "total_cost": self.total_cost,
            "default_model": self.default_model,
            "fallback_models": self.fallback_models,
            "avg_cost_per_request": self.total_cost / self.request_count if self.request_count > 0 else 0.0
        }
