"""
Domain Configuration Service - DNS and SSL Automation
Handles custom domain setup, DNS management, and SSL certificate automation
for white-label deployments in the $500K ARR platform.
"""

import asyncio
import hashlib
import secrets
import socket
import ssl
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import re

import aiohttp
import asyncpg
import dns.resolver
import dns.asyncresolver

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService

logger = get_logger(__name__)


class DomainType(Enum):
    """Domain configuration types."""
    AGENCY = "agency"
    CLIENT = "client"
    CUSTOM = "custom"


class VerificationMethod(Enum):
    """Domain verification methods."""
    DNS = "dns"
    FILE = "file"
    EMAIL = "email"


class SSLProvider(Enum):
    """SSL certificate providers."""
    LETSENCRYPT = "letsencrypt"
    CLOUDFLARE = "cloudflare"
    AWS_ACM = "aws_acm"
    CUSTOM = "custom"


class DNSProvider(Enum):
    """DNS service providers."""
    CLOUDFLARE = "cloudflare"
    ROUTE53 = "route53"
    GOOGLE_CLOUD_DNS = "google_cloud_dns"
    AZURE_DNS = "azure_dns"


@dataclass
class DNSRecord:
    """DNS record configuration."""
    name: str
    type: str  # A, AAAA, CNAME, TXT, MX
    value: str
    ttl: int = 300
    priority: Optional[int] = None  # For MX records


@dataclass
class DomainConfiguration:
    """Complete domain configuration."""
    domain_id: str
    agency_id: str
    client_id: Optional[str]
    domain_name: str
    subdomain: Optional[str]
    domain_type: DomainType

    # DNS Configuration
    dns_provider: Optional[DNSProvider]
    dns_zone_id: Optional[str]
    dns_records: List[DNSRecord]

    # SSL Configuration
    ssl_enabled: bool = True
    ssl_provider: SSLProvider = SSLProvider.LETSENCRYPT
    ssl_cert_status: str = "pending"
    ssl_cert_expires_at: Optional[datetime] = None
    ssl_auto_renew: bool = True

    # CDN Configuration
    cdn_enabled: bool = False
    cdn_provider: Optional[str] = None
    cdn_distribution_id: Optional[str] = None
    cdn_endpoint: Optional[str] = None

    # Verification
    verification_token: str = ""
    verification_status: str = "pending"
    verification_method: VerificationMethod = VerificationMethod.DNS
    verified_at: Optional[datetime] = None

    # Status
    status: str = "pending"
    health_check_url: Optional[str] = None
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"

    # Metadata
    configuration_metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.configuration_metadata is None:
            self.configuration_metadata = {}
        if not self.verification_token:
            self.verification_token = self._generate_verification_token()

    def _generate_verification_token(self) -> str:
        """Generate secure verification token."""
        return secrets.token_urlsafe(32)


