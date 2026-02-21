"""Tests for RAG billing and usage tracking."""

from unittest.mock import AsyncMock

import pytest
from shared_schemas import UsageEvent, UsageEventType

from rag_service.billing.stripe_service import RAGBillingService


@pytest.fixture
def mock_stripe_billing():
    """Mock Stripe billing service."""
    stripe = AsyncMock()
    stripe.report_usage = AsyncMock(return_value={"id": "evt_123", "status": "success"})
    stripe.create_subscription = AsyncMock(return_value={"id": "sub_123", "status": "active"})
    stripe.create_checkout_session = AsyncMock(
        return_value="https://checkout.stripe.com/session123"
    )
    return stripe


@pytest.fixture
def billing_service(mock_stripe_billing):
    """RAG billing service with mock Stripe."""
    return RAGBillingService(stripe_billing=mock_stripe_billing)


@pytest.fixture
def billing_service_no_stripe():
    """RAG billing service without Stripe (standalone mode)."""
    return RAGBillingService(stripe_billing=None)


class TestRAGBillingService:
    """Test RAG billing integration with Stripe."""

    async def test_report_query_usage(self, billing_service, mock_stripe_billing):
        """Test reporting RAG query usage to Stripe."""
        # Act
        result = await billing_service.report_query_usage(tenant_id="tenant-123", query_count=5)

        # Assert
        assert result is not None
        assert result["status"] == "success"
        mock_stripe_billing.report_usage.assert_called_once()

        # Verify usage event structure
        call_args = mock_stripe_billing.report_usage.call_args
        event = call_args[0][0]
        assert isinstance(event, UsageEvent)
        assert event.tenant_id == "tenant-123"
        assert event.event_type == UsageEventType.RAG_QUERY
        assert event.quantity == 5
        assert event.metadata["service"] == "rag-as-a-service"

    async def test_report_single_query(self, billing_service, mock_stripe_billing):
        """Test reporting single query usage (default)."""
        # Act
        result = await billing_service.report_query_usage(tenant_id="tenant-456")

        # Assert
        call_args = mock_stripe_billing.report_usage.call_args
        event = call_args[0][0]
        assert event.quantity == 1

    async def test_report_usage_without_stripe(self, billing_service_no_stripe):
        """Test that usage reporting is skipped without Stripe."""
        # Act
        result = await billing_service_no_stripe.report_query_usage(
            tenant_id="tenant-123", query_count=10
        )

        # Assert
        assert result is None

    async def test_report_usage_handles_stripe_error(self, billing_service, mock_stripe_billing):
        """Test graceful handling of Stripe errors."""
        # Arrange
        mock_stripe_billing.report_usage = AsyncMock(side_effect=Exception("Stripe API error"))

        # Act
        result = await billing_service.report_query_usage(tenant_id="tenant-123", query_count=1)

        # Assert
        assert result is None  # Should not raise, returns None on error

    async def test_create_subscription_starter(self, billing_service, mock_stripe_billing):
        """Test creating a starter tier subscription."""
        # Act
        result = await billing_service.create_subscription(customer_id="cus_123", tier="starter")

        # Assert
        assert result is not None
        assert result["status"] == "active"
        mock_stripe_billing.create_subscription.assert_called_once_with(
            "cus_123", "price_starter_rag"
        )

    async def test_create_subscription_pro(self, billing_service, mock_stripe_billing):
        """Test creating a pro tier subscription."""
        # Act
        result = await billing_service.create_subscription(customer_id="cus_456", tier="pro")

        # Assert
        mock_stripe_billing.create_subscription.assert_called_once_with("cus_456", "price_pro_rag")

    async def test_create_subscription_business(self, billing_service, mock_stripe_billing):
        """Test creating a business tier subscription."""
        # Act
        result = await billing_service.create_subscription(customer_id="cus_789", tier="business")

        # Assert
        mock_stripe_billing.create_subscription.assert_called_once_with(
            "cus_789", "price_business_rag"
        )

    async def test_create_subscription_invalid_tier(self, billing_service):
        """Test creating subscription with invalid tier."""
        # Act & Assert
        with pytest.raises(ValueError, match="Unknown tier"):
            await billing_service.create_subscription(customer_id="cus_123", tier="invalid")

    async def test_create_subscription_without_stripe(self, billing_service_no_stripe):
        """Test creating subscription without Stripe returns None."""
        # Act
        result = await billing_service_no_stripe.create_subscription(
            customer_id="cus_123", tier="starter"
        )

        # Assert
        assert result is None

    async def test_get_checkout_url_starter(self, billing_service, mock_stripe_billing):
        """Test generating Stripe checkout URL for starter tier."""
        # Act
        url = await billing_service.get_checkout_url(
            customer_id="cus_123",
            tier="starter",
            success_url="https://app.example.com/success",
            cancel_url="https://app.example.com/cancel",
        )

        # Assert
        assert url == "https://checkout.stripe.com/session123"
        mock_stripe_billing.create_checkout_session.assert_called_once_with(
            "cus_123",
            "price_starter_rag",
            "https://app.example.com/success",
            "https://app.example.com/cancel",
        )

    async def test_get_checkout_url_pro(self, billing_service, mock_stripe_billing):
        """Test generating checkout URL for pro tier."""
        # Act
        url = await billing_service.get_checkout_url(
            customer_id="cus_456",
            tier="pro",
        )

        # Assert
        assert url is not None
        call_args = mock_stripe_billing.create_checkout_session.call_args
        assert call_args[0][1] == "price_pro_rag"

    async def test_get_checkout_url_business(self, billing_service, mock_stripe_billing):
        """Test generating checkout URL for business tier."""
        # Act
        url = await billing_service.get_checkout_url(
            customer_id="cus_789",
            tier="business",
        )

        # Assert
        assert url is not None
        call_args = mock_stripe_billing.create_checkout_session.call_args
        assert call_args[0][1] == "price_business_rag"

    async def test_get_checkout_url_invalid_tier(self, billing_service):
        """Test checkout URL with invalid tier."""
        # Act & Assert
        with pytest.raises(ValueError, match="Unknown tier"):
            await billing_service.get_checkout_url(customer_id="cus_123", tier="enterprise")

    async def test_get_checkout_url_without_stripe(self, billing_service_no_stripe):
        """Test checkout URL generation without Stripe."""
        # Act
        url = await billing_service_no_stripe.get_checkout_url(
            customer_id="cus_123", tier="starter"
        )

        # Assert
        assert url is None


