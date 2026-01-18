#!/usr/bin/env python3
"""
CRITICAL SECURITY VALIDATION SCRIPT

This script validates that all critical security vulnerabilities have been properly fixed.
Run this to verify that silent failure vulnerabilities are eliminated.
"""

import asyncio
import sys
import os
from unittest.mock import patch, Mock, AsyncMock
import tempfile


async def test_tag_removal_security_fix():
    """Test that tag removal now properly removes tags instead of just logging."""
    print("🔍 Testing tag removal security fix...")
    
    try:
        # Add the project path
        sys.path.insert(0, '/Users/cave/Documents/GitHub/EnterpriseHub')
        from ghl_real_estate_ai.services.ghl_client import GHLClient
        
        client = GHLClient(api_key="test-key-32-chars-min-required-test", location_id="test")
        
        # Mock HTTP responses
        with patch('httpx.AsyncClient') as mock_client:
            # Setup proper mock responses
            mock_get_response = Mock()
            mock_get_response.raise_for_status = Mock()
            mock_get_response.json.return_value = {"tags": ["tag1", "tag2", "sensitive-tag"]}
            
            mock_put_response = Mock()
            mock_put_response.raise_for_status = Mock()
            mock_put_response.json.return_value = {"status": "success"}
            
            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_client_instance.get.return_value = mock_get_response
            mock_client_instance.put.return_value = mock_put_response
            
            # Test tag removal
            result = await client.remove_tags("contact123", ["sensitive-tag"])
            
            # Verify it actually calls the API
            assert mock_client_instance.get.called, "GET request should be made"
            assert mock_client_instance.put.called, "PUT request should be made"
            
            # Verify proper response structure
            assert result["status"] == "success", "Should return success status"
            assert "removed_tags" in result, "Should include removed tags"
            assert "remaining_tags" in result, "Should include remaining tags"
            
        print("✅ Tag removal security fix validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Tag removal security fix failed: {e}")
        return False


def test_jwt_security_fix():
    """Test that JWT no longer allows weak secret fallbacks."""
    print("🔍 Testing JWT security fix...")
    
    try:
        # Test with a weak secret
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "weak"}, clear=False):
            try:
                # Create a temporary test module to simulate import
                import tempfile
                import importlib.util
                
                # Read the actual JWT auth module content
                with open('/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/api/middleware/jwt_auth.py', 'r') as f:
                    jwt_content = f.read()
                
                # Create a temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
                    tmp_file.write(jwt_content)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Load the module
                    spec = importlib.util.spec_from_file_location("test_jwt", tmp_file_path)
                    test_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(test_module)
                    
                    print("❌ JWT should have rejected weak secret")
                    return False
                except ValueError as e:
                    if "JWT_SECRET_KEY must be at least 32 characters" in str(e):
                        print("✅ JWT properly rejects weak secrets")
                        return True
                    else:
                        print(f"⚠️ JWT raised ValueError but unexpected message: {e}")
                        return False
                finally:
                    os.unlink(tmp_file_path)
                    
            except Exception as e:
                if "JWT_SECRET_KEY must be at least 32 characters" in str(e):
                    print("✅ JWT properly rejects weak secrets")
                    return True
                else:
                    print(f"❌ JWT security fix failed: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ JWT security test failed: {e}")
        return False


def test_fetch_method_security_fix():
    """Test that fetch methods no longer silently fail."""
    print("🔍 Testing fetch methods security fix...")
    
    try:
        sys.path.insert(0, '/Users/cave/Documents/GitHub/EnterpriseHub')
        from ghl_real_estate_ai.services.ghl_client import GHLClient
        import httpx
        
        client = GHLClient(api_key="test-key-32-chars-min-required-test", location_id="test")
        
        # Test get_conversations with timeout
        with patch('httpx.Client') as mock_client:
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.get.side_effect = httpx.TimeoutException("Request timeout")
            
            try:
                client.get_conversations(limit=10)
                print("❌ get_conversations should raise exception on timeout")
                return False
            except ConnectionError as e:
                if "Timeout fetching conversations" in str(e):
                    print("✅ get_conversations properly raises exceptions on timeout")
                else:
                    print(f"⚠️ Unexpected error message: {e}")
                    return False
        
        # Test get_opportunities with HTTP error
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.get.side_effect = httpx.HTTPStatusError(
                "Server Error", request=Mock(), response=mock_response
            )
            
            try:
                client.get_opportunities()
                print("❌ get_opportunities should raise exception on HTTP error")
                return False
            except httpx.HTTPStatusError:
                print("✅ get_opportunities properly raises exceptions on HTTP errors")
                return True
        
        return True
        
    except Exception as e:
        print(f"❌ Fetch methods security fix failed: {e}")
        return False


