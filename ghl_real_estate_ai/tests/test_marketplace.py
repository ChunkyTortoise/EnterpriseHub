"""
Tests for Workflow Marketplace functionality
"""

import unittest
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ghl_real_estate_ai.services.workflow_marketplace import WorkflowMarketplaceService, TemplateSortBy
from ghl_real_estate_ai.services.template_installer import TemplateInstallerService
from ghl_real_estate_ai.services.template_manager import TemplateManagerService


class TestWorkflowMarketplace(unittest.TestCase):
    """Test workflow marketplace service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.marketplace = WorkflowMarketplaceService()
    
    def test_load_templates(self):
        """Test that templates are loaded"""
        self.assertGreater(len(self.marketplace.templates), 0, "Should load templates")
        self.assertGreater(len(self.marketplace.categories), 0, "Should load categories")
    
    def test_browse_all(self):
        """Test browsing all templates"""
        templates = self.marketplace.browse_templates()
        self.assertGreater(len(templates), 0, "Should return templates")
    
    def test_browse_by_category(self):
        """Test filtering by category"""
        templates = self.marketplace.browse_templates(category="lead_nurturing")
        self.assertGreater(len(templates), 0, "Should find lead nurturing templates")
        for template in templates:
            self.assertEqual(template.category, "lead_nurturing")
    
    def test_search(self):
        """Test search functionality"""
        results = self.marketplace.search_templates("welcome")
        self.assertGreater(len(results), 0, "Should find templates with 'welcome'")
    
    def test_filter_by_rating(self):
        """Test rating filter"""
        templates = self.marketplace.browse_templates(min_rating=4.5)
        self.assertGreater(len(templates), 0, "Should find highly rated templates")
        for template in templates:
            self.assertGreaterEqual(template.rating, 4.5)
    
    def test_filter_free_only(self):
        """Test free templates filter"""
        templates = self.marketplace.browse_templates(max_price=0)
        self.assertGreater(len(templates), 0, "Should find free templates")
        for template in templates:
            self.assertEqual(template.price, 0)
    
    def test_get_popular(self):
        """Test getting popular templates"""
        popular = self.marketplace.get_popular_templates(5)
        self.assertEqual(len(popular), 5, "Should return 5 popular templates")
        # Check they're sorted by downloads
        downloads = [t.downloads_count for t in popular]
        self.assertEqual(downloads, sorted(downloads, reverse=True))
    
    def test_get_featured(self):
        """Test getting featured templates"""
        featured = self.marketplace.get_featured_templates()
        self.assertGreater(len(featured), 0, "Should have featured templates")
        for template in featured:
            self.assertTrue(template.is_featured)
    
    def test_get_template_details(self):
        """Test getting specific template"""
        templates = self.marketplace.browse_templates(limit=1)
        if templates:
            template_id = templates[0].id
            details = self.marketplace.get_template_details(template_id)
            self.assertIsNotNone(details)
            self.assertEqual(details.id, template_id)
    
    def test_get_similar_templates(self):
        """Test similar templates recommendation"""
        templates = self.marketplace.browse_templates(limit=1)
        if templates:
            similar = self.marketplace.get_similar_templates(templates[0].id)
            self.assertIsInstance(similar, list)
    
    def test_marketplace_stats(self):
        """Test marketplace statistics"""
        stats = self.marketplace.get_stats()
        self.assertIn('total_templates', stats)
        self.assertIn('free_templates', stats)
        self.assertIn('premium_templates', stats)
        self.assertGreater(stats['total_templates'], 0)


class TestTemplateInstaller(unittest.TestCase):
    """Test template installer service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.installer = TemplateInstallerService()
        self.marketplace = WorkflowMarketplaceService()
    
    def test_validate_customizations(self):
        """Test customization validation"""
        templates = self.marketplace.browse_templates(limit=1)
        if templates:
            template = templates[0].__dict__
            customizations = {}
            for var in template.get('variables', []):
                customizations[var['name']] = "test_value"
            
            validation = self.installer.validate_customizations(template, customizations)
            self.assertTrue(validation['is_valid'])
    
    def test_preview_installation(self):
        """Test installation preview"""
        templates = self.marketplace.browse_templates(limit=1)
        if templates:
            template = templates[0].__dict__
            preview = self.installer.preview_installation(template)
            self.assertIn('name', preview)
            self.assertIn('steps_count', preview)
    
    def test_install_template(self):
        """Test template installation"""
        templates = self.marketplace.browse_templates(limit=1)
        if templates:
            template = templates[0].__dict__
            
            customizations = {}
            for var in template.get('variables', []):
                customizations[var['name']] = "TestValue"
            
            workflow = self.installer.install_template(
                template,
                tenant_id="test_user",
                customizations=customizations
            )
            
            self.assertIsNotNone(workflow)
            self.assertIn('workflow_id', workflow)
            self.assertEqual(workflow['created_by'], 'test_user')
    
    def test_installation_history(self):
        """Test getting installation history"""
        history = self.installer.get_installation_history()
        self.assertIsInstance(history, list)
    
    def test_installation_stats(self):
        """Test installation statistics"""
        stats = self.installer.get_installation_stats()
        self.assertIn('total_installations', stats)
        self.assertIn('unique_templates', stats)


