---
name: Subagent-Driven Development
description: This skill should be used when coordinating "multiple specialized agents", "complex workflow orchestration", "autonomous development teams", "agent collaboration", "distributed task management", or when managing sophisticated multi-agent development processes.
version: 1.0.0
---

# Subagent-Driven Development: Multi-Agent Coordination

## Overview

This skill provides comprehensive patterns for orchestrating multiple specialized agents in complex development workflows. It enables sophisticated coordination between autonomous agents, each with specific expertise and responsibilities.

## When to Use This Skill

Use this skill when implementing:
- **Multi-agent development workflows** with specialized roles
- **Complex task orchestration** requiring multiple expertise areas
- **Autonomous development teams** with agent coordination
- **Parallel workflow execution** with dependency management
- **Agent collaboration patterns** for complex problems
- **Distributed task management** across multiple agents
- **Quality assurance through specialized reviewers**

## Core Orchestration Architecture

### 1. Agent Taxonomy and Roles

```python
"""
Comprehensive agent taxonomy and role definitions
"""

from typing import Dict, Any, List, Optional, Union, Callable, Protocol
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import json
import logging
from datetime import datetime, timedelta
import uuid


class AgentType(Enum):
    """Types of specialized agents in the development ecosystem."""
    ARCHITECT = "architect"           # System design and architecture
    DEVELOPER = "developer"           # Code implementation
    TESTER = "tester"                # Testing and quality assurance
    REVIEWER = "reviewer"             # Code review and analysis
    SECURITY = "security"             # Security analysis and hardening
    PERFORMANCE = "performance"       # Performance optimization
    DOCUMENTATION = "documentation"   # Documentation creation
    DEVOPS = "devops"                # Deployment and infrastructure
    UI_UX = "ui_ux"                  # User interface and experience
    DATA = "data"                    # Data analysis and processing
    COORDINATOR = "coordinator"       # Workflow coordination
    QUALITY_GATE = "quality_gate"    # Quality gatekeeper


class AgentStatus(Enum):
    """Status states for agents during execution."""
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    BLOCKED = "blocked"


class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class AgentCapability:
    """Defines a specific capability an agent possesses."""
    name: str
    description: str
    expertise_level: int  # 1-10 scale
    prerequisites: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    estimated_duration: Optional[timedelta] = None


@dataclass
class Task:
    """Represents a task to be executed by an agent."""
    id: str
    title: str
    description: str
    agent_type: AgentType
    priority: Priority
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: Optional[timedelta] = None
    deadline: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"
    assigned_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'agent_type': self.agent_type.value,
            'priority': self.priority.value,
            'input_data': self.input_data,
            'dependencies': self.dependencies,
            'estimated_duration': self.estimated_duration.total_seconds() if self.estimated_duration else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'status': self.status,
            'assigned_agent': self.assigned_agent,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
            'metadata': self.metadata
        }


@dataclass
class WorkflowState:
    """Represents the current state of a multi-agent workflow."""
    workflow_id: str
    name: str
    description: str
    tasks: List[Task]
    active_agents: Dict[str, AgentStatus]
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    workflow_status: str = "initialized"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (dependencies satisfied)."""
        ready = []
        for task in self.tasks:
            if (task.status == "pending" and
                all(dep in self.completed_tasks for dep in task.dependencies)):
                ready.append(task)
        return ready

    def get_critical_path(self) -> List[str]:
        """Calculate the critical path for workflow completion."""
        # Simplified critical path calculation
        task_graph = {}
        for task in self.tasks:
            task_graph[task.id] = {
                'duration': task.estimated_duration.total_seconds() if task.estimated_duration else 3600,
                'dependencies': task.dependencies
            }

        # This would implement proper critical path analysis
        # For now, return tasks in dependency order
        return [task.id for task in sorted(self.tasks, key=lambda t: len(t.dependencies))]


class BaseAgent(ABC):
    """Abstract base class for all specialized agents."""

    def __init__(self, agent_id: str, agent_type: AgentType, capabilities: List[AgentCapability]):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.status = AgentStatus.IDLE
        self.current_task: Optional[Task] = None
        self.logger = logging.getLogger(f"{agent_type.value}_{agent_id}")

    @abstractmethod
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a specific task and return results."""
        pass

    @abstractmethod
    async def validate_input(self, task: Task) -> bool:
        """Validate that the agent can execute the given task."""
        pass

    async def can_handle_task(self, task: Task) -> bool:
        """Check if this agent can handle the given task."""
        if task.agent_type != self.agent_type:
            return False
        return await self.validate_input(task)

    async def estimate_duration(self, task: Task) -> timedelta:
        """Estimate how long the task will take to complete."""
        # Default estimation logic
        base_duration = timedelta(hours=1)

        # Adjust based on task complexity
        complexity_multiplier = task.metadata.get('complexity', 1.0)

        # Adjust based on agent expertise
        expertise_multiplier = 1.0
        for capability in self.capabilities:
            if capability.name.lower() in task.description.lower():
                expertise_multiplier = max(0.5, 1.0 - (capability.expertise_level / 20))
                break

        return base_duration * complexity_multiplier * expertise_multiplier

    def get_status_report(self) -> Dict[str, Any]:
        """Get current status report for this agent."""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'status': self.status.value,
            'current_task': self.current_task.id if self.current_task else None,
            'capabilities': [cap.name for cap in self.capabilities],
            'last_updated': datetime.now().isoformat()
        }


class ArchitectAgent(BaseAgent):
    """Agent specialized in system architecture and design."""

    def __init__(self, agent_id: str = "architect_001"):
        capabilities = [
            AgentCapability(
                name="System Design",
                description="Design scalable system architectures",
                expertise_level=9,
                outputs=["architecture_diagram", "design_document", "component_specification"]
            ),
            AgentCapability(
                name="Technology Selection",
                description="Choose appropriate technologies and frameworks",
                expertise_level=8,
                outputs=["technology_stack", "framework_recommendations", "tool_selection"]
            ),
            AgentCapability(
                name="Scalability Analysis",
                description="Analyze and design for system scalability",
                expertise_level=9,
                outputs=["scalability_plan", "performance_requirements", "bottleneck_analysis"]
            ),
            AgentCapability(
                name="Security Architecture",
                description="Design secure system architectures",
                expertise_level=7,
                outputs=["security_design", "threat_model", "security_requirements"]
            )
        ]
        super().__init__(agent_id, AgentType.ARCHITECT, capabilities)

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute architecture-related tasks."""
        self.status = AgentStatus.THINKING
        self.current_task = task

        try:
            task_type = task.metadata.get('task_type', 'general_design')

            if task_type == 'system_design':
                result = await self._design_system_architecture(task)
            elif task_type == 'technology_selection':
                result = await self._select_technologies(task)
            elif task_type == 'scalability_analysis':
                result = await self._analyze_scalability(task)
            elif task_type == 'security_architecture':
                result = await self._design_security_architecture(task)
            else:
                result = await self._general_architectural_analysis(task)

            self.status = AgentStatus.COMPLETED
            return result

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Task execution failed: {e}")
            raise

    async def validate_input(self, task: Task) -> bool:
        """Validate architectural task inputs."""
        required_fields = ['requirements', 'constraints']
        return all(field in task.input_data for field in required_fields)

    async def _design_system_architecture(self, task: Task) -> Dict[str, Any]:
        """Design comprehensive system architecture."""
        requirements = task.input_data['requirements']
        constraints = task.input_data.get('constraints', {})

        # Simulate architectural design process
        await asyncio.sleep(2)  # Simulate thinking time

        return {
            'architecture_type': 'microservices' if requirements.get('scalability') else 'monolithic',
            'components': [
                {
                    'name': 'API Gateway',
                    'type': 'service',
                    'responsibilities': ['routing', 'authentication', 'rate_limiting'],
                    'technology': 'Kong' if constraints.get('cloud_native') else 'Nginx'
                },
                {
                    'name': 'User Service',
                    'type': 'microservice',
                    'responsibilities': ['user_management', 'authentication', 'authorization'],
                    'technology': 'FastAPI' if requirements.get('python_preferred') else 'Node.js'
                },
                {
                    'name': 'Database Layer',
                    'type': 'data',
                    'responsibilities': ['data_persistence', 'data_integrity'],
                    'technology': 'PostgreSQL' if requirements.get('relational') else 'MongoDB'
                }
            ],
            'communication_patterns': ['REST', 'Event-driven'],
            'deployment_strategy': 'containerized',
            'monitoring_strategy': 'distributed_tracing',
            'estimated_complexity': 'medium',
            'implementation_phases': [
                'Core infrastructure setup',
                'Basic service implementation',
                'Integration and testing',
                'Performance optimization'
            ]
        }

    async def _select_technologies(self, task: Task) -> Dict[str, Any]:
        """Select appropriate technologies for the project."""
        requirements = task.input_data['requirements']
        constraints = task.input_data.get('constraints', {})

        await asyncio.sleep(1)

        return {
            'backend_framework': 'FastAPI' if requirements.get('python_preferred') else 'Express.js',
            'frontend_framework': 'React' if requirements.get('interactive_ui') else 'Streamlit',
            'database': 'PostgreSQL' if requirements.get('complex_queries') else 'SQLite',
            'caching': 'Redis' if requirements.get('high_performance') else 'In-memory',
            'deployment': 'Docker + Kubernetes' if requirements.get('cloud_native') else 'Traditional',
            'monitoring': 'Prometheus + Grafana',
            'ci_cd': 'GitHub Actions',
            'rationale': {
                'backend': 'FastAPI chosen for Python ecosystem compatibility and automatic API documentation',
                'frontend': 'React selected for rich interactivity requirements',
                'database': 'PostgreSQL for ACID compliance and complex querying capabilities'
            }
        }

    async def _analyze_scalability(self, task: Task) -> Dict[str, Any]:
        """Analyze system scalability requirements and design."""
        requirements = task.input_data['requirements']
        current_load = task.input_data.get('current_load', {})
        expected_growth = task.input_data.get('expected_growth', {})

        await asyncio.sleep(2)

        return {
            'current_capacity': current_load,
            'projected_capacity': {
                'users': expected_growth.get('users', 1000) * 5,
                'requests_per_second': expected_growth.get('rps', 100) * 10,
                'data_volume': expected_growth.get('data_gb', 10) * 20
            },
            'bottlenecks': [
                {
                    'component': 'database',
                    'issue': 'connection_limit',
                    'mitigation': 'connection_pooling'
                },
                {
                    'component': 'api_server',
                    'issue': 'cpu_bound_processing',
                    'mitigation': 'horizontal_scaling'
                }
            ],
            'scaling_strategies': [
                'horizontal_scaling',
                'database_sharding',
                'caching_layer',
                'cdn_integration'
            ],
            'implementation_priority': [
                'connection_pooling',
                'caching_implementation',
                'load_balancing',
                'database_optimization'
            ]
        }

    async def _design_security_architecture(self, task: Task) -> Dict[str, Any]:
        """Design security architecture for the system."""
        requirements = task.input_data['requirements']
        threat_model = task.input_data.get('threats', [])

        await asyncio.sleep(1.5)

        return {
            'authentication_strategy': 'JWT + OAuth2',
            'authorization_model': 'RBAC',
            'data_encryption': {
                'at_rest': 'AES-256',
                'in_transit': 'TLS 1.3',
                'key_management': 'AWS KMS'
            },
            'security_layers': [
                'API_gateway_security',
                'application_security',
                'database_security',
                'infrastructure_security'
            ],
            'compliance_requirements': requirements.get('compliance', []),
            'security_controls': [
                'input_validation',
                'output_encoding',
                'secure_headers',
                'rate_limiting',
                'audit_logging'
            ],
            'monitoring': [
                'security_events',
                'anomaly_detection',
                'vulnerability_scanning'
            ]
        }

    async def _general_architectural_analysis(self, task: Task) -> Dict[str, Any]:
        """Perform general architectural analysis."""
        await asyncio.sleep(1)

        return {
            'analysis_type': 'general_architecture',
            'recommendations': [
                'Implement modular architecture for maintainability',
                'Use dependency injection for testability',
                'Implement comprehensive logging and monitoring',
                'Follow SOLID principles in design'
            ],
            'design_patterns': [
                'Repository Pattern for data access',
                'Factory Pattern for object creation',
                'Observer Pattern for event handling',
                'Strategy Pattern for algorithm selection'
            ],
            'quality_attributes': {
                'maintainability': 'high',
                'scalability': 'medium',
                'performance': 'medium',
                'security': 'high',
                'testability': 'high'
            }
        }


class DeveloperAgent(BaseAgent):
    """Agent specialized in code implementation and development."""

    def __init__(self, agent_id: str = "developer_001"):
        capabilities = [
            AgentCapability(
                name="Backend Development",
                description="Implement backend services and APIs",
                expertise_level=9,
                outputs=["api_implementation", "database_models", "business_logic"]
            ),
            AgentCapability(
                name="Frontend Development",
                description="Implement user interfaces and client-side logic",
                expertise_level=8,
                outputs=["ui_components", "frontend_logic", "user_interactions"]
            ),
            AgentCapability(
                name="Database Integration",
                description="Implement database access and data management",
                expertise_level=8,
                outputs=["database_layer", "orm_models", "data_access_patterns"]
            ),
            AgentCapability(
                name="API Development",
                description="Design and implement RESTful and GraphQL APIs",
                expertise_level=9,
                outputs=["api_endpoints", "api_documentation", "api_testing"]
            )
        ]
        super().__init__(agent_id, AgentType.DEVELOPER, capabilities)

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute development tasks."""
        self.status = AgentStatus.WORKING
        self.current_task = task

        try:
            task_type = task.metadata.get('task_type', 'general_development')

            if task_type == 'api_implementation':
                result = await self._implement_api(task)
            elif task_type == 'frontend_component':
                result = await self._implement_frontend_component(task)
            elif task_type == 'database_model':
                result = await self._implement_database_model(task)
            elif task_type == 'business_logic':
                result = await self._implement_business_logic(task)
            else:
                result = await self._general_development(task)

            self.status = AgentStatus.COMPLETED
            return result

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Development task failed: {e}")
            raise

    async def validate_input(self, task: Task) -> bool:
        """Validate development task inputs."""
        required_fields = ['specification', 'technology_stack']
        return all(field in task.input_data for field in required_fields)

    async def _implement_api(self, task: Task) -> Dict[str, Any]:
        """Implement API endpoints based on specification."""
        spec = task.input_data['specification']
        tech_stack = task.input_data['technology_stack']

        await asyncio.sleep(3)  # Simulate development time

        return {
            'implementation_type': 'api',
            'endpoints': [
                {
                    'path': endpoint['path'],
                    'method': endpoint['method'],
                    'implementation_status': 'completed',
                    'test_coverage': '95%',
                    'documentation_status': 'completed'
                }
                for endpoint in spec.get('endpoints', [])
            ],
            'framework': tech_stack.get('backend_framework', 'FastAPI'),
            'authentication': 'JWT implemented',
            'validation': 'Pydantic schemas implemented',
            'error_handling': 'Global exception handling implemented',
            'logging': 'Structured logging implemented',
            'files_created': [
                f"api/{endpoint['path'].replace('/', '_')}.py"
                for endpoint in spec.get('endpoints', [])
            ],
            'tests_created': [
                f"tests/test_{endpoint['path'].replace('/', '_')}.py"
                for endpoint in spec.get('endpoints', [])
            ]
        }

    async def _implement_frontend_component(self, task: Task) -> Dict[str, Any]:
        """Implement frontend components."""
        spec = task.input_data['specification']
        tech_stack = task.input_data['technology_stack']

        await asyncio.sleep(2.5)

        return {
            'implementation_type': 'frontend_component',
            'component_name': spec.get('component_name', 'UnknownComponent'),
            'framework': tech_stack.get('frontend_framework', 'React'),
            'features_implemented': spec.get('features', []),
            'styling': 'CSS modules implemented',
            'accessibility': 'WCAG 2.1 AA compliant',
            'responsive_design': 'Mobile-first approach',
            'state_management': 'Context API implemented',
            'files_created': [
                f"components/{spec.get('component_name', 'Unknown')}.jsx",
                f"components/{spec.get('component_name', 'Unknown')}.module.css",
                f"components/{spec.get('component_name', 'Unknown')}.test.jsx"
            ],
            'integration_points': spec.get('api_integrations', [])
        }

    async def _implement_database_model(self, task: Task) -> Dict[str, Any]:
        """Implement database models and data access layer."""
        spec = task.input_data['specification']
        tech_stack = task.input_data['technology_stack']

        await asyncio.sleep(2)

        return {
            'implementation_type': 'database_model',
            'orm': tech_stack.get('orm', 'SQLAlchemy'),
            'database': tech_stack.get('database', 'PostgreSQL'),
            'models_implemented': [
                {
                    'name': model['name'],
                    'fields': model.get('fields', []),
                    'relationships': model.get('relationships', []),
                    'indexes': model.get('indexes', []),
                    'validation': 'Implemented'
                }
                for model in spec.get('models', [])
            ],
            'migrations_created': True,
            'seed_data': 'Sample data created',
            'files_created': [
                f"models/{model['name'].lower()}.py"
                for model in spec.get('models', [])
            ],
            'repository_pattern': 'Implemented for data access abstraction'
        }

    async def _implement_business_logic(self, task: Task) -> Dict[str, Any]:
        """Implement business logic and domain services."""
        spec = task.input_data['specification']

        await asyncio.sleep(3.5)

        return {
            'implementation_type': 'business_logic',
            'services_implemented': [
                {
                    'name': service['name'],
                    'methods': service.get('methods', []),
                    'dependencies': service.get('dependencies', []),
                    'validation': 'Input/output validation implemented',
                    'error_handling': 'Domain-specific exceptions implemented'
                }
                for service in spec.get('services', [])
            ],
            'domain_events': 'Event system implemented',
            'validation_rules': 'Business rule validation implemented',
            'transaction_handling': 'Database transactions properly managed',
            'caching_strategy': 'Service-level caching implemented',
            'files_created': [
                f"services/{service['name'].lower()}_service.py"
                for service in spec.get('services', [])
            ]
        }

    async def _general_development(self, task: Task) -> Dict[str, Any]:
        """Handle general development tasks."""
        await asyncio.sleep(2)

        return {
            'implementation_type': 'general',
            'status': 'completed',
            'code_quality': 'high',
            'test_coverage': '90%',
            'documentation': 'inline_comments_and_docstrings',
            'performance_optimized': True,
            'security_considerations': 'implemented',
            'files_modified': task.input_data.get('target_files', []),
            'best_practices_followed': [
                'SOLID_principles',
                'DRY_principle',
                'clean_code_standards',
                'proper_error_handling',
                'comprehensive_testing'
            ]
        }


class QualityGateAgent(BaseAgent):
    """Agent specialized in quality gate enforcement and validation."""

    def __init__(self, agent_id: str = "quality_gate_001"):
        capabilities = [
            AgentCapability(
                name="Code Quality Analysis",
                description="Analyze code quality and enforce standards",
                expertise_level=9,
                outputs=["quality_report", "violation_list", "improvement_suggestions"]
            ),
            AgentCapability(
                name="Test Coverage Analysis",
                description="Analyze test coverage and quality",
                expertise_level=8,
                outputs=["coverage_report", "missing_tests", "test_quality_assessment"]
            ),
            AgentCapability(
                name="Security Validation",
                description="Validate security compliance and identify vulnerabilities",
                expertise_level=8,
                outputs=["security_report", "vulnerability_list", "compliance_status"]
            ),
            AgentCapability(
                name="Performance Validation",
                description="Validate performance requirements and identify bottlenecks",
                expertise_level=7,
                outputs=["performance_report", "bottleneck_analysis", "optimization_recommendations"]
            )
        ]
        super().__init__(agent_id, AgentType.QUALITY_GATE, capabilities)

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute quality gate validation."""
        self.status = AgentStatus.THINKING
        self.current_task = task

        try:
            validation_type = task.metadata.get('validation_type', 'comprehensive')

            if validation_type == 'code_quality':
                result = await self._validate_code_quality(task)
            elif validation_type == 'test_coverage':
                result = await self._validate_test_coverage(task)
            elif validation_type == 'security':
                result = await self._validate_security(task)
            elif validation_type == 'performance':
                result = await self._validate_performance(task)
            else:
                result = await self._comprehensive_validation(task)

            self.status = AgentStatus.COMPLETED
            return result

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Quality gate validation failed: {e}")
            raise

    async def validate_input(self, task: Task) -> bool:
        """Validate quality gate task inputs."""
        required_fields = ['target_artifacts', 'quality_standards']
        return all(field in task.input_data for field in required_fields)

    async def _validate_code_quality(self, task: Task) -> Dict[str, Any]:
        """Validate code quality against standards."""
        artifacts = task.input_data['target_artifacts']
        standards = task.input_data['quality_standards']

        await asyncio.sleep(2)

        violations = []
        score = 95  # Mock high score

        return {
            'validation_type': 'code_quality',
            'overall_score': score,
            'passed': score >= standards.get('min_quality_score', 80),
            'metrics': {
                'cyclomatic_complexity': 3.2,
                'maintainability_index': 78,
                'code_duplication': 2.1,
                'lines_of_code': 1250,
                'technical_debt_ratio': 1.8
            },
            'violations': violations,
            'recommendations': [
                'Extract complex methods into smaller functions',
                'Add more descriptive variable names',
                'Implement error handling in edge cases'
            ],
            'files_analyzed': len(artifacts),
            'standards_compliance': 'PASSED'
        }

    async def _validate_test_coverage(self, task: Task) -> Dict[str, Any]:
        """Validate test coverage requirements."""
        artifacts = task.input_data['target_artifacts']
        standards = task.input_data['quality_standards']

        await asyncio.sleep(1.5)

        coverage = 92  # Mock coverage
        min_coverage = standards.get('min_test_coverage', 80)

        return {
            'validation_type': 'test_coverage',
            'overall_coverage': coverage,
            'passed': coverage >= min_coverage,
            'coverage_by_type': {
                'line_coverage': 92,
                'branch_coverage': 88,
                'function_coverage': 95,
                'statement_coverage': 91
            },
            'uncovered_areas': [
                'Error handling in payment_service.py lines 45-50',
                'Edge case in user_validator.py lines 23-25'
            ],
            'test_quality_metrics': {
                'test_count': 156,
                'assertion_count': 312,
                'avg_assertions_per_test': 2.0,
                'test_execution_time': '2.3s'
            },
            'missing_tests': [
                'Integration test for user registration flow',
                'Performance test for search functionality'
            ],
            'recommendations': [
                'Add tests for error handling scenarios',
                'Implement property-based testing for data validation'
            ]
        }

    async def _validate_security(self, task: Task) -> Dict[str, Any]:
        """Validate security compliance."""
        artifacts = task.input_data['target_artifacts']
        standards = task.input_data['quality_standards']

        await asyncio.sleep(2.5)

        return {
            'validation_type': 'security',
            'security_score': 88,
            'passed': True,
            'vulnerabilities': [
                {
                    'type': 'LOW',
                    'description': 'Potential timing attack in password comparison',
                    'location': 'auth_service.py:45',
                    'recommendation': 'Use constant-time comparison function'
                }
            ],
            'compliance_checks': {
                'owasp_top_10': 'PASSED',
                'input_validation': 'PASSED',
                'authentication': 'PASSED',
                'authorization': 'PASSED',
                'data_encryption': 'PASSED',
                'secure_communication': 'PASSED',
                'error_handling': 'WARNING',
                'logging_security': 'PASSED'
            },
            'security_controls': {
                'implemented': [
                    'JWT token authentication',
                    'Input sanitization',
                    'SQL injection prevention',
                    'XSS protection',
                    'CSRF tokens'
                ],
                'missing': [
                    'Rate limiting on authentication endpoints',
                    'Account lockout mechanism'
                ]
            },
            'recommendations': [
                'Implement rate limiting for API endpoints',
                'Add account lockout after failed login attempts',
                'Use constant-time comparison for password validation'
            ]
        }

    async def _validate_performance(self, task: Task) -> Dict[str, Any]:
        """Validate performance requirements."""
        artifacts = task.input_data['target_artifacts']
        standards = task.input_data['quality_standards']

        await asyncio.sleep(2)

        return {
            'validation_type': 'performance',
            'performance_score': 85,
            'passed': True,
            'metrics': {
                'response_time_p95': '250ms',
                'response_time_p99': '500ms',
                'throughput': '1000 rps',
                'memory_usage': '128MB',
                'cpu_utilization': '45%'
            },
            'requirements_check': {
                'response_time': 'PASSED',
                'throughput': 'PASSED',
                'resource_usage': 'PASSED',
                'scalability': 'PASSED'
            },
            'bottlenecks': [
                {
                    'component': 'database_query',
                    'impact': 'medium',
                    'description': 'Complex join query in user search',
                    'recommendation': 'Add database index or optimize query'
                }
            ],
            'optimization_opportunities': [
                'Implement caching for frequently accessed data',
                'Optimize database queries with proper indexing',
                'Consider implementing pagination for large result sets'
            ]
        }

    async def _comprehensive_validation(self, task: Task) -> Dict[str, Any]:
        """Perform comprehensive quality validation."""
        # Run all validation types
        code_quality = await self._validate_code_quality(task)
        test_coverage = await self._validate_test_coverage(task)
        security = await self._validate_security(task)
        performance = await self._validate_performance(task)

        # Aggregate results
        overall_passed = all([
            code_quality['passed'],
            test_coverage['passed'],
            security['passed'],
            performance['passed']
        ])

        overall_score = (
            code_quality['overall_score'] +
            test_coverage['overall_coverage'] +
            security['security_score'] +
            performance['performance_score']
        ) / 4

        return {
            'validation_type': 'comprehensive',
            'overall_score': overall_score,
            'overall_passed': overall_passed,
            'validation_results': {
                'code_quality': code_quality,
                'test_coverage': test_coverage,
                'security': security,
                'performance': performance
            },
            'gate_status': 'PASSED' if overall_passed else 'FAILED',
            'critical_issues': [],
            'next_steps': [
                'Deploy to staging environment' if overall_passed else 'Address failing validations',
                'Monitor performance metrics',
                'Schedule security review'
            ]
        }


class WorkflowOrchestrator:
    """Central orchestrator for managing multi-agent workflows."""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, WorkflowState] = {}
        self.task_queue: List[Task] = []
        self.logger = logging.getLogger("WorkflowOrchestrator")

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id} ({agent.agent_type.value})")

    def create_workflow(self, workflow_id: str, name: str, description: str, tasks: List[Task]) -> WorkflowState:
        """Create a new workflow with the given tasks."""
        workflow = WorkflowState(
            workflow_id=workflow_id,
            name=name,
            description=description,
            tasks=tasks,
            active_agents={}
        )

        self.workflows[workflow_id] = workflow
        self.logger.info(f"Created workflow: {workflow_id}")
        return workflow

    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a complete workflow with proper coordination."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.workflow_status = "running"
        workflow.started_at = datetime.now()

        try:
            while workflow.workflow_status == "running":
                # Get ready tasks
                ready_tasks = workflow.get_ready_tasks()

                if not ready_tasks and not workflow.active_agents:
                    # No ready tasks and no active agents - workflow complete
                    break

                # Assign ready tasks to available agents
                for task in ready_tasks:
                    agent = await self._find_suitable_agent(task)
                    if agent and agent.status == AgentStatus.IDLE:
                        await self._assign_task_to_agent(task, agent, workflow)

                # Wait for some tasks to complete
                await asyncio.sleep(1)

                # Check for completed tasks
                await self._check_completed_tasks(workflow)

            # Finalize workflow
            await self._finalize_workflow(workflow)

            return {
                'workflow_id': workflow_id,
                'status': workflow.workflow_status,
                'completed_tasks': len(workflow.completed_tasks),
                'failed_tasks': len(workflow.failed_tasks),
                'total_tasks': len(workflow.tasks),
                'duration': (workflow.completed_at - workflow.started_at).total_seconds() if workflow.completed_at else None,
                'results': [task.result for task in workflow.tasks if task.result]
            }

        except Exception as e:
            workflow.workflow_status = "failed"
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            raise

    async def _find_suitable_agent(self, task: Task) -> Optional[BaseAgent]:
        """Find the most suitable agent for a given task."""
        suitable_agents = []

        for agent in self.agents.values():
            if await agent.can_handle_task(task):
                suitable_agents.append(agent)

        if not suitable_agents:
            return None

        # Select agent with highest expertise for the task type
        return max(suitable_agents, key=lambda a: max(
            (cap.expertise_level for cap in a.capabilities
             if cap.name.lower() in task.description.lower()),
            default=5
        ))

    async def _assign_task_to_agent(self, task: Task, agent: BaseAgent, workflow: WorkflowState):
        """Assign a task to an agent and start execution."""
        task.assigned_agent = agent.agent_id
        task.started_at = datetime.now()
        task.status = "in_progress"

        workflow.active_agents[agent.agent_id] = AgentStatus.WORKING

        self.logger.info(f"Assigned task {task.id} to agent {agent.agent_id}")

        # Start task execution asynchronously
        asyncio.create_task(self._execute_agent_task(task, agent, workflow))

    async def _execute_agent_task(self, task: Task, agent: BaseAgent, workflow: WorkflowState):
        """Execute a task with an agent (async wrapper)."""
        try:
            result = await agent.execute_task(task)
            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now()

            workflow.completed_tasks.append(task.id)
            workflow.active_agents[agent.agent_id] = AgentStatus.IDLE

            self.logger.info(f"Task {task.id} completed successfully")

        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            task.completed_at = datetime.now()

            workflow.failed_tasks.append(task.id)
            workflow.active_agents[agent.agent_id] = AgentStatus.ERROR

            self.logger.error(f"Task {task.id} failed: {e}")

            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = "pending"
                self.logger.info(f"Retrying task {task.id} (attempt {task.retry_count})")

    async def _check_completed_tasks(self, workflow: WorkflowState):
        """Check for completed tasks and update workflow state."""
        total_tasks = len(workflow.tasks)
        completed_or_failed = len(workflow.completed_tasks) + len(workflow.failed_tasks)

        if completed_or_failed >= total_tasks:
            workflow.workflow_status = "completed"

    async def _finalize_workflow(self, workflow: WorkflowState):
        """Finalize the workflow and generate summary."""
        workflow.completed_at = datetime.now()

        if len(workflow.failed_tasks) == 0:
            workflow.workflow_status = "completed_successfully"
        elif len(workflow.completed_tasks) > 0:
            workflow.workflow_status = "partially_completed"
        else:
            workflow.workflow_status = "failed"

        self.logger.info(f"Workflow {workflow.workflow_id} finalized with status: {workflow.workflow_status}")

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {'error': 'Workflow not found'}

        return {
            'workflow_id': workflow_id,
            'status': workflow.workflow_status,
            'progress': {
                'total_tasks': len(workflow.tasks),
                'completed_tasks': len(workflow.completed_tasks),
                'failed_tasks': len(workflow.failed_tasks),
                'active_tasks': len([t for t in workflow.tasks if t.status == 'in_progress'])
            },
            'active_agents': {
                agent_id: status.value
                for agent_id, status in workflow.active_agents.items()
            },
            'estimated_completion': None,  # Could implement estimation logic
            'created_at': workflow.created_at.isoformat(),
            'started_at': workflow.started_at.isoformat() if workflow.started_at else None
        }

    def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get status summary of all registered agents."""
        return {
            'total_agents': len(self.agents),
            'agents_by_type': {
                agent_type.value: len([a for a in self.agents.values() if a.agent_type == agent_type])
                for agent_type in AgentType
            },
            'agents_by_status': {
                status.value: len([a for a in self.agents.values() if a.status == status])
                for status in AgentStatus
            },
            'agent_details': [agent.get_status_report() for agent in self.agents.values()]
        }
```

