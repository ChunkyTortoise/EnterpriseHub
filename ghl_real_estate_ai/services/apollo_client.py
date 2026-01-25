"""
Production Apollo.io Client for Service 6 Lead Recovery & Nurture Engine.

Provides real Apollo.io API integration for lead enrichment:
- Professional information lookup
- Contact data enrichment
- Company information retrieval
- Email verification
- Advanced search capabilities
- Rate limiting and error handling
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import aiohttp
from aiohttp import ClientTimeout
from pydantic import BaseModel, validator

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.optimized_cache_service import cached

logger = get_logger(__name__)


class ApolloConfig(BaseModel):
    """Apollo.io client configuration."""
    
    api_key: str = settings.apollo_api_key
    base_url: str = "https://api.apollo.io/v1"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_requests_per_minute: int = 200
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or v == "your_apollo_api_key_here":
            raise ValueError("Valid Apollo.io API key is required")
        return v


class PersonEnrichmentResult(BaseModel):
    """Apollo person enrichment result."""
    
    id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    email_status: Optional[str] = None  # verified, unverified, invalid
    phone_numbers: List[Dict[str, str]] = []
    title: Optional[str] = None
    organization: Optional[Dict[str, Any]] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    github_url: Optional[str] = None
    facebook_url: Optional[str] = None
    headline: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    employment_history: List[Dict[str, Any]] = []
    photo_url: Optional[str] = None
    intent_strength: Optional[str] = None
    show_intent: bool = False
    revealed_for_current_team: bool = False
    
    class Config:
        extra = "allow"


class OrganizationEnrichmentResult(BaseModel):
    """Apollo organization enrichment result."""
    
    id: Optional[str] = None
    name: Optional[str] = None
    website_url: Optional[str] = None
    blog_url: Optional[str] = None
    angellist_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    primary_phone: Optional[Dict[str, str]] = None
    languages: List[str] = []
    alexa_ranking: Optional[int] = None
    phone: Optional[str] = None
    linkedin_uid: Optional[str] = None
    founded_year: Optional[int] = None
    publicly_traded_symbol: Optional[str] = None
    publicly_traded_exchange: Optional[str] = None
    logo_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    primary_domain: Optional[str] = None
    industry: Optional[str] = None
    keywords: List[str] = []
    estimated_num_employees: Optional[int] = None
    snippets_loaded: bool = False
    industry_tag_id: Optional[str] = None
    industry_tag_hash: Optional[Dict[str, Any]] = None
    revenue_in_thousands: Optional[int] = None
    
    class Config:
        extra = "allow"


class ApolloAPIException(Exception):
    """Apollo API specific exception."""
    
    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)


class ApolloClient:
    """
    Production Apollo.io API client.
    
    Provides comprehensive lead enrichment capabilities with:
    - Person and company lookup
    - Email verification and phone enrichment
    - Advanced search and filtering
    - Rate limiting and caching
    - Retry logic and error handling
    """
    
    def __init__(self, config: ApolloConfig = None, cache_service: CacheService = None):
        """Initialize Apollo client."""
        self.config = config or ApolloConfig()
        self.cache_service = cache_service or CacheService()
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_semaphore = asyncio.Semaphore(self.config.rate_limit_requests_per_minute)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure HTTP session is created."""
        if not self.session:
            timeout = ClientTimeout(total=self.config.timeout)
            
            headers = {
                "Cache-Control": "no-cache",
                "Content-Type": "application/json",
                "X-Api-Key": self.config.api_key
            }
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
            )
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _make_request(self, method: str, endpoint: str, 
                          data: Dict[str, Any] = None,
                          params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make rate-limited HTTP request to Apollo API."""
        await self._ensure_session()
        
        async with self._rate_limit_semaphore:
            url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
            
            # Add retry logic
            for attempt in range(self.config.max_retries + 1):
                try:
                    if method.upper() == "GET":
                        async with self.session.get(url, params=params) as response:
                            return await self._handle_response(response)
                    elif method.upper() == "POST":
                        async with self.session.post(url, json=data, params=params) as response:
                            return await self._handle_response(response)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                
                except aiohttp.ClientError as e:
                    if attempt < self.config.max_retries:
                        delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Apollo API request failed, retrying in {delay}s: {e}")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise ApolloAPIException(f"Network error after {self.config.max_retries} retries: {e}")
                
                except Exception as e:
                    logger.error(f"Unexpected error in Apollo API request: {e}")
                    raise ApolloAPIException(f"Unexpected error: {e}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle Apollo API response."""
        try:
            response_data = await response.json()
        except aiohttp.ContentTypeError:
            response_text = await response.text()
            logger.error(f"Apollo API returned non-JSON response: {response_text}")
            raise ApolloAPIException(f"Invalid response format", response.status)
        
        if response.status == 200:
            return response_data
        elif response.status == 429:
            # Rate limit exceeded
            raise ApolloAPIException("Rate limit exceeded", response.status, response_data)
        elif response.status in [401, 403]:
            # Authentication/authorization error
            raise ApolloAPIException("Authentication failed", response.status, response_data)
        elif response.status == 404:
            # Not found - return empty result
            return {"people": [], "organizations": []}
        else:
            error_msg = response_data.get("error", f"HTTP {response.status}")
            raise ApolloAPIException(error_msg, response.status, response_data)
    
    # ============================================================================
    # Person Enrichment
    # ============================================================================
    
    @cached(ttl=3600, key_prefix="apollo_person_enrichment")
    async def enrich_person(self, email: str = None, first_name: str = None, 
                           last_name: str = None, organization_domain: str = None) -> PersonEnrichmentResult:
        """
        Enrich person data using Apollo API.
        
        Args:
            email: Person's email address
            first_name: Person's first name
            last_name: Person's last name
            organization_domain: Company domain (e.g., "apollo.io")
        
        Returns:
            PersonEnrichmentResult with enriched data
        """
        if not email and not (first_name and last_name):
            raise ValueError("Email or first_name + last_name is required")
        
        # Build request data
        data = {}
        if email:
            data["email"] = email
        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        if organization_domain:
            data["organization_domain"] = organization_domain
        
        # Include additional fields we want
        data["reveal_personal_emails"] = True
        data["reveal_phone_number"] = True
        
        try:
            response = await self._make_request("POST", "/people/match", data=data)
            
            person_data = response.get("person", {})
            
            if not person_data:
                logger.info(f"No person data found for {email or f'{first_name} {last_name}'}")
                return PersonEnrichmentResult()
            
            # Transform Apollo response to our model
            result = PersonEnrichmentResult(**person_data)
            
            logger.info(f"Successfully enriched person: {result.email or email}")
            return result
            
        except ApolloAPIException as e:
            logger.error(f"Apollo person enrichment failed: {e.message}")
            # Return empty result instead of raising exception
            return PersonEnrichmentResult()
    
    @cached(ttl=3600, key_prefix="apollo_email_verification")
    async def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify email address using Apollo.
        
        Returns:
            Dict with verification status and additional info
        """
        try:
            response = await self._make_request("POST", "/emailVerifier", data={"email": email})
            
            verification_result = {
                "email": email,
                "is_valid": response.get("is_valid", False),
                "is_disposable": response.get("is_disposable", False),
                "is_webmail": response.get("is_webmail", False),
                "is_deliverable": response.get("is_deliverable", False),
                "verification_status": response.get("verification", "unknown"),
                "confidence_score": response.get("confidence", 0),
                "verified_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Email verification completed for {email}: {verification_result['verification_status']}")
            return verification_result
            
        except ApolloAPIException as e:
            logger.error(f"Email verification failed for {email}: {e.message}")
            return {
                "email": email,
                "is_valid": False,
                "verification_status": "error",
                "error": e.message,
                "verified_at": datetime.utcnow().isoformat()
            }
    
    # ============================================================================
    # Organization Enrichment
    # ============================================================================
    
    @cached(ttl=7200, key_prefix="apollo_organization_enrichment")
    async def enrich_organization(self, domain: str = None, 
                                organization_name: str = None) -> OrganizationEnrichmentResult:
        """
        Enrich organization data using Apollo API.
        
        Args:
            domain: Company domain (e.g., "apollo.io")
            organization_name: Company name
        
        Returns:
            OrganizationEnrichmentResult with enriched data
        """
        if not domain and not organization_name:
            raise ValueError("Domain or organization_name is required")
        
        data = {}
        if domain:
            data["domain"] = domain
        if organization_name:
            data["name"] = organization_name
        
        try:
            response = await self._make_request("POST", "/organizations/match", data=data)
            
            org_data = response.get("organization", {})
            
            if not org_data:
                logger.info(f"No organization data found for {domain or organization_name}")
                return OrganizationEnrichmentResult()
            
            result = OrganizationEnrichmentResult(**org_data)
            
            logger.info(f"Successfully enriched organization: {result.name or organization_name}")
            return result
            
        except ApolloAPIException as e:
            logger.error(f"Apollo organization enrichment failed: {e.message}")
            return OrganizationEnrichmentResult()
    
    # ============================================================================
    # Advanced Search
    # ============================================================================
    
    async def search_people(self, search_criteria: Dict[str, Any], 
                           limit: int = 25) -> List[PersonEnrichmentResult]:
        """
        Search for people using Apollo's advanced search.
        
        Args:
            search_criteria: Dict with search parameters
            limit: Maximum number of results (max 25 per request)
        
        Returns:
            List of PersonEnrichmentResult objects
        """
        # Build search query
        data = {
            "page": 1,
            "per_page": min(limit, 25)  # Apollo limits to 25 per request
        }
        
        # Add search criteria
        if "titles" in search_criteria:
            data["person_titles"] = search_criteria["titles"]
        
        if "locations" in search_criteria:
            data["person_locations"] = search_criteria["locations"]
        
        if "organization_domains" in search_criteria:
            data["organization_domains"] = search_criteria["organization_domains"]
        
        if "organization_num_employees_ranges" in search_criteria:
            data["organization_num_employees_ranges"] = search_criteria["organization_num_employees_ranges"]
        
        if "industries" in search_criteria:
            data["organization_industry_tag_ids"] = search_criteria["industries"]
        
        try:
            response = await self._make_request("POST", "/mixed_people/search", data=data)
            
            people = response.get("people", [])
            results = []
            
            for person_data in people:
                try:
                    result = PersonEnrichmentResult(**person_data)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to parse person data: {e}")
                    continue
            
            logger.info(f"Apollo people search returned {len(results)} results")
            return results
            
        except ApolloAPIException as e:
            logger.error(f"Apollo people search failed: {e.message}")
            return []
    
    # ============================================================================
    # Lead Scoring Integration
    # ============================================================================
    
    async def calculate_lead_score(self, person_data: PersonEnrichmentResult,
                                 organization_data: OrganizationEnrichmentResult = None) -> Dict[str, Any]:
        """
        Calculate lead score based on Apollo enrichment data.
        
        Scoring factors:
        - Title seniority (C-level, VP, Director, etc.)
        - Company size and revenue
        - Industry relevance
        - Contact data completeness
        - Email verification status
        """
        score = 0
        score_breakdown = {}
        
        # Title scoring (0-30 points)
        title_score = self._score_title(person_data.title)
        score += title_score
        score_breakdown["title"] = title_score
        
        # Company size scoring (0-25 points)
        company_score = self._score_company(organization_data)
        score += company_score
        score_breakdown["company"] = company_score
        
        # Contact completeness (0-20 points)
        contact_score = self._score_contact_completeness(person_data)
        score += contact_score
        score_breakdown["contact_completeness"] = contact_score
        
        # Email verification (0-15 points)
        email_score = self._score_email_verification(person_data)
        score += email_score
        score_breakdown["email_verification"] = email_score
        
        # Intent signals (0-10 points)
        intent_score = self._score_intent_signals(person_data)
        score += intent_score
        score_breakdown["intent_signals"] = intent_score
        
        # Determine temperature based on score
        if score >= 70:
            temperature = "hot"
        elif score >= 40:
            temperature = "warm"
        else:
            temperature = "cold"
        
        return {
            "total_score": min(score, 100),  # Cap at 100
            "temperature": temperature,
            "score_breakdown": score_breakdown,
            "scored_at": datetime.utcnow().isoformat()
        }
    
    def _score_title(self, title: str) -> int:
        """Score based on job title seniority."""
        if not title:
            return 0
        
        title_lower = title.lower()
        
        # C-level executives
        if any(word in title_lower for word in ["ceo", "cfo", "cto", "cmo", "chief"]):
            return 30
        
        # VP level
        if any(word in title_lower for word in ["vice president", "vp", "v.p."]):
            return 25
        
        # Director level
        if any(word in title_lower for word in ["director", "head of"]):
            return 20
        
        # Manager level
        if any(word in title_lower for word in ["manager", "lead", "senior"]):
            return 15
        
        # Individual contributor
        if any(word in title_lower for word in ["specialist", "analyst", "coordinator"]):
            return 10
        
        # Others
        return 5
    
    def _score_company(self, org_data: OrganizationEnrichmentResult) -> int:
        """Score based on company characteristics."""
        if not org_data:
            return 0
        
        score = 0
        
        # Employee count scoring
        if org_data.estimated_num_employees:
            if org_data.estimated_num_employees >= 1000:
                score += 15
            elif org_data.estimated_num_employees >= 100:
                score += 10
            elif org_data.estimated_num_employees >= 50:
                score += 8
            elif org_data.estimated_num_employees >= 10:
                score += 5
        
        # Revenue scoring
        if org_data.revenue_in_thousands:
            if org_data.revenue_in_thousands >= 100000:  # $100M+
                score += 10
            elif org_data.revenue_in_thousands >= 10000:  # $10M+
                score += 8
            elif org_data.revenue_in_thousands >= 1000:   # $1M+
                score += 5
        
        return min(score, 25)
    
    def _score_contact_completeness(self, person_data: PersonEnrichmentResult) -> int:
        """Score based on how complete the contact information is."""
        score = 0
        
        # Email
        if person_data.email:
            score += 5
        
        # Phone number
        if person_data.phone_numbers:
            score += 5
        
        # Social profiles
        if person_data.linkedin_url:
            score += 3
        
        # Professional info
        if person_data.title:
            score += 3
        
        # Company info
        if person_data.organization:
            score += 2
        
        # Location
        if person_data.city or person_data.state:
            score += 2
        
        return min(score, 20)
    
    def _score_email_verification(self, person_data: PersonEnrichmentResult) -> int:
        """Score based on email verification status."""
        if not person_data.email_status:
            return 0
        
        if person_data.email_status == "verified":
            return 15
        elif person_data.email_status == "unverified":
            return 8
        else:  # invalid
            return 0
    
    def _score_intent_signals(self, person_data: PersonEnrichmentResult) -> int:
        """Score based on intent and engagement signals."""
        score = 0
        
        if person_data.show_intent:
            score += 5
        
        if person_data.intent_strength == "high":
            score += 5
        elif person_data.intent_strength == "medium":
            score += 3
        elif person_data.intent_strength == "low":
            score += 1
        
        return min(score, 10)
    
    # ============================================================================
    # Batch Processing
    # ============================================================================
    
    async def batch_enrich_people(self, contacts: List[Dict[str, str]], 
                                batch_size: int = 10) -> List[PersonEnrichmentResult]:
        """
        Enrich multiple people in batches to respect rate limits.
        
        Args:
            contacts: List of contact dictionaries with email/name info
            batch_size: Number of contacts to process in parallel
        
        Returns:
            List of PersonEnrichmentResult objects
        """
        results = []
        
        # Process in batches
        for i in range(0, len(contacts), batch_size):
            batch = contacts[i:i + batch_size]
            
            # Create enrichment tasks
            tasks = []
            for contact in batch:
                task = self.enrich_person(
                    email=contact.get("email"),
                    first_name=contact.get("first_name"),
                    last_name=contact.get("last_name"),
                    organization_domain=contact.get("organization_domain")
                )
                tasks.append(task)
            
            # Execute batch
            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch enrichment error: {result}")
                        results.append(PersonEnrichmentResult())  # Empty result
                    else:
                        results.append(result)
                
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                # Add empty results for failed batch
                results.extend([PersonEnrichmentResult()] * len(batch))
            
            # Delay between batches to respect rate limits
            if i + batch_size < len(contacts):
                await asyncio.sleep(1)
        
        logger.info(f"Completed batch enrichment for {len(contacts)} contacts")
        return results
    
    # ============================================================================
    # Health Check
    # ============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Apollo API connectivity and status."""
        try:
            # Test with a simple email verification
            test_response = await self._make_request(
                "POST", 
                "/emailVerifier", 
                data={"email": "test@apollo.io"}
            )
            
            return {
                "status": "healthy",
                "api_accessible": True,
                "test_response_received": bool(test_response),
                "rate_limit_available": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except ApolloAPIException as e:
            return {
                "status": "unhealthy" if e.status_code != 429 else "rate_limited",
                "api_accessible": e.status_code not in [401, 403],
                "error": e.message,
                "status_code": e.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "api_accessible": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    async def test_apollo_client():
        """Test Apollo client functionality."""
        async with ApolloClient() as apollo:
            try:
                # Test person enrichment
                person_result = await apollo.enrich_person(email="tim@apollo.io")
                print(f"Person enrichment: {person_result.name or 'No name'}")
                
                # Test email verification
                verification = await apollo.verify_email("tim@apollo.io")
                print(f"Email verification: {verification['verification_status']}")
                
                # Test organization enrichment
                org_result = await apollo.enrich_organization(domain="apollo.io")
                print(f"Organization: {org_result.name or 'No name'}")
                
                # Test lead scoring
                if person_result.email:
                    score_data = await apollo.calculate_lead_score(person_result, org_result)
                    print(f"Lead score: {score_data['total_score']} ({score_data['temperature']})")
                
                # Health check
                health = await apollo.health_check()
                print(f"Health: {health['status']}")
                
            except Exception as e:
                print(f"Test failed: {e}")
    
    # Run test
    asyncio.run(test_apollo_client())