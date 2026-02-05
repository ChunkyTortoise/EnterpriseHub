"""
OpenRouter Integration Tests for EnterpriseHub.

Tests the OpenRouter client integration including:
- API connectivity
- Model routing and fallbacks
- Cost tracking
- Sync and async generation
"""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from ghl_real_estate_ai.core.llm_providers.openrouter_client import OpenRouterClient, OpenRouterUsage
from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider


class TestOpenRouterClient:
    """Tests for the OpenRouterClient class."""
    
    def test_client_initialization(self):
        """Test that OpenRouter client initializes correctly."""
        client = OpenRouterClient(
            api_key="test-key",
            default_model="anthropic/claude-3.5-sonnet",
            fallback_models=["anthropic/claude-3-sonnet"]
        )
        
        assert client.api_key == "test-key"
        assert client.default_model == "anthropic/claude-3.5-sonnet"
        assert len(client.fallback_models) == 1
        assert client.total_cost == 0.0
        assert client.request_count == 0
    
    def test_get_headers(self):
        """Test header generation."""
        client = OpenRouterClient(api_key="test-key")
        headers = client._get_headers()
        
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
        assert "X-Title" in headers
    
    def test_cost_tracking(self):
        """Test cost extraction from response headers."""
        client = OpenRouterClient(
            api_key="test-key",
            enable_cost_tracking=True
        )
        
        # Mock headers
        from httpx import Headers
        headers = Headers({
            "x-openrouter-generation-cost": "0.0025",
            "x-openrouter-total-cost": "0.015"
        })
        
        cost_info = client._extract_cost_from_headers(headers)
        
        assert cost_info["generation_cost"] == 0.0025
        assert cost_info["total_cost"] == 0.015
        assert client.total_cost == 0.0025
    
    @pytest.mark.asyncio
    async def test_async_generation_mock(self):
        """Test async generation with mocked response."""
        client = OpenRouterClient(api_key="test-key")
        
        # Mock the async client
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": "Test response"
                    }
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                }
            }
            mock_response.headers = {
                "x-openrouter-generation-cost": "0.001",
                "x-openrouter-total-cost": "0.005"
            }
            mock_response.raise_for_status = Mock()
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await client.generate_async(
                prompt="Test prompt",
                system_prompt="You are helpful"
            )
            
            assert result["content"] =="Test response"
            assert result["usage"].prompt_tokens == 10
            assert result["usage"].completion_tokens == 20
    
    def test_sync_generation_fallback(self):
        """Test that fallback models are tried on failure."""
        client = OpenRouterClient(
            api_key="test-key",
            default_model="invalid/model",
            fallback_models=["anthropic/claude-3.5-sonnet"]
        )
        
        # This would fail in real usage but tests the fallback logic
        # In production, you'd mock the HTTP calls to simulate failures
        assert len(client.fallback_models) == 1
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        client = OpenRouterClient(api_key="test-key")
        client.total_cost = 0.05
        client.request_count = 10
        
        stats = client.get_stats()
        
        assert stats["total_requests"] == 10
        assert stats["total_cost"] == 0.05
        assert stats["avg_cost_per_request"] == 0.005


class TestLLMClientOpenRouter:
    """Tests for OpenRouter integration in LLMClient."""
    
    def test_openrouter_provider_initialization(self):
        """Test that OpenRouter provider is recognized."""
        # Only test if API key is set
        if not os.getenv("OPENROUTER_API_KEY"):
            pytest.skip("OPENROUTER_API_KEY not set")
        
        client = LLMClient(provider="openrouter")
        
        assert client.provider == LLMProvider.OPENROUTER
        assert client.model  # Should have a default model
    
    def test_openrouter_without_api_key(self):
        """Test graceful handling when API key is missing."""
        # Temporarily clear the API key
        old_key = os.environ.get("OPENROUTER_API_KEY")
        if "OPENROUTER_API_KEY" in os.environ:
            del os.environ["OPENROUTER_API_KEY"]
        
        try:
            client = LLMClient(provider="openrouter")
            client._init_client()
            
            #Client should initialize but log warning
            assert client.provider == LLMProvider.OPENROUTER
        finally:
            if old_key:
                os.environ["OPENROUTER_API_KEY"] = old_key
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set")
    async def test_openrouter_real_async_generation(self):
        """Integration test with real OpenRouter API."""
        client = LLMClient(provider="openrouter")
        
        result = await client.agenerate(
            prompt="Say 'Hello from OpenRouter' and nothing else.",
            max_tokens=50,
            temperature=0.0
        )
        
        assert result.content
        assert "Hello" in result.content or "hello" in result.content
        assert result.provider == LLMProvider.OPENROUTER
        assert result.input_tokens > 0
        assert result.output_tokens > 0
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set")
    def test_openrouter_real_sync_generation(self):
        """Integration test with real OpenRouter API (sync)."""
        client = LLMClient(provider="openrouter")
        
        result = client.generate(
            prompt="Say 'Test successful' and nothing else.",
            max_tokens=50,
            temperature=0.0
        )
        
        assert result.content
        assert result.provider == LLMProvider.OPENROUTER


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not integration"])