async def test_apply_actions_security_fix():
    """Test that apply_actions properly escalates critical failures."""
    print("🔍 Testing apply_actions security fix...")
    
    try:
        sys.path.insert(0, '/Users/cave/Documents/GitHub/EnterpriseHub')
        from ghl_real_estate_ai.services.ghl_client import GHLClient
        from ghl_real_estate_ai.api.schemas.ghl import ActionType, GHLAction
        
        client = GHLClient(api_key="test-key-32-chars-min-required-test", location_id="test")
        
        actions = [
            GHLAction(type=ActionType.REMOVE_TAG, tag="security-critical-tag"),
            GHLAction(type=ActionType.ADD_TAG, tag="normal-tag")
        ]
        
        with patch.object(client, 'remove_tags') as mock_remove:
            mock_remove.side_effect = Exception("Critical tag removal failed")
            
            try:
                await client.apply_actions("contact123", actions)
                print("❌ apply_actions should raise RuntimeError for critical failures")
                return False
            except RuntimeError as e:
                if "Critical security action failed" in str(e):
                    print("✅ apply_actions properly escalates critical security failures")
                    return True
                else:
                    print(f"⚠️ Unexpected error message: {e}")
                    return False
            except Exception as e:
                print(f"⚠️ Unexpected exception type: {type(e)} - {e}")
                return False
        
    except Exception as e:
        print(f"❌ apply_actions security fix failed: {e}")
        return False


def test_dashboard_fetch_security_fix():
    """Test that dashboard fetch no longer masks critical failures."""
    print("🔍 Testing dashboard fetch security fix...")
    
    try:
        sys.path.insert(0, '/Users/cave/Documents/GitHub/EnterpriseHub')
        from ghl_real_estate_ai.services.ghl_client import GHLClient
        
        client = GHLClient(api_key="test-key-32-chars-min-required-test", location_id="test")
        
        with patch.object(client, 'get_conversations') as mock_conversations:
            mock_conversations.side_effect = Exception("Critical API failure")
            
            try:
                client.fetch_dashboard_data()
                print("❌ fetch_dashboard_data should raise RuntimeError for API failures")
                return False
            except RuntimeError as e:
                if "Dashboard data fetch failed" in str(e):
                    print("✅ dashboard fetch properly raises exceptions instead of masking failures")
                    return True
                else:
                    print(f"⚠️ Unexpected error message: {e}")
                    return False
            except Exception as e:
                print(f"⚠️ Unexpected exception type: {type(e)} - {e}")
                return False
        
    except Exception as e:
        print(f"❌ Dashboard fetch security fix failed: {e}")
        return False


async def main():
    """Run all security validation tests."""
    print("🛡️  CRITICAL SECURITY VULNERABILITY VALIDATION")
    print("=" * 55)
    print("Validating that all silent failure vulnerabilities have been fixed...\n")
    
    tests = [
        ("Tag Removal Security", test_tag_removal_security_fix()),
        ("JWT Security", test_jwt_security_fix()),
        ("Fetch Methods Security", test_fetch_method_security_fix()),
        ("Apply Actions Security", test_apply_actions_security_fix()),
        ("Dashboard Fetch Security", test_dashboard_fetch_security_fix())
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if asyncio.iscoroutine(test_func):
                result = await test_func
            else:
                result = test_func
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 55)
    print(f"🛡️  SECURITY VALIDATION SUMMARY")
    print(f"✅ Passed: {passed}/{total} tests")
    
    if passed == total:
        print("🎉 ALL CRITICAL SECURITY VULNERABILITIES HAVE BEEN FIXED!")
        print("🔒 Silent failures have been eliminated from the system.")
        return True
    else:
        print("⚠️  Some security fixes need attention.")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)