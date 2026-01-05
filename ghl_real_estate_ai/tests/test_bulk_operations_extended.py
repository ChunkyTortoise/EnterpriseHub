"""
Comprehensive tests for bulk_operations module
Target: 80%+ coverage (from 11%)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import json
from datetime import datetime

from ghl_real_estate_ai.services.bulk_operations import BulkOperationsManager


class TestBulkOperationsManager:
    """Comprehensive test suite for BulkOperationsManager."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """Create manager instance with temp directory."""
        with patch('ghl_real_estate_ai.services.bulk_operations.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            manager = BulkOperationsManager(location_id="test_location")
            manager.operations_dir = tmp_path / "bulk_operations" / "test_location"
            manager.operations_dir.mkdir(parents=True, exist_ok=True)
            manager.operations_file = manager.operations_dir / "operations.json"
            return manager
    
    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager.location_id == "test_location"
        assert isinstance(manager.operations_history, dict)
        assert "operations" in manager.operations_history
        assert "templates" in manager.operations_history
    
    def test_create_operation_basic(self, manager):
        """Test creating a basic bulk operation."""
        operation_id = manager.create_operation(
            operation_type="tag",
            target_leads=["lead1", "lead2", "lead3"],
            parameters={"tags": ["test_tag"]},
            created_by="test_user"
        )
        
        assert operation_id.startswith("bulk_")
        assert len(manager.operations_history["operations"]) > 0
    
    def test_create_operation_score(self, manager):
        """Test creating a scoring operation."""
        operation_id = manager.create_operation(
            operation_type="score",
            target_leads=["lead1"],
            parameters={"criteria": "engagement"},
            created_by="system"
        )
        
        assert operation_id is not None
    
    def test_create_operation_message(self, manager):
        """Test creating a messaging operation."""
        operation_id = manager.create_operation(
            operation_type="message",
            target_leads=["lead1", "lead2"],
            parameters={"template": "welcome", "channel": "sms"},
            created_by="test_user"
        )
        
        assert operation_id is not None
    
    def test_create_operation_empty_leads(self, manager):
        """Test operation with empty leads list."""
        operation_id = manager.create_operation(
            operation_type="tag",
            target_leads=[],
            parameters={"tags": ["test"]},
            created_by="test_user"
        )
        
        assert operation_id is not None
    
    def test_create_operation_large_batch(self, manager):
        """Test operation with large number of leads."""
        leads = [f"lead_{i}" for i in range(1000)]
        operation_id = manager.create_operation(
            operation_type="export",
            target_leads=leads,
            parameters={"format": "csv"},
            created_by="test_user"
        )
        
        assert operation_id is not None
    
    def test_load_operations_no_file(self, tmp_path):
        """Test loading operations when file doesn't exist."""
        with patch('ghl_real_estate_ai.services.bulk_operations.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            manager = BulkOperationsManager(location_id="new_location")
            history = manager._load_operations()
            
            assert "operations" in history
            assert "templates" in history
            assert isinstance(history["operations"], list)
    
    def test_load_operations_existing_file(self, tmp_path):
        """Test loading operations from existing file."""
        ops_dir = tmp_path / "bulk_operations" / "test_loc"
        ops_dir.mkdir(parents=True, exist_ok=True)
        ops_file = ops_dir / "operations.json"
        
        test_data = {
            "operations": [{"id": "test1"}],
            "templates": {"template1": {}}
        }
        ops_file.write_text(json.dumps(test_data))
        
        with patch('ghl_real_estate_ai.services.bulk_operations.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            manager = BulkOperationsManager(location_id="test_loc")
            manager.operations_file = ops_file
            history = manager._load_operations()
            
            assert len(history["operations"]) == 1
            assert "template1" in history["templates"]
    
    def test_save_operations(self, manager):
        """Test saving operations to file."""
        manager.operations_history["operations"].append({"id": "test_op"})
        manager._save_operations()
        
        assert manager.operations_file.exists()
        data = json.loads(manager.operations_file.read_text())
        assert len(data["operations"]) > 0
    
    def test_operation_types(self, manager):
        """Test all supported operation types."""
        types = ["score", "message", "tag", "assign", "stage", "export"]
        
        for op_type in types:
            operation_id = manager.create_operation(
                operation_type=op_type,
                target_leads=["lead1"],
                parameters={},
                created_by="test"
            )
            assert operation_id is not None


class TestBulkOperationsEdgeCases:
    """Test edge cases and error handling."""
    
    def test_invalid_operation_type(self):
        """Test handling of invalid operation type."""
        manager = BulkOperationsManager(location_id="test")
        # Should handle gracefully
        operation_id = manager.create_operation(
            operation_type="invalid_type",
            target_leads=["lead1"],
            parameters={},
            created_by="test"
        )
        assert operation_id is not None
    
    def test_malformed_parameters(self):
        """Test handling of malformed parameters."""
        manager = BulkOperationsManager(location_id="test")
        operation_id = manager.create_operation(
            operation_type="tag",
            target_leads=["lead1"],
            parameters=None,  # Invalid
            created_by="test"
        )
        # Should handle gracefully or raise appropriate error
    
    def test_special_characters_in_leads(self):
        """Test leads with special characters."""
        manager = BulkOperationsManager(location_id="test")
        operation_id = manager.create_operation(
            operation_type="tag",
            target_leads=["lead@#$%", "lead!@#"],
            parameters={"tags": ["test"]},
            created_by="test"
        )
        assert operation_id is not None


class TestBulkOperationsIntegration:
    """Integration tests for bulk operations."""
    
    def test_create_and_retrieve_operation(self):
        """Test creating and retrieving an operation."""
        manager = BulkOperationsManager(location_id="integration_test")
        
        operation_id = manager.create_operation(
            operation_type="tag",
            target_leads=["lead1", "lead2"],
            parameters={"tags": ["integration_test"]},
            created_by="tester"
        )
        
        assert operation_id in str(manager.operations_history)
    
    def test_multiple_operations_same_location(self):
        """Test multiple operations for same location."""
        manager = BulkOperationsManager(location_id="multi_test")
        
        for i in range(5):
            operation_id = manager.create_operation(
                operation_type="tag",
                target_leads=[f"lead_{i}"],
                parameters={"tags": [f"tag_{i}"]},
                created_by="tester"
            )
            assert operation_id is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ghl_real_estate_ai.services.bulk_operations"])
