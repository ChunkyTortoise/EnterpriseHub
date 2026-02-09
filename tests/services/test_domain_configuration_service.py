import pytest
pytestmark = pytest.mark.integration

"""
Tests for Domain Configuration Service
Validates DNS/SSL automation and domain management functionality
for the white-label platform.
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
import pytest
import pytest_asyncio

from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.domain_configuration_service import (

@pytest.mark.integration
    DNSProvider,
    DNSRecord,
    DomainConfiguration,
    DomainConfigurationService,
    DomainType,
    SSLProvider,
    VerificationMethod,
)


@pytest_asyncio.fixture
async def mock_db_pool():
    """Mock database pool."""
    pool = AsyncMock(spec=asyncpg.Pool)
    return pool


@pytest_asyncio.fixture
async def mock_cache_service():
    """Mock cache service."""
    cache = AsyncMock(spec=CacheService)
    cache.get.return_value = None  # Default to cache miss
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


@pytest_asyncio.fixture
async def domain_service(mock_db_pool, mock_cache_service):
    """Create domain configuration service instance."""
    return DomainConfigurationService(mock_db_pool, mock_cache_service)


@pytest.fixture
def sample_domain_config():
    """Sample domain configuration for testing."""
    return DomainConfiguration(
        domain_id="domain_test_123",
        agency_id="agency_001",
        client_id="client_001",
        domain_name="test.example.com",
        subdomain="test",
        domain_type=DomainType.CLIENT,
        dns_provider=DNSProvider.CLOUDFLARE,
        dns_zone_id="zone_123",
        dns_records=[],
        ssl_provider=SSLProvider.LETSENCRYPT,
        verification_method=VerificationMethod.DNS,
        created_at=datetime.utcnow(),
    )


class TestDomainConfigurationService:
    """Test suite for domain configuration service."""

    @pytest.mark.asyncio
    async def test_create_domain_configuration_success(self, domain_service, mock_db_pool):
        """Test successful domain configuration creation."""
        # Mock database responses
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock
        conn_mock.fetchrow.return_value = None  # No existing domain
        conn_mock.execute = AsyncMock()

        # Mock DNS validation
        with patch.object(domain_service, "_validate_domain_name", return_value=True):
            with patch.object(domain_service, "get_domain_by_name", return_value=None):
                with patch.object(domain_service, "_save_domain_configuration") as mock_save:
                    with patch.object(domain_service, "initiate_domain_verification") as mock_verify:
                        result = await domain_service.create_domain_configuration(
                            agency_id="agency_001",
                            domain_name="test.example.com",
                            domain_type=DomainType.CLIENT,
                            client_id="client_001",
                            dns_provider=DNSProvider.CLOUDFLARE,
                        )

                        assert result.agency_id == "agency_001"
                        assert result.domain_name == "test.example.com"
                        assert result.domain_type == DomainType.CLIENT
                        assert result.client_id == "client_001"
                        assert result.dns_provider == DNSProvider.CLOUDFLARE
                        assert result.domain_id.startswith("domain_")

                        mock_save.assert_called_once()
                        mock_verify.assert_called_once_with(result.domain_id)

    @pytest.mark.asyncio
    async def test_create_domain_configuration_duplicate_domain(self, domain_service, sample_domain_config):
        """Test domain configuration creation with duplicate domain."""
        with patch.object(domain_service, "_validate_domain_name", return_value=True):
            with patch.object(domain_service, "get_domain_by_name", return_value=sample_domain_config):
                with pytest.raises(ValueError, match="already configured"):
                    await domain_service.create_domain_configuration(
                        agency_id="agency_001",
                        domain_name="test.example.com",
                        domain_type=DomainType.CLIENT,
                        client_id="client_001",
                    )

    @pytest.mark.asyncio
    async def test_create_domain_configuration_invalid_domain(self, domain_service):
        """Test domain configuration creation with invalid domain name."""
        with patch.object(domain_service, "_validate_domain_name", side_effect=ValueError("Invalid domain")):
            with pytest.raises(ValueError, match="Invalid domain"):
                await domain_service.create_domain_configuration(
                    agency_id="agency_001",
                    domain_name="invalid..domain",
                    domain_type=DomainType.CLIENT,
                    client_id="client_001",
                )

    @pytest.mark.asyncio
    async def test_get_domain_configuration_from_cache(self, domain_service, mock_cache_service, sample_domain_config):
        """Test getting domain configuration from cache."""
        # Setup cache hit
        mock_cache_service.get.return_value = json.dumps(
            {
                "domain_id": "domain_test_123",
                "agency_id": "agency_001",
                "client_id": "client_001",
                "domain_name": "test.example.com",
                "subdomain": "test",
                "domain_type": "client",
                "dns_provider": "cloudflare",
                "dns_zone_id": "zone_123",
                "dns_records": [],
                "ssl_enabled": True,
                "ssl_provider": "letsencrypt",
                "ssl_cert_status": "pending",
                "ssl_cert_expires_at": None,
                "ssl_auto_renew": True,
                "cdn_enabled": False,
                "cdn_provider": None,
                "cdn_distribution_id": None,
                "cdn_endpoint": None,
                "verification_token": "test_token",
                "verification_status": "pending",
                "verification_method": "dns",
                "verified_at": None,
                "status": "pending",
                "health_check_url": None,
                "last_health_check": None,
                "health_status": "unknown",
                "configuration_metadata": {},
                "created_at": "2024-01-01T00:00:00",
                "updated_at": None,
            }
        )

        result = await domain_service.get_domain_configuration("domain_test_123")

        assert result is not None
        assert result.domain_id == "domain_test_123"
        assert result.agency_id == "agency_001"
        mock_cache_service.get.assert_called_once_with("domain_config:domain_test_123")

    @pytest.mark.asyncio
    async def test_get_domain_configuration_from_db(self, domain_service, mock_db_pool, mock_cache_service):
        """Test getting domain configuration from database when cache miss."""
        # Setup cache miss
        mock_cache_service.get.return_value = None

        # Mock database response
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock

        db_row = {
            "domain_id": "domain_test_123",
            "agency_id": "agency_001",
            "client_id": "client_001",
            "domain_name": "test.example.com",
            "subdomain": "test",
            "domain_type": "client",
            "dns_provider": "cloudflare",
            "dns_zone_id": "zone_123",
            "dns_records": "[]",
            "ssl_enabled": True,
            "ssl_provider": "letsencrypt",
            "ssl_cert_status": "pending",
            "ssl_cert_expires_at": None,
            "ssl_auto_renew": True,
            "cdn_enabled": False,
            "cdn_provider": None,
            "cdn_distribution_id": None,
            "cdn_endpoint": None,
            "verification_token": "test_token",
            "verification_status": "pending",
            "verification_method": "dns",
            "verified_at": None,
            "status": "pending",
            "health_check_url": None,
            "last_health_check": None,
            "health_status": "unknown",
            "configuration_metadata": "{}",
            "created_at": datetime.utcnow(),
            "updated_at": None,
        }

        conn_mock.fetchrow.return_value = db_row

        # Patch json.dumps in the service module to handle Enum serialization
        original_json_dumps = json.dumps

        def _enum_json_dumps(obj, **kwargs):
            return original_json_dumps(obj, default=str, **kwargs)

        with patch("ghl_real_estate_ai.services.domain_configuration_service.json.dumps", side_effect=_enum_json_dumps):
            result = await domain_service.get_domain_configuration("domain_test_123")

        assert result is not None
        assert result.domain_id == "domain_test_123"
        assert result.domain_type == DomainType.CLIENT

        # Verify cache was set
        mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_agency_domains(self, domain_service, mock_db_pool):
        """Test listing domains for an agency."""
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock

        # Mock database response with multiple domains
        db_rows = [
            {
                "domain_id": "domain_001",
                "agency_id": "agency_001",
                "client_id": None,
                "domain_name": "agency.example.com",
                "subdomain": None,
                "domain_type": "agency",
                "dns_provider": "cloudflare",
                "dns_zone_id": "zone_001",
                "dns_records": "[]",
                "ssl_enabled": True,
                "ssl_provider": "letsencrypt",
                "ssl_cert_status": "issued",
                "ssl_cert_expires_at": None,
                "ssl_auto_renew": True,
                "cdn_enabled": True,
                "cdn_provider": "cloudflare",
                "cdn_distribution_id": None,
                "cdn_endpoint": None,
                "verification_token": "token_001",
                "verification_status": "verified",
                "verification_method": "dns",
                "verified_at": datetime.utcnow(),
                "status": "active",
                "health_check_url": None,
                "last_health_check": None,
                "health_status": "healthy",
                "configuration_metadata": "{}",
                "created_at": datetime.utcnow(),
                "updated_at": None,
            },
            {
                "domain_id": "domain_002",
                "agency_id": "agency_001",
                "client_id": "client_001",
                "domain_name": "client.agency.example.com",
                "subdomain": "client",
                "domain_type": "client",
                "dns_provider": "cloudflare",
                "dns_zone_id": "zone_001",
                "dns_records": "[]",
                "ssl_enabled": True,
                "ssl_provider": "letsencrypt",
                "ssl_cert_status": "issued",
                "ssl_cert_expires_at": None,
                "ssl_auto_renew": True,
                "cdn_enabled": False,
                "cdn_provider": None,
                "cdn_distribution_id": None,
                "cdn_endpoint": None,
                "verification_token": "token_002",
                "verification_status": "verified",
                "verification_method": "dns",
                "verified_at": datetime.utcnow(),
                "status": "active",
                "health_check_url": None,
                "last_health_check": None,
                "health_status": "healthy",
                "configuration_metadata": "{}",
                "created_at": datetime.utcnow(),
                "updated_at": None,
            },
        ]

        conn_mock.fetch.return_value = db_rows

        result = await domain_service.list_agency_domains("agency_001")

        assert len(result) == 2
        assert result[0].domain_type == DomainType.AGENCY
        assert result[1].domain_type == DomainType.CLIENT
        assert all(domain.agency_id == "agency_001" for domain in result)

    @pytest.mark.asyncio
    async def test_list_agency_domains_with_filters(self, domain_service, mock_db_pool):
        """Test listing agency domains with filters."""
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock
        conn_mock.fetch.return_value = []

        await domain_service.list_agency_domains("agency_001", domain_type=DomainType.CLIENT, status="active")

        # Verify correct query parameters were used
        call_args = conn_mock.fetch.call_args
        assert "agency_id = $1" in call_args[0][0]
        assert "domain_type = $2" in call_args[0][0]
        assert "status = $3" in call_args[0][0]
        assert call_args[0][1:] == ("agency_001", "client", "active")

    @pytest.mark.asyncio
    async def test_initiate_domain_verification_dns_success(self, domain_service, sample_domain_config):
        """Test successful DNS domain verification initiation."""
        with patch.object(domain_service, "get_domain_configuration", return_value=sample_domain_config):
            with patch.object(domain_service, "_update_domain_config") as mock_update:
                with patch.object(domain_service, "_verify_dns_ownership", return_value=True):
                    with patch.object(domain_service, "_mark_domain_verified") as mock_mark_verified:
                        with patch.object(domain_service, "provision_ssl_certificate") as mock_provision_ssl:
                            result = await domain_service.initiate_domain_verification("domain_test_123")

                            assert result is True
                            mock_mark_verified.assert_called_once_with("domain_test_123")
                            mock_provision_ssl.assert_called_once_with("domain_test_123")

    @pytest.mark.asyncio
    async def test_initiate_domain_verification_dns_failure(self, domain_service, sample_domain_config):
        """Test DNS domain verification failure."""
        with patch.object(domain_service, "get_domain_configuration", return_value=sample_domain_config):
            with patch.object(domain_service, "_verify_dns_ownership", return_value=False):
                result = await domain_service.initiate_domain_verification("domain_test_123")

                assert result is False

    @pytest.mark.asyncio
    async def test_initiate_domain_verification_domain_not_found(self, domain_service):
        """Test domain verification with non-existent domain."""
        with patch.object(domain_service, "get_domain_configuration", return_value=None):
            result = await domain_service.initiate_domain_verification("nonexistent_domain")

            assert result is False

    @pytest.mark.asyncio
    async def test_provision_ssl_certificate_letsencrypt_success(self, domain_service, sample_domain_config):
        """Test successful Let's Encrypt SSL certificate provisioning."""
        # Set domain as verified
        sample_domain_config.verification_status = "verified"

        with patch.object(domain_service, "get_domain_configuration", return_value=sample_domain_config):
            with patch.object(domain_service, "_provision_letsencrypt_certificate", return_value=True):
                with patch.object(domain_service, "_update_domain_config") as mock_update:
                    result = await domain_service.provision_ssl_certificate("domain_test_123")

                    assert result is True
                    mock_update.assert_called_once()

                    # Verify SSL status was updated
                    updated_config = mock_update.call_args[0][0]
                    assert updated_config.ssl_cert_status == "issued"
                    assert updated_config.ssl_cert_expires_at is not None

    @pytest.mark.asyncio
    async def test_provision_ssl_certificate_unverified_domain(self, domain_service, sample_domain_config):
        """Test SSL certificate provisioning for unverified domain."""
        # Keep domain as unverified
        sample_domain_config.verification_status = "pending"

        with patch.object(domain_service, "get_domain_configuration", return_value=sample_domain_config):
            result = await domain_service.provision_ssl_certificate("domain_test_123")

            assert result is False

    @pytest.mark.asyncio
    async def test_configure_dns_records(self, domain_service, sample_domain_config):
        """Test DNS records configuration."""
        dns_records = [
            DNSRecord(name="@", type="A", value="192.168.1.1", ttl=300),
            DNSRecord(name="www", type="CNAME", value="example.com", ttl=300),
            DNSRecord(name="@", type="TXT", value="v=spf1 include:_spf.google.com ~all", ttl=300),
        ]

        with patch.object(domain_service, "get_domain_configuration", return_value=sample_domain_config):
            with patch.object(domain_service, "_configure_cloudflare_dns", return_value=True) as mock_cf_dns:
                with patch.object(domain_service, "_update_domain_config") as mock_update:
                    result = await domain_service.configure_dns_records(
                        "domain_test_123", dns_records, auto_configure=True
                    )

                    assert result is True
                    mock_cf_dns.assert_called_once_with(sample_domain_config, dns_records)
                    mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_perform_health_check_all_healthy(self, domain_service, sample_domain_config):
        """Test comprehensive domain health check with all checks passing."""
        sample_domain_config.ssl_enabled = True
        sample_domain_config.health_check_url = "https://test.example.com/health"
        sample_domain_config.cdn_enabled = True

        with patch.object(domain_service, "get_domain_configuration", return_value=sample_domain_config):
            with patch.object(
                domain_service, "_check_dns_resolution", return_value={"success": True, "ip_addresses": ["192.168.1.1"]}
            ):
                with patch.object(
                    domain_service, "_check_ssl_certificate", return_value={"success": True, "days_until_expiry": 60}
                ):
                    with patch.object(
                        domain_service, "_check_http_response", return_value={"success": True, "status_code": 200}
                    ):
                        with patch.object(domain_service, "_check_cdn_status", return_value={"success": True}):
                            with patch.object(domain_service, "_update_domain_config") as mock_update:
                                result = await domain_service.perform_health_check("domain_test_123")

                                assert result["overall_status"] == "healthy"
                                assert "dns" in result["checks"]
                                assert "ssl" in result["checks"]
                                assert "http" in result["checks"]
                                assert "cdn" in result["checks"]
                                assert result["checks"]["dns"]["success"] is True

                                mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_perform_health_check_some_failures(self, domain_service, sample_domain_config):
        """Test health check with some failures."""
        sample_domain_config.ssl_enabled = True
        sample_domain_config.health_check_url = "https://test.example.com/health"

        with patch.object(domain_service, "get_domain_configuration", return_value=sample_domain_config):
            with patch.object(domain_service, "_check_dns_resolution", return_value={"success": True}):
                with patch.object(
                    domain_service,
                    "_check_ssl_certificate",
                    return_value={"success": False, "error": "Certificate expired"},
                ):
                    with patch.object(domain_service, "_check_http_response", return_value={"success": True}):
                        with patch.object(domain_service, "_update_domain_config"):
                            result = await domain_service.perform_health_check("domain_test_123")

                            assert result["overall_status"] == "degraded"
                            assert "failed_checks" in result
                            assert "ssl" in result["failed_checks"]

    @pytest.mark.asyncio
    async def test_auto_renew_ssl_certificates(self, domain_service, mock_db_pool):
        """Test SSL certificate auto-renewal process."""
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock

        # Mock expiring certificates
        expiring_certs = [{"domain_id": "domain_001"}, {"domain_id": "domain_002"}]
        conn_mock.fetch.return_value = expiring_certs

        with patch.object(domain_service, "provision_ssl_certificate") as mock_provision:
            mock_provision.side_effect = [True, False]  # First succeeds, second fails

            result = await domain_service.auto_renew_ssl_certificates()

            assert result["total_checked"] == 2
            assert result["successful_renewals"] == 1
            assert result["failed_renewals"] == 1
            assert len(result["details"]) == 2
            assert result["details"][0]["status"] == "renewed"
            assert result["details"][1]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_validate_domain_name_valid_domains(self, domain_service):
        """Test domain name validation with valid domains."""
        valid_domains = ["example.com", "subdomain.example.com", "test-domain.co.uk", "my.domain.example.org"]

        for domain in valid_domains:
            result = await domain_service._validate_domain_name(domain)
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_domain_name_invalid_domains(self, domain_service):
        """Test domain name validation with invalid domains."""
        invalid_domains = [
            "invalid..domain",
            ".invalid.domain",
            "invalid.domain.",
            "invalid_domain.com",
            "invalid domain.com",
            "",
        ]

        for domain in invalid_domains:
            with pytest.raises(ValueError, match="Invalid domain name format"):
                await domain_service._validate_domain_name(domain)

    @pytest.mark.asyncio
    async def test_dns_verification_success(self, domain_service):
        """Test successful DNS verification."""
        config = DomainConfiguration(
            domain_id="test",
            agency_id="agency_001",
            client_id=None,
            domain_name="example.com",
            subdomain=None,
            domain_type=DomainType.AGENCY,
            dns_provider=None,
            dns_zone_id=None,
            dns_records=[],
            verification_token="test_token_123",
        )

        # Mock DNS resolver
        mock_result = MagicMock()
        mock_result.__iter__ = lambda x: iter([MagicMock()])
        mock_result.__getitem__ = lambda x, y: MagicMock()

        with patch.object(domain_service.dns_resolver, "resolve") as mock_resolve:
            mock_resolve.return_value = [MagicMock(__str__=lambda x: "white-label-verify=test_token_123")]

            result = await domain_service._verify_dns_ownership(config)

            assert result is True

    @pytest.mark.asyncio
    async def test_dns_verification_failure(self, domain_service):
        """Test DNS verification failure."""
        config = DomainConfiguration(
            domain_id="test",
            agency_id="agency_001",
            client_id=None,
            domain_name="example.com",
            subdomain=None,
            domain_type=DomainType.AGENCY,
            dns_provider=None,
            dns_zone_id=None,
            dns_records=[],
            verification_token="test_token_123",
        )

        with patch.object(domain_service.dns_resolver, "resolve") as mock_resolve:
            mock_resolve.return_value = [MagicMock(__str__=lambda x: "different-verification-token")]

            result = await domain_service._verify_dns_ownership(config)

            assert result is False

    @pytest.mark.asyncio
    async def test_file_verification_success(self, domain_service):
        """Test successful file-based verification."""
        config = DomainConfiguration(
            domain_id="test",
            agency_id="agency_001",
            client_id=None,
            domain_name="example.com",
            subdomain=None,
            domain_type=DomainType.AGENCY,
            dns_provider=None,
            dns_zone_id=None,
            dns_records=[],
            verification_token="test_token_123",
        )

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="test_token_123")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await domain_service._verify_file_ownership(config)

            assert result is True

    @pytest.mark.asyncio
    async def test_file_verification_failure(self, domain_service):
        """Test file-based verification failure."""
        config = DomainConfiguration(
            domain_id="test",
            agency_id="agency_001",
            client_id=None,
            domain_name="example.com",
            subdomain=None,
            domain_type=DomainType.AGENCY,
            dns_provider=None,
            dns_zone_id=None,
            dns_records=[],
            verification_token="test_token_123",
        )

        # Mock HTTP response with wrong token
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="wrong_token")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await domain_service._verify_file_ownership(config)

            assert result is False


if __name__ == "__main__":
    pytest.main([__file__])