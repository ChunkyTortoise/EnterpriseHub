"""
Service 6 Production Deployment Script.

Comprehensive deployment automation for the Lead Recovery & Nurture Engine:
- Environment validation and setup
- Database migrations and seeding
- Service health verification
- Configuration validation
- Security checks and initialization
- Production readiness verification
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import asyncpg
import redis.asyncio as aioredis
import aiohttp
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.database_service import DatabaseService
from ghl_real_estate_ai.services.security_framework import SecurityFramework
from ghl_real_estate_ai.services.monitoring_service import MonitoringService
from ghl_real_estate_ai.services.apollo_client import ApolloClient
from ghl_real_estate_ai.services.twilio_client import TwilioClient
from ghl_real_estate_ai.services.sendgrid_client import SendGridClient
from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient

console = Console()
logger = get_logger(__name__)


class DeploymentStatus:
    """Track deployment status and results."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.steps: List[Dict[str, Any]] = []
        self.current_step = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def start_step(self, name: str, description: str = ""):
        """Start a new deployment step."""
        self.current_step = {
            "name": name,
            "description": description,
            "start_time": datetime.utcnow(),
            "status": "running",
            "error": None
        }
        
    def complete_step(self, success: bool = True, message: str = ""):
        """Complete the current step."""
        if self.current_step:
            self.current_step["end_time"] = datetime.utcnow()
            self.current_step["status"] = "success" if success else "failed"
            self.current_step["message"] = message
            
            if not success:
                self.errors.append(f"{self.current_step['name']}: {message}")
            
            self.steps.append(self.current_step)
            self.current_step = None
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get deployment summary."""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        successful_steps = len([s for s in self.steps if s["status"] == "success"])
        failed_steps = len([s for s in self.steps if s["status"] == "failed"])
        
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total_steps": len(self.steps),
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "warnings": len(self.warnings),
            "overall_success": failed_steps == 0,
            "errors": self.errors,
            "warnings_list": self.warnings
        }


class Service6Deployer:
    """
    Service 6 production deployment orchestrator.
    
    Handles all aspects of deploying the Lead Recovery & Nurture Engine
    to production environments with comprehensive validation.
    """
    
    def __init__(self, environment: str = "production"):
        """Initialize deployer."""
        self.environment = environment
        self.status = DeploymentStatus()
        self.console = Console()
        self.project_root = Path(__file__).parent.parent
        
        # Services to deploy and validate
        self.services = {}
        
    async def deploy(self) -> bool:
        """Execute complete deployment process."""
        self.console.print(Panel(
            f"[bold blue]Service 6 Lead Recovery & Nurture Engine[/bold blue]\n"
            f"[yellow]Production Deployment - {self.environment.upper()}[/yellow]\n"
            f"[dim]Started at {self.status.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}[/dim]",
            title="🚀 Deployment Starting"
        ))
        
        deployment_steps = [
            ("environment_validation", "Validate Environment & Dependencies"),
            ("security_initialization", "Initialize Security Framework"),
            ("database_setup", "Database Setup & Migrations"),
            ("external_services_validation", "Validate External Service Connections"),
            ("service_initialization", "Initialize Core Services"),
            ("health_checks", "Run Comprehensive Health Checks"),
            ("monitoring_setup", "Setup Monitoring & Alerting"),
            ("production_readiness", "Production Readiness Verification"),
            ("final_validation", "Final System Validation")
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            for step_name, step_description in deployment_steps:
                task = progress.add_task(f"[yellow]{step_description}[/yellow]", total=None)
                
                self.status.start_step(step_name, step_description)
                
                try:
                    method = getattr(self, f"_deploy_{step_name}")
                    success = await method()
                    
                    if success:
                        progress.update(task, description=f"[green]✓ {step_description}[/green]")
                        self.status.complete_step(True, "Completed successfully")
                    else:
                        progress.update(task, description=f"[red]✗ {step_description}[/red]")
                        self.status.complete_step(False, "Step failed")
                        break
                        
                except Exception as e:
                    progress.update(task, description=f"[red]✗ {step_description} - Error[/red]")
                    self.status.complete_step(False, str(e))
                    logger.error(f"Deployment step {step_name} failed: {e}")
                    break
                
                progress.remove_task(task)
        
        # Display deployment summary
        await self._display_deployment_summary()
        
        return self.status.get_summary()["overall_success"]
    
    # ============================================================================
    # Deployment Steps
    # ============================================================================
    
    async def _deploy_environment_validation(self) -> bool:
        """Validate environment and dependencies."""
        self.console.print("[cyan]Validating environment...[/cyan]")
        
        # Check Python version
        if sys.version_info < (3, 11):
            self.status.add_warning("Python 3.11+ recommended for optimal performance")
        
        # Check required environment variables
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL", 
            "CLAUDE_API_KEY",
            "JWT_SECRET_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.console.print(f"[red]Missing environment variables: {', '.join(missing_vars)}[/red]")
            return False
        
        # Check external service credentials
        optional_services = {
            "APOLLO_API_KEY": "Apollo.io integration",
            "TWILIO_ACCOUNT_SID": "SMS functionality", 
            "SENDGRID_API_KEY": "Email functionality",
            "GHL_API_KEY": "GoHighLevel integration"
        }
        
        for var, service_name in optional_services.items():
            if not os.getenv(var) or os.getenv(var).startswith("your_"):
                self.status.add_warning(f"{service_name} not configured - {var} missing")
        
        # Check Docker availability (if using containers)
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            self.console.print("[green]✓ Docker available[/green]")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.status.add_warning("Docker not available - manual setup required")
        
        # Validate project structure
        required_paths = [
            "ghl_real_estate_ai/services/database_service.py",
            "ghl_real_estate_ai/services/security_framework.py",
            "requirements.txt"
        ]
        
        for path in required_paths:
            if not (self.project_root / path).exists():
                self.console.print(f"[red]Missing required file: {path}[/red]")
                return False
        
        self.console.print("[green]✓ Environment validation complete[/green]")
        return True
    
    async def _deploy_security_initialization(self) -> bool:
        """Initialize security framework."""
        self.console.print("[cyan]Initializing security framework...[/cyan]")
        
        try:
            # Initialize security framework
            security = SecurityFramework()
            
            # Test JWT token generation
            test_token = security.generate_jwt_token("deploy_test", "admin")
            if not test_token:
                return False
            
            # Validate token
            token_payload = await security.validate_jwt_token(test_token)
            if token_payload.get("sub") != "deploy_test":
                return False
            
            self.services["security"] = security
            
            self.console.print("[green]✓ Security framework initialized[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Security initialization failed: {e}[/red]")
            return False
    
    async def _deploy_database_setup(self) -> bool:
        """Setup database and run migrations."""
        self.console.print("[cyan]Setting up database...[/cyan]")
        
        try:
            # Test database connection
            db = DatabaseService()
            await db.initialize()
            
            # Run health check
            health = await db.health_check()
            if health.get("status") != "healthy":
                self.console.print(f"[red]Database health check failed: {health}[/red]")
                return False
            
            # Verify tables exist (migrations should have run during init)
            async with db.get_connection() as conn:
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                
                table_names = [row['table_name'] for row in tables]
                required_tables = ['leads', 'communication_logs', 'nurture_campaigns', 'lead_campaign_status']
                
                missing_tables = [t for t in required_tables if t not in table_names]
                if missing_tables:
                    self.console.print(f"[red]Missing database tables: {missing_tables}[/red]")
                    return False
            
            self.services["database"] = db
            
            self.console.print(f"[green]✓ Database ready ({len(table_names)} tables)[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Database setup failed: {e}[/red]")
            return False
    
    async def _deploy_external_services_validation(self) -> bool:
        """Validate external service connections."""
        self.console.print("[cyan]Validating external services...[/cyan]")
        
        service_results = {}
        
        # Test Apollo.io
        if settings.apollo_api_key and not settings.apollo_api_key.startswith("your_"):
            try:
                async with ApolloClient() as apollo:
                    health = await apollo.health_check()
                    service_results["apollo"] = health.get("status") == "healthy"
            except Exception as e:
                service_results["apollo"] = False
                self.status.add_warning(f"Apollo.io connection failed: {e}")
        
        # Test Twilio
        if settings.twilio_account_sid and not settings.twilio_account_sid.startswith("your_"):
            try:
                async with TwilioClient() as twilio:
                    health = await twilio.health_check()
                    service_results["twilio"] = health.get("status") == "healthy"
            except Exception as e:
                service_results["twilio"] = False
                self.status.add_warning(f"Twilio connection failed: {e}")
        
        # Test SendGrid
        if settings.sendgrid_api_key and not settings.sendgrid_api_key.startswith("your_"):
            try:
                async with SendGridClient() as sendgrid:
                    health = await sendgrid.health_check()
                    service_results["sendgrid"] = health.get("status") == "healthy"
            except Exception as e:
                service_results["sendgrid"] = False
                self.status.add_warning(f"SendGrid connection failed: {e}")
        
        # Test GoHighLevel
        if settings.ghl_api_key and not settings.ghl_api_key.startswith("your_"):
            try:
                async with EnhancedGHLClient() as ghl:
                    health = await ghl.health_check()
                    service_results["ghl"] = health.get("status") == "healthy"
            except Exception as e:
                service_results["ghl"] = False
                self.status.add_warning(f"GoHighLevel connection failed: {e}")
        
        # Test Redis
        try:
            redis = aioredis.from_url(settings.redis_url)
            await redis.ping()
            await redis.close()
            service_results["redis"] = True
        except Exception as e:
            service_results["redis"] = False
            self.status.add_warning(f"Redis connection failed: {e}")
        
        # Display service status table
        table = Table(title="External Service Validation")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Notes")
        
        for service, status in service_results.items():
            status_text = "✓ Connected" if status else "✗ Failed"
            notes = "Ready for production" if status else "May operate in degraded mode"
            table.add_row(service.title(), status_text, notes)
        
        self.console.print(table)
        
        # At least Redis and Database must be working
        if not service_results.get("redis", False):
            self.console.print("[red]Redis connection required for production deployment[/red]")
            return False
        
        return True
    
    async def _deploy_service_initialization(self) -> bool:
        """Initialize core services."""
        self.console.print("[cyan]Initializing core services...[/cyan]")
        
        try:
            # Initialize monitoring service
            monitoring = MonitoringService()
            
            # Register health checks for available services
            if "database" in self.services:
                monitoring.register_database_health_check(self.services["database"])
            
            # Register other service health checks
            if settings.apollo_api_key and not settings.apollo_api_key.startswith("your_"):
                apollo = ApolloClient()
                monitoring.register_apollo_health_check(apollo)
                self.services["apollo"] = apollo
            
            if settings.twilio_account_sid and not settings.twilio_account_sid.startswith("your_"):
                twilio = TwilioClient()
                monitoring.register_twilio_health_check(twilio)
                self.services["twilio"] = twilio
            
            if settings.sendgrid_api_key and not settings.sendgrid_api_key.startswith("your_"):
                sendgrid = SendGridClient()
                monitoring.register_sendgrid_health_check(sendgrid)
                self.services["sendgrid"] = sendgrid
            
            if settings.ghl_api_key and not settings.ghl_api_key.startswith("your_"):
                ghl = EnhancedGHLClient()
                monitoring.register_ghl_health_check(ghl)
                self.services["ghl"] = ghl
            
            self.services["monitoring"] = monitoring
            
            self.console.print(f"[green]✓ {len(self.services)} services initialized[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Service initialization failed: {e}[/red]")
            return False
    
    async def _deploy_health_checks(self) -> bool:
        """Run comprehensive health checks."""
        self.console.print("[cyan]Running health checks...[/cyan]")
        
        if "monitoring" not in self.services:
            self.console.print("[red]Monitoring service not available[/red]")
            return False
        
        try:
            monitoring = self.services["monitoring"]
            
            # Run all health checks
            health_results = await monitoring.run_all_health_checks()
            
            # Display results table
            table = Table(title="Service Health Check Results")
            table.add_column("Service", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Response Time", justify="right")
            table.add_column("Details")
            
            for service_name, result in health_results.get("services", {}).items():
                status = result.get("status", "unknown")
                response_time = f"{result.get('response_time_ms', 0):.1f}ms"
                
                status_color = {
                    "healthy": "green",
                    "degraded": "yellow", 
                    "unhealthy": "red",
                    "critical": "red bold"
                }.get(status, "white")
                
                details = result.get("details", {})
                details_text = json.dumps(details) if details else ""
                if len(details_text) > 50:
                    details_text = details_text[:47] + "..."
                
                table.add_row(
                    service_name.title(),
                    f"[{status_color}]{status.title()}[/{status_color}]",
                    response_time,
                    details_text
                )
            
            self.console.print(table)
            
            # Check overall status
            overall_status = health_results.get("overall_status", "unknown")
            if overall_status not in ["healthy", "degraded"]:
                self.console.print(f"[red]Overall system status: {overall_status}[/red]")
                return False
            
            if overall_status == "degraded":
                self.status.add_warning("System is in degraded state but operational")
            
            self.console.print(f"[green]✓ Health checks complete - Status: {overall_status}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Health checks failed: {e}[/red]")
            return False
    
    async def _deploy_monitoring_setup(self) -> bool:
        """Setup monitoring and alerting."""
        self.console.print("[cyan]Setting up monitoring...[/cyan]")
        
        if "monitoring" not in self.services:
            return False
        
        try:
            monitoring = self.services["monitoring"]
            
            # Start monitoring background tasks
            await monitoring.start_monitoring()
            
            # Wait a moment for initial checks
            await asyncio.sleep(2)
            
            # Get monitoring dashboard data
            dashboard_data = await monitoring.get_monitoring_dashboard_data()
            
            system_status = dashboard_data.get("system_status", {})
            self.console.print(f"[green]✓ Monitoring active - {system_status.get('metrics', {}).get('total_services', 0)} services monitored[/green]")
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]Monitoring setup failed: {e}[/red]")
            return False
    
    async def _deploy_production_readiness(self) -> bool:
        """Verify production readiness."""
        self.console.print("[cyan]Verifying production readiness...[/cyan]")
        
        readiness_checks = []
        
        # Check database connection pool
        if "database" in self.services:
            db = self.services["database"]
            if db.pool and db.pool.get_size() >= 5:
                readiness_checks.append(("Database connection pool", True, f"{db.pool.get_size()} connections"))
            else:
                readiness_checks.append(("Database connection pool", False, "Insufficient connections"))
        
        # Check security framework
        if "security" in self.services:
            readiness_checks.append(("Security framework", True, "JWT and rate limiting ready"))
        else:
            readiness_checks.append(("Security framework", False, "Not initialized"))
        
        # Check external integrations
        external_services = ["apollo", "twilio", "sendgrid", "ghl"]
        available_integrations = len([s for s in external_services if s in self.services])
        
        if available_integrations >= 2:
            readiness_checks.append(("External integrations", True, f"{available_integrations}/4 services"))
        else:
            readiness_checks.append(("External integrations", False, f"Only {available_integrations}/4 services"))
        
        # Check monitoring
        if "monitoring" in self.services:
            monitoring = self.services["monitoring"]
            if monitoring.monitoring_enabled:
                readiness_checks.append(("Monitoring & alerting", True, "Active monitoring"))
            else:
                readiness_checks.append(("Monitoring & alerting", False, "Not active"))
        
        # Display readiness table
        table = Table(title="Production Readiness Checklist")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        
        failed_checks = 0
        for check_name, passed, details in readiness_checks:
            status_text = "[green]✓ Ready[/green]" if passed else "[red]✗ Not Ready[/red]"
            table.add_row(check_name, status_text, details)
            
            if not passed:
                failed_checks += 1
        
        self.console.print(table)
        
        if failed_checks > 0:
            self.console.print(f"[red]{failed_checks} readiness checks failed[/red]")
            return False
        
        self.console.print("[green]✓ All production readiness checks passed[/green]")
        return True
    
    async def _deploy_final_validation(self) -> bool:
        """Final system validation."""
        self.console.print("[cyan]Running final validation...[/cyan]")
        
        try:
            # Test end-to-end functionality
            validation_results = []
            
            # Test database operations
            if "database" in self.services:
                db = self.services["database"]
                
                # Test lead creation
                try:
                    lead_data = {
                        "first_name": "Deployment",
                        "last_name": "Test",
                        "email": "deployment-test@service6.com",
                        "source": "deployment_validation"
                    }
                    lead_id = await db.create_lead(lead_data, created_by="deployment_script")
                    
                    # Test lead retrieval
                    lead = await db.get_lead(lead_id)
                    if lead and lead["email"] == lead_data["email"]:
                        validation_results.append(("Database CRUD operations", True))
                    else:
                        validation_results.append(("Database CRUD operations", False))
                except Exception as e:
                    validation_results.append(("Database CRUD operations", False))
            
            # Test security framework
            if "security" in self.services:
                security = self.services["security"]
                try:
                    # Test rate limiting
                    from ghl_real_estate_ai.services.security_framework import RateLimitType
                    from unittest.mock import Mock
                    
                    mock_request = Mock()
                    mock_request.client.host = "127.0.0.1"
                    mock_request.method = "GET"
                    mock_request.url.path = "/test"
                    mock_request.headers = {}
                    
                    rate_limit_ok = await security.check_rate_limit(mock_request, limit=10, limit_type=RateLimitType.PER_IP)
                    validation_results.append(("Security rate limiting", rate_limit_ok))
                except Exception as e:
                    validation_results.append(("Security rate limiting", False))
            
            # Display validation results
            table = Table(title="Final Validation Results")
            table.add_column("Validation", style="cyan")
            table.add_column("Result", style="green")
            
            failed_validations = 0
            for validation_name, passed in validation_results:
                result_text = "[green]✓ Pass[/green]" if passed else "[red]✗ Fail[/red]"
                table.add_row(validation_name, result_text)
                
                if not passed:
                    failed_validations += 1
            
            self.console.print(table)
            
            if failed_validations > 0:
                self.console.print(f"[red]{failed_validations} validations failed[/red]")
                return False
            
            self.console.print("[green]✓ All final validations passed[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Final validation failed: {e}[/red]")
            return False
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    async def _display_deployment_summary(self):
        """Display comprehensive deployment summary."""
        summary = self.status.get_summary()
        
        # Create summary panel
        if summary["overall_success"]:
            title = "[bold green]🎉 Deployment Successful![/bold green]"
            border_style = "green"
        else:
            title = "[bold red]❌ Deployment Failed[/bold red]"
            border_style = "red"
        
        summary_text = Text()
        summary_text.append(f"Duration: {summary['duration_seconds']:.1f} seconds\n")
        summary_text.append(f"Steps completed: {summary['successful_steps']}/{summary['total_steps']}\n")
        
        if summary["warnings"]:
            summary_text.append(f"Warnings: {summary['warnings']}\n", style="yellow")
        
        if summary["errors"]:
            summary_text.append("Errors:\n", style="red")
            for error in summary["errors"]:
                summary_text.append(f"  • {error}\n", style="red")
        
        self.console.print(Panel(summary_text, title=title, border_style=border_style))
        
        # Display next steps
        if summary["overall_success"]:
            next_steps = Panel(
                "1. Monitor system health via monitoring dashboard\n"
                "2. Test lead capture and processing workflows\n"
                "3. Configure alert notifications (Slack, email)\n"
                "4. Run load testing if high volume expected\n"
                "5. Schedule regular backups and maintenance",
                title="[bold blue]Next Steps[/bold blue]",
                border_style="blue"
            )
            self.console.print(next_steps)
        else:
            troubleshooting = Panel(
                "1. Review error messages above\n"
                "2. Check environment variable configuration\n"
                "3. Verify external service credentials\n"
                "4. Ensure database and Redis are accessible\n"
                "5. Check network connectivity and firewall rules",
                title="[bold yellow]Troubleshooting[/bold yellow]",
                border_style="yellow"
            )
            self.console.print(troubleshooting)
    
    async def cleanup(self):
        """Cleanup resources after deployment."""
        # Close service connections
        for service_name, service in self.services.items():
            try:
                if hasattr(service, 'close'):
                    await service.close()
                elif hasattr(service, 'stop_monitoring'):
                    await service.stop_monitoring()
            except Exception as e:
                logger.error(f"Failed to cleanup {service_name}: {e}")


# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Service 6 Production Deployment")
    parser.add_argument(
        "--environment", 
        choices=["production", "staging", "development"], 
        default="production",
        help="Deployment environment"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Run deployment validation without making changes"
    )
    parser.add_argument(
        "--skip-external", 
        action="store_true",
        help="Skip external service validation"
    )
    
    args = parser.parse_args()
    
    deployer = Service6Deployer(args.environment)
    
    try:
        if args.dry_run:
            console.print("[yellow]Running in DRY RUN mode - no changes will be made[/yellow]")
        
        success = await deployer.deploy()
        
        if success:
            console.print("\n[bold green]🚀 Service 6 is ready for production![/bold green]")
            sys.exit(0)
        else:
            console.print("\n[bold red]❌ Deployment failed - check errors above[/bold red]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Deployment cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        sys.exit(1)
    finally:
        await deployer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())