## Usage Examples

### Real Estate Development Workflow

```python
"""
Example: Real estate feature development workflow using multiple specialized agents
"""

async def create_real_estate_feature_workflow():
    """Create a workflow for developing a new real estate feature."""

    # Initialize orchestrator and agents
    orchestrator = WorkflowOrchestrator()

    # Register specialized agents
    architect = ArchitectAgent("architect_001")
    developer = DeveloperAgent("developer_001")
    quality_gate = QualityGateAgent("quality_gate_001")

    orchestrator.register_agent(architect)
    orchestrator.register_agent(developer)
    orchestrator.register_agent(quality_gate)

    # Define tasks for property matching feature
    tasks = [
        Task(
            id="arch_001",
            title="Design Property Matching System Architecture",
            description="Design scalable architecture for AI-powered property matching",
            agent_type=AgentType.ARCHITECT,
            priority=Priority.HIGH,
            input_data={
                'requirements': {
                    'scalability': True,
                    'python_preferred': True,
                    'ai_integration': True,
                    'real_time_matching': True
                },
                'constraints': {
                    'budget': 'medium',
                    'timeline': '6_weeks',
                    'team_size': 3
                }
            },
            metadata={'task_type': 'system_design', 'complexity': 2.0}
        ),

        Task(
            id="dev_001",
            title="Implement Property Matching API",
            description="Implement REST API for property matching functionality",
            agent_type=AgentType.DEVELOPER,
            priority=Priority.HIGH,
            input_data={
                'specification': {
                    'endpoints': [
                        {'path': '/api/v1/match', 'method': 'POST'},
                        {'path': '/api/v1/preferences', 'method': 'PUT'},
                        {'path': '/api/v1/matches/{user_id}', 'method': 'GET'}
                    ]
                },
                'technology_stack': {
                    'backend_framework': 'FastAPI',
                    'database': 'PostgreSQL',
                    'orm': 'SQLAlchemy'
                }
            },
            dependencies=["arch_001"],
            metadata={'task_type': 'api_implementation', 'complexity': 2.5}
        ),

        Task(
            id="dev_002",
            title="Implement Property Matching Models",
            description="Implement database models for properties and user preferences",
            agent_type=AgentType.DEVELOPER,
            priority=Priority.MEDIUM,
            input_data={
                'specification': {
                    'models': [
                        {
                            'name': 'Property',
                            'fields': ['id', 'address', 'price', 'bedrooms', 'bathrooms', 'features'],
                            'relationships': ['property_images', 'property_matches']
                        },
                        {
                            'name': 'UserPreferences',
                            'fields': ['user_id', 'budget_min', 'budget_max', 'location', 'features'],
                            'relationships': ['user', 'property_matches']
                        }
                    ]
                },
                'technology_stack': {
                    'orm': 'SQLAlchemy',
                    'database': 'PostgreSQL'
                }
            },
            dependencies=["arch_001"],
            metadata={'task_type': 'database_model', 'complexity': 1.5}
        ),

        Task(
            id="dev_003",
            title="Implement Matching Algorithm Service",
            description="Implement AI-powered property matching business logic",
            agent_type=AgentType.DEVELOPER,
            priority=Priority.HIGH,
            input_data={
                'specification': {
                    'services': [
                        {
                            'name': 'PropertyMatchingService',
                            'methods': ['calculate_match_score', 'find_matches', 'update_preferences'],
                            'dependencies': ['PropertyRepository', 'UserPreferencesRepository', 'MLService']
                        }
                    ]
                }
            },
            dependencies=["dev_002"],
            metadata={'task_type': 'business_logic', 'complexity': 3.0}
        ),

        Task(
            id="qa_001",
            title="Quality Gate Validation",
            description="Comprehensive quality validation for property matching feature",
            agent_type=AgentType.QUALITY_GATE,
            priority=Priority.CRITICAL,
            input_data={
                'target_artifacts': ['api_implementation', 'database_models', 'business_logic'],
                'quality_standards': {
                    'min_test_coverage': 85,
                    'min_quality_score': 80,
                    'security_compliance': 'required'
                }
            },
            dependencies=["dev_001", "dev_002", "dev_003"],
            metadata={'validation_type': 'comprehensive'}
        )
    ]

    # Create and execute workflow
    workflow_id = str(uuid.uuid4())
    workflow = orchestrator.create_workflow(
        workflow_id=workflow_id,
        name="Property Matching Feature Development",
        description="Complete development workflow for AI-powered property matching feature",
        tasks=tasks
    )

    # Execute workflow
    result = await orchestrator.execute_workflow(workflow_id)
    return result


# Example usage
async def demo_multi_agent_workflow():
    """Demonstrate multi-agent workflow execution."""

    print("🚀 Starting Multi-Agent Development Workflow")

    # Create and execute workflow
    result = await create_real_estate_feature_workflow()

    print(f"\n✅ Workflow completed!")
    print(f"Status: {result['status']}")
    print(f"Total tasks: {result['total_tasks']}")
    print(f"Completed: {result['completed_tasks']}")
    print(f"Failed: {result['failed_tasks']}")
    print(f"Duration: {result['duration']:.2f} seconds")

    # Display results from each agent
    for i, task_result in enumerate(result['results']):
        if task_result:
            print(f"\n📋 Task {i+1} Results:")
            print(f"Type: {task_result.get('implementation_type', 'Unknown')}")
            if 'files_created' in task_result:
                print(f"Files created: {len(task_result['files_created'])}")


# Integration with Streamlit
def create_workflow_dashboard():
    """Create a Streamlit dashboard for monitoring agent workflows."""

    import streamlit as st

    st.title("🤖 Multi-Agent Development Dashboard")

    # Initialize orchestrator (in real app, this would be persistent)
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = WorkflowOrchestrator()

        # Register some demo agents
        st.session_state.orchestrator.register_agent(ArchitectAgent())
        st.session_state.orchestrator.register_agent(DeveloperAgent())
        st.session_state.orchestrator.register_agent(QualityGateAgent())

    orchestrator = st.session_state.orchestrator

    # Agent Status Summary
    st.header("Agent Status")
    agent_summary = orchestrator.get_agent_status_summary()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Agents", agent_summary['total_agents'])
    with col2:
        idle_agents = agent_summary['agents_by_status'].get('idle', 0)
        st.metric("Available Agents", idle_agents)
    with col3:
        working_agents = agent_summary['agents_by_status'].get('working', 0)
        st.metric("Working Agents", working_agents)

    # Agent Details
    st.subheader("Agent Details")
    for agent_detail in agent_summary['agent_details']:
        with st.expander(f"{agent_detail['agent_id']} ({agent_detail['agent_type']})"):
            st.write(f"**Status:** {agent_detail['status']}")
            st.write(f"**Current Task:** {agent_detail['current_task'] or 'None'}")
            st.write(f"**Capabilities:** {', '.join(agent_detail['capabilities'])}")

    # Workflow Management
    st.header("Workflow Management")

    if st.button("Create Demo Workflow"):
        with st.spinner("Creating and executing workflow..."):
            # This would need to be adapted for Streamlit's sync nature
            st.success("Demo workflow creation started!")

    # Workflow Status
    if orchestrator.workflows:
        st.subheader("Active Workflows")
        for workflow_id, workflow in orchestrator.workflows.items():
            status = orchestrator.get_workflow_status(workflow_id)

            with st.expander(f"Workflow: {workflow.name}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Status:** {status['status']}")
                    st.write(f"**Progress:** {status['progress']['completed_tasks']}/{status['progress']['total_tasks']}")
                with col2:
                    st.write(f"**Created:** {status['created_at']}")
                    if status['started_at']:
                        st.write(f"**Started:** {status['started_at']}")

                # Progress bar
                if status['progress']['total_tasks'] > 0:
                    progress = status['progress']['completed_tasks'] / status['progress']['total_tasks']
                    st.progress(progress)
```

## Best Practices

1. **Clear Agent Responsibilities**: Each agent should have well-defined, non-overlapping responsibilities
2. **Proper Dependency Management**: Ensure task dependencies are correctly specified and enforced
3. **Error Handling**: Implement robust error handling and retry mechanisms
4. **Status Monitoring**: Provide comprehensive status monitoring and reporting
5. **Resource Management**: Prevent resource contention and ensure efficient agent utilization
6. **Quality Gates**: Implement quality validation at appropriate workflow stages
7. **Scalability**: Design for horizontal scaling of agent instances

This subagent-driven development skill provides a comprehensive framework for orchestrating complex multi-agent development workflows, particularly suited for the sophisticated requirements of the EnterpriseHub GHL Real Estate AI project.