class TestTemplateManager(unittest.TestCase):
    """Test template manager service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = TemplateManagerService()
    
    def test_export_workflow(self):
        """Test exporting workflow as template"""
        workflow = {
            "workflow_id": "test_workflow",
            "name": "Test Workflow",
            "description": "Test description",
            "trigger": {"trigger_type": "lead_created", "conditions": {}},
            "actions": [
                {
                    "action_id": "action_1",
                    "action_type": "send_sms",
                    "config": {"message": "Hi {{name}}!"},
                    "conditions": [],
                    "delay_seconds": 0
                }
            ]
        }
        
        template = self.manager.export_workflow_as_template(
            workflow,
            metadata={"name": "Test Template", "category": "lead_nurturing"}
        )
        
        self.assertIn('id', template)
        self.assertEqual(template['name'], "Test Template")
        self.assertGreater(len(template['variables']), 0)
    
    def test_validate_template(self):
        """Test template validation"""
        template = {
            "name": "Valid Template",
            "description": "A valid template for testing",
            "category": "lead_nurturing",
            "trigger": "lead_created",
            "workflow": {
                "actions": [{"action_type": "send_sms"}]
            },
            "icon": "👋"
        }
        
        validation = self.manager.validate_template(template)
        self.assertTrue(validation.is_valid)
    
    def test_validate_invalid_template(self):
        """Test validation catches errors"""
        template = {
            "name": "X",  # Too short
            "description": "",  # Too short
            "category": "invalid_category",
            "trigger": "lead_created",
            "workflow": {"actions": []},  # No actions
            "icon": "👋"
        }
        
        validation = self.manager.validate_template(template)
        self.assertFalse(validation.is_valid)
        self.assertGreater(len(validation.errors), 0)
    
    def test_customize_template(self):
        """Test template customization"""
        template = {
            "workflow": {
                "actions": [
                    {
                        "config": {
                            "message": "Hi {{firstName}}, I'm {{agentName}}!"
                        }
                    }
                ]
            }
        }
        
        customizations = {
            "firstName": "John",
            "agentName": "Sarah"
        }
        
        customized = self.manager.customize_template(template, customizations)
        message = customized['actions'][0]['config']['message']
        
        self.assertIn("John", message)
        self.assertIn("Sarah", message)
        self.assertNotIn("{{", message)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        """Set up services"""
        self.marketplace = WorkflowMarketplaceService()
        self.installer = TemplateInstallerService()
        self.manager = TemplateManagerService()
    
    def test_complete_installation_flow(self):
        """Test complete flow: browse -> select -> customize -> install"""
        # 1. Browse templates
        templates = self.marketplace.browse_templates(category="lead_nurturing", limit=1)
        self.assertGreater(len(templates), 0, "Should find templates")
        
        template = templates[0]
        
        # 2. Get details
        details = self.marketplace.get_template_details(template.id)
        self.assertIsNotNone(details)
        
        # 3. Preview installation
        customizations = {var['name']: "TestValue" for var in details.variables}
        preview = self.installer.preview_installation(details.__dict__, customizations)
        self.assertIn('name', preview)
        
        # 4. Validate customizations
        validation = self.installer.validate_customizations(details.__dict__, customizations)
        self.assertTrue(validation['is_valid'])
        
        # 5. Install
        workflow = self.installer.install_template(
            details.__dict__,
            tenant_id="integration_test",
            customizations=customizations
        )
        self.assertIsNotNone(workflow)
        self.assertIn('workflow_id', workflow)
    
    def test_template_export_and_publish(self):
        """Test exporting and publishing a template"""
        # Create a workflow
        workflow = {
            "workflow_id": "export_test",
            "name": "Export Test",
            "description": "Test workflow for export",
            "trigger": {"trigger_type": "lead_created", "conditions": {}},
            "actions": [
                {
                    "action_id": "a1",
                    "action_type": "send_sms",
                    "config": {"message": "Hello {{name}}!"},
                    "conditions": [],
                    "delay_seconds": 0
                }
            ]
        }
        
        # Export as template
        template = self.manager.export_workflow_as_template(
            workflow,
            metadata={
                "name": "Exported Template",
                "description": "This is an exported template",
                "category": "custom",
                "tags": ["test", "export"]
            }
        )
        
        # Validate
        validation = self.manager.validate_template(template)
        self.assertTrue(validation.is_valid)
        
        # Publish privately
        published = self.manager.publish_template(template, visibility="private")
        self.assertIn('id', published)


def run_tests():
    """Run all tests"""
    print("🧪 Running Marketplace Tests\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowMarketplace))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateInstaller))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