class DomainConfigurationService:
    """
    Service for managing domain configurations, DNS automation, and SSL certificates
    in the white-label platform.
    """

    def __init__(self, db_pool: asyncpg.Pool, cache_service: CacheService):
        """Initialize domain configuration service."""
        self.db_pool = db_pool
        self.cache = cache_service

        # DNS resolver for validation
        self.dns_resolver = dns.asyncresolver.Resolver()
        self.dns_resolver.timeout = 10
        self.dns_resolver.lifetime = 30

        # Provider configurations (from environment)
        self.cloudflare_token = settings.get("CLOUDFLARE_API_TOKEN")
        self.aws_access_key = settings.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = settings.get("AWS_SECRET_ACCESS_KEY")

        logger.info("Domain configuration service initialized")

    async def create_domain_configuration(
        self,
        agency_id: str,
        domain_name: str,
        domain_type: DomainType,
        client_id: Optional[str] = None,
        dns_provider: Optional[DNSProvider] = None,
        ssl_provider: SSLProvider = SSLProvider.LETSENCRYPT,
        cdn_enabled: bool = False
    ) -> DomainConfiguration:
        """Create new domain configuration."""

        try:
            # Validate domain name
            await self._validate_domain_name(domain_name)

            # Check if domain already exists
            existing = await self.get_domain_by_name(domain_name)
            if existing:
                raise ValueError(f"Domain {domain_name} already configured")

            # Generate domain ID
            domain_id = f"domain_{int(time.time())}_{secrets.token_hex(8)}"

            # Extract subdomain if applicable
            subdomain = None
            if domain_type == DomainType.CLIENT and '.' in domain_name:
                parts = domain_name.split('.')
                if len(parts) > 2:
                    subdomain = parts[0]

            # Create configuration
            config = DomainConfiguration(
                domain_id=domain_id,
                agency_id=agency_id,
                client_id=client_id,
                domain_name=domain_name,
                subdomain=subdomain,
                domain_type=domain_type,
                dns_provider=dns_provider,
                dns_zone_id=None,
                dns_records=[],
                ssl_provider=ssl_provider,
                cdn_enabled=cdn_enabled,
                created_at=datetime.utcnow()
            )

            # Save to database
            await self._save_domain_configuration(config)

            # Start domain verification process
            await self.initiate_domain_verification(domain_id)

            logger.info(f"Created domain configuration {domain_id} for {domain_name}")
            return config

        except Exception as e:
            logger.error(f"Failed to create domain configuration for {domain_name}: {e}")
            raise

    async def get_domain_configuration(self, domain_id: str) -> Optional[DomainConfiguration]:
        """Get domain configuration by ID."""

        # Check cache first
        cache_key = f"domain_config:{domain_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return DomainConfiguration(**json.loads(cached))

        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT *
                    FROM domain_configurations
                    WHERE domain_id = $1
                """
                row = await conn.fetchrow(query, domain_id)

                if not row:
                    return None

                config = self._row_to_domain_config(row)

                # Cache for 15 minutes
                await self.cache.set(cache_key, json.dumps(asdict(config)), ttl=900)

                return config

        except Exception as e:
            logger.error(f"Failed to get domain configuration {domain_id}: {e}")
            return None

    async def get_domain_by_name(self, domain_name: str) -> Optional[DomainConfiguration]:
        """Get domain configuration by name."""

        # Check cache first
        cache_key = f"domain_by_name:{domain_name}"
        cached = await self.cache.get(cache_key)
        if cached:
            return DomainConfiguration(**json.loads(cached))

        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT *
                    FROM domain_configurations
                    WHERE domain_name = $1
                """
                row = await conn.fetchrow(query, domain_name)

                if not row:
                    return None

                config = self._row_to_domain_config(row)

                # Cache for 15 minutes
                await self.cache.set(cache_key, json.dumps(asdict(config)), ttl=900)

                return config

        except Exception as e:
            logger.error(f"Failed to get domain by name {domain_name}: {e}")
            return None

    async def list_agency_domains(
        self,
        agency_id: str,
        domain_type: Optional[DomainType] = None,
        status: Optional[str] = None
    ) -> List[DomainConfiguration]:
        """List domains for an agency."""

        try:
            async with self.db_pool.acquire() as conn:
                conditions = ["agency_id = $1"]
                params = [agency_id]

                if domain_type:
                    conditions.append(f"domain_type = ${len(params) + 1}")
                    params.append(domain_type.value)

                if status:
                    conditions.append(f"status = ${len(params) + 1}")
                    params.append(status)

                query = f"""
                    SELECT *
                    FROM domain_configurations
                    WHERE {' AND '.join(conditions)}
                    ORDER BY created_at DESC
                """

                rows = await conn.fetch(query, *params)
                return [self._row_to_domain_config(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list agency domains for {agency_id}: {e}")
            return []

    async def initiate_domain_verification(self, domain_id: str) -> bool:
        """Start domain verification process."""

        try:
            config = await self.get_domain_configuration(domain_id)
            if not config:
                raise ValueError(f"Domain configuration {domain_id} not found")

            # Generate new verification token if needed
            if not config.verification_token:
                config.verification_token = secrets.token_urlsafe(32)
                await self._update_domain_config(config)

            # Start verification based on method
            if config.verification_method == VerificationMethod.DNS:
                success = await self._verify_dns_ownership(config)
            elif config.verification_method == VerificationMethod.FILE:
                success = await self._verify_file_ownership(config)
            else:
                # Email verification not implemented yet
                success = False

            if success:
                await self._mark_domain_verified(domain_id)
                # Start SSL certificate process
                await self.provision_ssl_certificate(domain_id)

            return success

        except Exception as e:
            logger.error(f"Failed to initiate domain verification for {domain_id}: {e}")
            return False

    async def provision_ssl_certificate(self, domain_id: str) -> bool:
        """Provision SSL certificate for domain."""

        try:
            config = await self.get_domain_configuration(domain_id)
            if not config:
                raise ValueError(f"Domain configuration {domain_id} not found")

            if config.verification_status != "verified":
                logger.warning(f"Cannot provision SSL for unverified domain {config.domain_name}")
                return False

            # Provision based on SSL provider
            if config.ssl_provider == SSLProvider.LETSENCRYPT:
                success = await self._provision_letsencrypt_certificate(config)
            elif config.ssl_provider == SSLProvider.CLOUDFLARE:
                success = await self._provision_cloudflare_certificate(config)
            elif config.ssl_provider == SSLProvider.AWS_ACM:
                success = await self._provision_aws_acm_certificate(config)
            else:
                logger.warning(f"SSL provider {config.ssl_provider} not implemented")
                success = False

            if success:
                # Update SSL status
                config.ssl_cert_status = "issued"
                config.ssl_cert_expires_at = datetime.utcnow() + timedelta(days=90)  # Standard Let's Encrypt duration
                await self._update_domain_config(config)

                logger.info(f"SSL certificate provisioned for {config.domain_name}")

            return success

        except Exception as e:
            logger.error(f"Failed to provision SSL certificate for {domain_id}: {e}")
            return False

    async def configure_dns_records(
        self,
        domain_id: str,
        records: List[DNSRecord],
        auto_configure: bool = True
    ) -> bool:
        """Configure DNS records for domain."""

        try:
            config = await self.get_domain_configuration(domain_id)
            if not config:
                raise ValueError(f"Domain configuration {domain_id} not found")

            # Add records to configuration
            config.dns_records = records

            # Auto-configure with DNS provider if enabled
            if auto_configure and config.dns_provider:
                if config.dns_provider == DNSProvider.CLOUDFLARE:
                    success = await self._configure_cloudflare_dns(config, records)
                elif config.dns_provider == DNSProvider.ROUTE53:
                    success = await self._configure_route53_dns(config, records)
                else:
                    logger.warning(f"DNS provider {config.dns_provider} not implemented")
                    success = False

                if not success:
                    logger.warning(f"Failed to auto-configure DNS for {config.domain_name}")

            # Update configuration
            await self._update_domain_config(config)

            logger.info(f"DNS records configured for {config.domain_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to configure DNS records for {domain_id}: {e}")
            return False

    async def perform_health_check(self, domain_id: str) -> Dict[str, Any]:
        """Perform comprehensive health check on domain."""

        try:
            config = await self.get_domain_configuration(domain_id)
            if not config:
                raise ValueError(f"Domain configuration {domain_id} not found")

            health_results = {
                "domain_name": config.domain_name,
                "overall_status": "healthy",
                "checks": {},
                "timestamp": datetime.utcnow().isoformat()
            }

            # DNS resolution check
            dns_check = await self._check_dns_resolution(config.domain_name)
            health_results["checks"]["dns"] = dns_check

            # SSL certificate check
            if config.ssl_enabled:
                ssl_check = await self._check_ssl_certificate(config.domain_name)
                health_results["checks"]["ssl"] = ssl_check

            # HTTP response check
            if config.health_check_url:
                http_check = await self._check_http_response(config.health_check_url)
                health_results["checks"]["http"] = http_check

            # CDN check
            if config.cdn_enabled:
                cdn_check = await self._check_cdn_status(config)
                health_results["checks"]["cdn"] = cdn_check

            # Determine overall status
            failed_checks = [name for name, result in health_results["checks"].items() if not result.get("success", False)]
            if failed_checks:
                if len(failed_checks) == len(health_results["checks"]):
                    health_results["overall_status"] = "unhealthy"
                else:
                    health_results["overall_status"] = "degraded"
                health_results["failed_checks"] = failed_checks

            # Update domain health status
            config.health_status = health_results["overall_status"]
            config.last_health_check = datetime.utcnow()
            await self._update_domain_config(config)

            return health_results

        except Exception as e:
            logger.error(f"Failed to perform health check for {domain_id}: {e}")
            return {
                "domain_name": domain_id,
                "overall_status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def auto_renew_ssl_certificates(self) -> Dict[str, Any]:
        """Auto-renew SSL certificates that are expiring soon."""

        try:
            # Find certificates expiring in the next 30 days
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT domain_id
                    FROM domain_configurations
                    WHERE ssl_enabled = true
                      AND ssl_auto_renew = true
                      AND ssl_cert_expires_at <= $1
                      AND status = 'active'
                """
                expiring_date = datetime.utcnow() + timedelta(days=30)
                rows = await conn.fetch(query, expiring_date)

            renewal_results = {
                "total_checked": len(rows),
                "successful_renewals": 0,
                "failed_renewals": 0,
                "details": []
            }

            for row in rows:
                domain_id = row["domain_id"]
                try:
                    success = await self.provision_ssl_certificate(domain_id)
                    if success:
                        renewal_results["successful_renewals"] += 1
                        renewal_results["details"].append({
                            "domain_id": domain_id,
                            "status": "renewed"
                        })
                    else:
                        renewal_results["failed_renewals"] += 1
                        renewal_results["details"].append({
                            "domain_id": domain_id,
                            "status": "failed"
                        })
                except Exception as e:
                    renewal_results["failed_renewals"] += 1
                    renewal_results["details"].append({
                        "domain_id": domain_id,
                        "status": "error",
                        "error": str(e)
                    })

            logger.info(f"SSL auto-renewal completed: {renewal_results['successful_renewals']} successful, {renewal_results['failed_renewals']} failed")
            return renewal_results

        except Exception as e:
            logger.error(f"Failed to auto-renew SSL certificates: {e}")
            return {"error": str(e)}

    # Private helper methods

    async def _validate_domain_name(self, domain_name: str) -> bool:
        """Validate domain name format."""
        domain_regex = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        if not domain_regex.match(domain_name):
            raise ValueError(f"Invalid domain name format: {domain_name}")
        return True

    async def _save_domain_configuration(self, config: DomainConfiguration) -> None:
        """Save domain configuration to database."""
        async with self.db_pool.acquire() as conn:
            query = """
                INSERT INTO domain_configurations (
                    domain_id, agency_id, client_id, domain_name, subdomain,
                    domain_type, dns_provider, dns_zone_id, dns_records,
                    ssl_enabled, ssl_provider, ssl_cert_status, ssl_auto_renew,
                    cdn_enabled, cdn_provider, verification_token, verification_method,
                    status, configuration_metadata, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
                )
            """
            await conn.execute(
                query,
                config.domain_id,
                config.agency_id,
                config.client_id,
                config.domain_name,
                config.subdomain,
                config.domain_type.value,
                config.dns_provider.value if config.dns_provider else None,
                config.dns_zone_id,
                json.dumps([asdict(record) for record in config.dns_records]),
                config.ssl_enabled,
                config.ssl_provider.value,
                config.ssl_cert_status,
                config.ssl_auto_renew,
                config.cdn_enabled,
                config.cdn_provider,
                config.verification_token,
                config.verification_method.value,
                config.status,
                json.dumps(config.configuration_metadata),
                config.created_at,
                datetime.utcnow()
            )

    async def _update_domain_config(self, config: DomainConfiguration) -> None:
        """Update domain configuration in database."""
        config.updated_at = datetime.utcnow()

        async with self.db_pool.acquire() as conn:
            query = """
                UPDATE domain_configurations
                SET dns_records = $1, ssl_cert_status = $2, ssl_cert_expires_at = $3,
                    verification_status = $4, verified_at = $5, status = $6,
                    health_status = $7, last_health_check = $8, configuration_metadata = $9,
                    updated_at = $10
                WHERE domain_id = $11
            """
            await conn.execute(
                query,
                json.dumps([asdict(record) for record in config.dns_records]),
                config.ssl_cert_status,
                config.ssl_cert_expires_at,
                config.verification_status,
                config.verified_at,
                config.status,
                config.health_status,
                config.last_health_check,
                json.dumps(config.configuration_metadata),
                config.updated_at,
                config.domain_id
            )

        # Invalidate cache
        await self.cache.delete(f"domain_config:{config.domain_id}")
        await self.cache.delete(f"domain_by_name:{config.domain_name}")

    def _row_to_domain_config(self, row) -> DomainConfiguration:
        """Convert database row to DomainConfiguration."""
        dns_records = []
        if row["dns_records"]:
            for record_data in json.loads(row["dns_records"]):
                dns_records.append(DNSRecord(**record_data))

        return DomainConfiguration(
            domain_id=row["domain_id"],
            agency_id=row["agency_id"],
            client_id=row["client_id"],
            domain_name=row["domain_name"],
            subdomain=row["subdomain"],
            domain_type=DomainType(row["domain_type"]),
            dns_provider=DNSProvider(row["dns_provider"]) if row["dns_provider"] else None,
            dns_zone_id=row["dns_zone_id"],
            dns_records=dns_records,
            ssl_enabled=row["ssl_enabled"],
            ssl_provider=SSLProvider(row["ssl_provider"]),
            ssl_cert_status=row["ssl_cert_status"],
            ssl_cert_expires_at=row["ssl_cert_expires_at"],
            ssl_auto_renew=row["ssl_auto_renew"],
            cdn_enabled=row["cdn_enabled"],
            cdn_provider=row["cdn_provider"],
            cdn_distribution_id=row["cdn_distribution_id"],
            cdn_endpoint=row["cdn_endpoint"],
            verification_token=row["verification_token"],
            verification_status=row["verification_status"],
            verification_method=VerificationMethod(row["verification_method"]),
            verified_at=row["verified_at"],
            status=row["status"],
            health_check_url=row["health_check_url"],
            last_health_check=row["last_health_check"],
            health_status=row["health_status"],
            configuration_metadata=json.loads(row["configuration_metadata"]) if row["configuration_metadata"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    async def _verify_dns_ownership(self, config: DomainConfiguration) -> bool:
        """Verify domain ownership via DNS TXT record."""
        try:
            expected_record = f"white-label-verify={config.verification_token}"

            # Look for TXT record with verification token
            result = await self.dns_resolver.resolve(config.domain_name, "TXT")
            for rdata in result:
                if expected_record in str(rdata).replace('"', ''):
                    return True

            return False

        except Exception as e:
            logger.warning(f"DNS verification failed for {config.domain_name}: {e}")
            return False

    async def _verify_file_ownership(self, config: DomainConfiguration) -> bool:
        """Verify domain ownership via file on web server."""
        try:
            verification_url = f"https://{config.domain_name}/.well-known/white-label-verify.txt"

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(verification_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return config.verification_token in content.strip()

            return False

        except Exception as e:
            logger.warning(f"File verification failed for {config.domain_name}: {e}")
            return False

    async def _mark_domain_verified(self, domain_id: str) -> None:
        """Mark domain as verified."""
        config = await self.get_domain_configuration(domain_id)
        if config:
            config.verification_status = "verified"
            config.verified_at = datetime.utcnow()
            config.status = "active"
            await self._update_domain_config(config)

    async def _provision_letsencrypt_certificate(self, config: DomainConfiguration) -> bool:
        """Provision Let's Encrypt SSL certificate."""
        # This would integrate with ACME client (certbot or acme.py)
        # For now, simulate the process
        logger.info(f"Simulating Let's Encrypt certificate provisioning for {config.domain_name}")

        # In production, this would:
        # 1. Create ACME client
        # 2. Request certificate via HTTP-01 or DNS-01 challenge
        # 3. Store certificate in secure storage
        # 4. Configure web server/load balancer

        await asyncio.sleep(1)  # Simulate processing time
        return True

    async def _provision_cloudflare_certificate(self, config: DomainConfiguration) -> bool:
        """Provision Cloudflare SSL certificate."""
        if not self.cloudflare_token:
            logger.error("Cloudflare API token not configured")
            return False

        # This would integrate with Cloudflare API for origin certificates
        logger.info(f"Simulating Cloudflare certificate provisioning for {config.domain_name}")
        return True

    async def _provision_aws_acm_certificate(self, config: DomainConfiguration) -> bool:
        """Provision AWS ACM SSL certificate."""
        if not self.aws_access_key or not self.aws_secret_key:
            logger.error("AWS credentials not configured")
            return False

        # This would integrate with AWS ACM API
        logger.info(f"Simulating AWS ACM certificate provisioning for {config.domain_name}")
        return True

    async def _configure_cloudflare_dns(self, config: DomainConfiguration, records: List[DNSRecord]) -> bool:
        """Configure DNS records via Cloudflare API."""
        if not self.cloudflare_token:
            logger.error("Cloudflare API token not configured")
            return False

        # This would integrate with Cloudflare API
        logger.info(f"Simulating Cloudflare DNS configuration for {config.domain_name}")
        return True

    async def _configure_route53_dns(self, config: DomainConfiguration, records: List[DNSRecord]) -> bool:
        """Configure DNS records via Route 53 API."""
        if not self.aws_access_key or not self.aws_secret_key:
            logger.error("AWS credentials not configured")
            return False

        # This would integrate with AWS Route 53 API
        logger.info(f"Simulating Route 53 DNS configuration for {config.domain_name}")
        return True

    async def _check_dns_resolution(self, domain_name: str) -> Dict[str, Any]:
        """Check DNS resolution for domain."""
        try:
            result = await self.dns_resolver.resolve(domain_name, "A")
            return {
                "success": True,
                "ip_addresses": [str(rdata) for rdata in result],
                "ttl": result.rrset.ttl
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _check_ssl_certificate(self, domain_name: str) -> Dict[str, Any]:
        """Check SSL certificate status."""
        try:
            context = ssl.create_default_context()

            # Connect and get certificate
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)

            wrapped_socket = context.wrap_socket(sock, server_hostname=domain_name)
            wrapped_socket.connect((domain_name, 443))

            cert = wrapped_socket.getpeercert()
            wrapped_socket.close()

            # Parse certificate details
            not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            days_until_expiry = (not_after - datetime.utcnow()).days

            return {
                "success": True,
                "issuer": cert.get("issuer", []),
                "subject": cert.get("subject", []),
                "expires_at": cert["notAfter"],
                "days_until_expiry": days_until_expiry,
                "is_valid": days_until_expiry > 0
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _check_http_response(self, url: str) -> Dict[str, Any]:
        """Check HTTP response for health check URL."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                start_time = time.time()
                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

                    return {
                        "success": response.status < 400,
                        "status_code": response.status,
                        "response_time_ms": round(response_time, 2),
                        "content_type": response.headers.get("Content-Type")
                    }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _check_cdn_status(self, config: DomainConfiguration) -> Dict[str, Any]:
        """Check CDN status."""
        if not config.cdn_enabled:
            return {"success": True, "message": "CDN not enabled"}

        # This would check CDN provider status
        return {
            "success": True,
            "provider": config.cdn_provider,
            "endpoint": config.cdn_endpoint
        }


# Factory function for service initialization
def get_domain_configuration_service(db_pool: asyncpg.Pool, cache_service: CacheService) -> DomainConfigurationService:
    """Get configured domain configuration service instance."""
    return DomainConfigurationService(db_pool, cache_service)