class TestUsageTracking:
    """Test usage tracking patterns."""

    async def test_batch_usage_reporting(self, billing_service, mock_stripe_billing):
        """Test reporting usage in batches."""
        # Act - report 3 separate query batches
        await billing_service.report_query_usage("tenant-1", query_count=10)
        await billing_service.report_query_usage("tenant-1", query_count=5)
        await billing_service.report_query_usage("tenant-1", query_count=3)

        # Assert
        assert mock_stripe_billing.report_usage.call_count == 3

    async def test_multi_tenant_usage(self, billing_service, mock_stripe_billing):
        """Test tracking usage across multiple tenants."""
        # Act
        await billing_service.report_query_usage("tenant-1", query_count=10)
        await billing_service.report_query_usage("tenant-2", query_count=5)
        await billing_service.report_query_usage("tenant-3", query_count=1)

        # Assert
        assert mock_stripe_billing.report_usage.call_count == 3
        calls = mock_stripe_billing.report_usage.call_args_list
        tenant_ids = [call[0][0].tenant_id for call in calls]
        assert "tenant-1" in tenant_ids
        assert "tenant-2" in tenant_ids
        assert "tenant-3" in tenant_ids


class TestBillingIntegration:
    """Integration-style tests for billing workflow."""

    async def test_subscription_lifecycle(self, billing_service, mock_stripe_billing):
        """Test complete subscription lifecycle."""
        # 1. Get checkout URL
        checkout_url = await billing_service.get_checkout_url(customer_id="cus_new", tier="pro")
        assert checkout_url is not None

        # 2. Create subscription (after checkout)
        subscription = await billing_service.create_subscription(customer_id="cus_new", tier="pro")
        assert subscription["status"] == "active"

        # 3. Report usage
        usage = await billing_service.report_query_usage(tenant_id="tenant-new", query_count=100)
        assert usage is not None

    async def test_tier_upgrade_workflow(self, billing_service, mock_stripe_billing):
        """Test workflow for tier upgrade."""
        # Start with starter tier
        await billing_service.create_subscription(customer_id="cus_123", tier="starter")

        # Upgrade to pro
        upgrade_url = await billing_service.get_checkout_url(customer_id="cus_123", tier="pro")

        assert upgrade_url is not None
        # Should generate checkout for pro tier
        call_args = mock_stripe_billing.create_checkout_session.call_args
        assert "price_pro_rag" in call_args[0]
