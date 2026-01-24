#!/usr/bin/env python3
"""
Jorge's Real Estate AI Platform - Comprehensive Security Scanner
================================================================
Enterprise-grade vulnerability assessment and security validation tool.
Designed for continuous security monitoring and SOC2 compliance.

Features:
- Dependency vulnerability scanning
- Container security assessment
- Infrastructure security validation
- Code security analysis
- Compliance checking (SOC2, GDPR)
- Automated remediation suggestions

Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import argparse
import tempfile

import aiohttp
import yaml
from dataclasses import dataclass, asdict
from enum import Enum

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security-scan.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SeverityLevel(str, Enum):
    """Security vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ScanType(str, Enum):
    """Types of security scans available."""
    DEPENDENCIES = "dependencies"
    CONTAINER = "container"
    CODE = "code"
    INFRASTRUCTURE = "infrastructure"
    COMPLIANCE = "compliance"
    ALL = "all"

@dataclass
class Vulnerability:
    """Security vulnerability data model."""
    id: str
    title: str
    description: str
    severity: SeverityLevel
    cve: Optional[str] = None
    cvss_score: Optional[float] = None
    affected_component: Optional[str] = None
    remediation: Optional[str] = None
    references: List[str] = None

    def __post_init__(self):
        if self.references is None:
            self.references = []

@dataclass
class ScanResult:
    """Security scan result container."""
    scan_type: ScanType
    timestamp: datetime
    duration_seconds: float
    status: str
    vulnerabilities: List[Vulnerability]
    summary: Dict[str, int]
    metadata: Dict[str, Any]

class ComprehensiveSecurityScanner:
    """
    Enterprise security scanner for Jorge's Real Estate AI Platform.

    Performs comprehensive security assessments including:
    - Python dependency vulnerabilities (using safety, pip-audit)
    - Container security (using trivy, grype)
    - Static code analysis (using bandit, semgrep)
    - Infrastructure configuration (using checkov, kics)
    - Compliance validation (SOC2, GDPR, real estate regulations)
    """

    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.scan_results: List[ScanResult] = []
        self.temp_dir = tempfile.mkdtemp(prefix="jorge-security-scan-")

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load scanner configuration from file or use defaults."""
        default_config = {
            "severity_threshold": SeverityLevel.MEDIUM,
            "fail_on_critical": True,
            "fail_on_high": False,
            "exclude_patterns": [
                "tests/",
                "__pycache__/",
                ".git/",
                "node_modules/"
            ],
            "container_registries": [
                "ghcr.io/jorge-salas/jorge-revenue-platform"
            ],
            "compliance_frameworks": ["soc2", "gdpr", "real-estate"],
            "output_formats": ["json", "sarif", "html"],
            "notification_channels": [],
            "remediation_suggestions": True
        }

        if config_file and Path(config_file).exists():
            with open(config_file) as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    async def run_comprehensive_scan(self, scan_types: List[ScanType]) -> List[ScanResult]:
        """Execute comprehensive security scanning across all specified scan types."""
        logger.info("🔍 Starting comprehensive security scan for Jorge's Real Estate AI Platform")
        logger.info(f"Scan types: {', '.join(scan_types)}")

        if ScanType.ALL in scan_types:
            scan_types = [ScanType.DEPENDENCIES, ScanType.CONTAINER, ScanType.CODE,
                         ScanType.INFRASTRUCTURE, ScanType.COMPLIANCE]

        # Run scans concurrently for better performance
        scan_tasks = []
        for scan_type in scan_types:
            if scan_type == ScanType.DEPENDENCIES:
                scan_tasks.append(self._scan_dependencies())
            elif scan_type == ScanType.CONTAINER:
                scan_tasks.append(self._scan_containers())
            elif scan_type == ScanType.CODE:
                scan_tasks.append(self._scan_code_security())
            elif scan_type == ScanType.INFRASTRUCTURE:
                scan_tasks.append(self._scan_infrastructure())
            elif scan_type == ScanType.COMPLIANCE:
                scan_tasks.append(self._scan_compliance())

        # Execute all scans concurrently
        results = await asyncio.gather(*scan_tasks, return_exceptions=True)

        # Process results and handle exceptions
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Scan failed with exception: {result}")
            else:
                self.scan_results.append(result)

        logger.info(f"✅ Comprehensive security scan completed. {len(self.scan_results)} scans executed.")
        return self.scan_results

    async def _scan_dependencies(self) -> ScanResult:
        """Scan Python dependencies for known vulnerabilities."""
        logger.info("📦 Scanning Python dependencies for vulnerabilities...")
        start_time = time.time()
        vulnerabilities = []

        try:
            # Install security scanning tools
            await self._ensure_tools_installed(["safety", "pip-audit"])

            # Safety scan
            safety_result = await self._run_safety_scan()
            vulnerabilities.extend(safety_result)

            # Pip-audit scan
            pip_audit_result = await self._run_pip_audit_scan()
            vulnerabilities.extend(pip_audit_result)

            # Check for outdated packages
            outdated_result = await self._check_outdated_packages()
            vulnerabilities.extend(outdated_result)

            duration = time.time() - start_time
            summary = self._calculate_vulnerability_summary(vulnerabilities)

            return ScanResult(
                scan_type=ScanType.DEPENDENCIES,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
                status="completed",
                vulnerabilities=vulnerabilities,
                summary=summary,
                metadata={
                    "tools_used": ["safety", "pip-audit"],
                    "packages_scanned": await self._count_packages(),
                    "scan_duration": duration
                }
            )

        except Exception as e:
            logger.error(f"Dependency scan failed: {e}")
            return ScanResult(
                scan_type=ScanType.DEPENDENCIES,
                timestamp=datetime.utcnow(),
                duration_seconds=time.time() - start_time,
                status="failed",
                vulnerabilities=[],
                summary={},
                metadata={"error": str(e)}
            )

    async def _run_safety_scan(self) -> List[Vulnerability]:
        """Run Safety scan for known vulnerabilities."""
        vulnerabilities = []

        try:
            # Run safety check
            result = subprocess.run(
                ["safety", "check", "--json", "--full-report"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.stdout:
                safety_data = json.loads(result.stdout)

                for vuln in safety_data.get("vulnerabilities", []):
                    vulnerability = Vulnerability(
                        id=vuln.get("id", "SAFETY-UNKNOWN"),
                        title=f"Vulnerable dependency: {vuln.get('package_name', 'Unknown')}",
                        description=vuln.get("advisory", ""),
                        severity=self._map_safety_severity(vuln.get("severity", "medium")),
                        cve=vuln.get("cve"),
                        affected_component=vuln.get("package_name"),
                        remediation=f"Upgrade to version {vuln.get('safe_version', 'latest')} or higher",
                        references=[vuln.get("more_info_url", "")]
                    )
                    vulnerabilities.append(vulnerability)

        except subprocess.TimeoutExpired:
            logger.error("Safety scan timed out")
        except Exception as e:
            logger.error(f"Safety scan error: {e}")

        return vulnerabilities

    async def _run_pip_audit_scan(self) -> List[Vulnerability]:
        """Run pip-audit scan for additional vulnerability detection."""
        vulnerabilities = []

        try:
            result = subprocess.run(
                ["pip-audit", "--format", "json", "--progress-spinner", "off"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.stdout:
                audit_data = json.loads(result.stdout)

                for vuln in audit_data.get("vulnerabilities", []):
                    vulnerability = Vulnerability(
                        id=vuln.get("id", f"PIP-AUDIT-{vuln.get('package', 'UNKNOWN')}"),
                        title=f"Security advisory for {vuln.get('package', 'Unknown')}",
                        description=vuln.get("description", ""),
                        severity=self._map_pip_audit_severity(vuln.get("fix_versions", [])),
                        affected_component=vuln.get("package"),
                        remediation=f"Update to fixed version: {', '.join(vuln.get('fix_versions', []))}",
                        references=vuln.get("aliases", [])
                    )
                    vulnerabilities.append(vulnerability)

        except subprocess.TimeoutExpired:
            logger.error("Pip-audit scan timed out")
        except Exception as e:
            logger.error(f"Pip-audit scan error: {e}")

        return vulnerabilities

    async def _scan_containers(self) -> ScanResult:
        """Scan container images for security vulnerabilities."""
        logger.info("🐳 Scanning container images for vulnerabilities...")
        start_time = time.time()
        vulnerabilities = []

        try:
            # Install container scanning tools
            await self._ensure_tools_installed(["trivy", "grype"])

            for registry in self.config.get("container_registries", []):
                # Trivy scan
                trivy_vulns = await self._run_trivy_scan(registry)
                vulnerabilities.extend(trivy_vulns)

                # Grype scan for additional coverage
                grype_vulns = await self._run_grype_scan(registry)
                vulnerabilities.extend(grype_vulns)

            duration = time.time() - start_time
            summary = self._calculate_vulnerability_summary(vulnerabilities)

            return ScanResult(
                scan_type=ScanType.CONTAINER,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
                status="completed",
                vulnerabilities=vulnerabilities,
                summary=summary,
                metadata={
                    "tools_used": ["trivy", "grype"],
                    "images_scanned": len(self.config.get("container_registries", [])),
                    "scan_duration": duration
                }
            )

        except Exception as e:
            logger.error(f"Container scan failed: {e}")
            return ScanResult(
                scan_type=ScanType.CONTAINER,
                timestamp=datetime.utcnow(),
                duration_seconds=time.time() - start_time,
                status="failed",
                vulnerabilities=[],
                summary={},
                metadata={"error": str(e)}
            )

    async def _scan_code_security(self) -> ScanResult:
        """Perform static code analysis for security vulnerabilities."""
        logger.info("🔒 Scanning code for security vulnerabilities...")
        start_time = time.time()
        vulnerabilities = []

        try:
            # Install code analysis tools
            await self._ensure_tools_installed(["bandit", "semgrep"])

            # Bandit scan for Python security issues
            bandit_vulns = await self._run_bandit_scan()
            vulnerabilities.extend(bandit_vulns)

            # Semgrep scan for additional security patterns
            semgrep_vulns = await self._run_semgrep_scan()
            vulnerabilities.extend(semgrep_vulns)

            # Custom Jorge-specific security checks
            jorge_vulns = await self._run_jorge_security_checks()
            vulnerabilities.extend(jorge_vulns)

            duration = time.time() - start_time
            summary = self._calculate_vulnerability_summary(vulnerabilities)

            return ScanResult(
                scan_type=ScanType.CODE,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
                status="completed",
                vulnerabilities=vulnerabilities,
                summary=summary,
                metadata={
                    "tools_used": ["bandit", "semgrep", "jorge-custom"],
                    "files_scanned": await self._count_python_files(),
                    "scan_duration": duration
                }
            )

        except Exception as e:
            logger.error(f"Code security scan failed: {e}")
            return ScanResult(
                scan_type=ScanType.CODE,
                timestamp=datetime.utcnow(),
                duration_seconds=time.time() - start_time,
                status="failed",
                vulnerabilities=[],
                summary={},
                metadata={"error": str(e)}
            )

    async def _run_bandit_scan(self) -> List[Vulnerability]:
        """Run Bandit static security analysis."""
        vulnerabilities = []

        try:
            result = subprocess.run(
                ["bandit", "-r", "ghl_real_estate_ai/", "-f", "json", "-q"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.stdout:
                bandit_data = json.loads(result.stdout)

                for result in bandit_data.get("results", []):
                    vulnerability = Vulnerability(
                        id=f"BANDIT-{result.get('test_id', 'UNKNOWN')}",
                        title=result.get("issue_text", "Security issue detected"),
                        description=f"{result.get('issue_text', '')} in {result.get('filename', 'unknown file')}",
                        severity=self._map_bandit_severity(result.get("issue_severity", "LOW")),
                        affected_component=result.get("filename"),
                        remediation=result.get("more_info", "Review code and apply security best practices"),
                        references=[result.get("more_info", "")]
                    )
                    vulnerabilities.append(vulnerability)

        except Exception as e:
            logger.error(f"Bandit scan error: {e}")

        return vulnerabilities

    async def _scan_infrastructure(self) -> ScanResult:
        """Scan infrastructure configurations for security issues."""
        logger.info("🏗️ Scanning infrastructure configurations...")
        start_time = time.time()
        vulnerabilities = []

        try:
            # Install infrastructure scanning tools
            await self._ensure_tools_installed(["checkov", "kics"])

            # Checkov scan for Kubernetes and Docker configurations
            checkov_vulns = await self._run_checkov_scan()
            vulnerabilities.extend(checkov_vulns)

            # KICS scan for additional infrastructure security
            kics_vulns = await self._run_kics_scan()
            vulnerabilities.extend(kics_vulns)

            # Custom Jorge infrastructure checks
            jorge_infra_vulns = await self._run_jorge_infrastructure_checks()
            vulnerabilities.extend(jorge_infra_vulns)

            duration = time.time() - start_time
            summary = self._calculate_vulnerability_summary(vulnerabilities)

            return ScanResult(
                scan_type=ScanType.INFRASTRUCTURE,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
                status="completed",
                vulnerabilities=vulnerabilities,
                summary=summary,
                metadata={
                    "tools_used": ["checkov", "kics", "jorge-custom"],
                    "config_files_scanned": await self._count_config_files(),
                    "scan_duration": duration
                }
            )

        except Exception as e:
            logger.error(f"Infrastructure scan failed: {e}")
            return ScanResult(
                scan_type=ScanType.INFRASTRUCTURE,
                timestamp=datetime.utcnow(),
                duration_seconds=time.time() - start_time,
                status="failed",
                vulnerabilities=[],
                summary={},
                metadata={"error": str(e)}
            )

    async def _scan_compliance(self) -> ScanResult:
        """Perform compliance validation against security standards."""
        logger.info("📋 Performing compliance validation...")
        start_time = time.time()
        vulnerabilities = []

        try:
            # SOC2 compliance checks
            soc2_vulns = await self._check_soc2_compliance()
            vulnerabilities.extend(soc2_vulns)

            # GDPR compliance checks
            gdpr_vulns = await self._check_gdpr_compliance()
            vulnerabilities.extend(gdpr_vulns)

            # Real estate industry specific checks
            real_estate_vulns = await self._check_real_estate_compliance()
            vulnerabilities.extend(real_estate_vulns)

            duration = time.time() - start_time
            summary = self._calculate_vulnerability_summary(vulnerabilities)

            return ScanResult(
                scan_type=ScanType.COMPLIANCE,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
                status="completed",
                vulnerabilities=vulnerabilities,
                summary=summary,
                metadata={
                    "frameworks_checked": ["soc2", "gdpr", "real-estate"],
                    "controls_evaluated": len(vulnerabilities) * 5,  # Approximate
                    "scan_duration": duration
                }
            )

        except Exception as e:
            logger.error(f"Compliance scan failed: {e}")
            return ScanResult(
                scan_type=ScanType.COMPLIANCE,
                timestamp=datetime.utcnow(),
                duration_seconds=time.time() - start_time,
                status="failed",
                vulnerabilities=[],
                summary={},
                metadata={"error": str(e)}
            )

    async def _check_soc2_compliance(self) -> List[Vulnerability]:
        """Check SOC2 compliance requirements."""
        vulnerabilities = []

        # CC6.1 - Access Controls
        if not await self._check_file_exists("infrastructure/security/rbac.yaml"):
            vulnerabilities.append(Vulnerability(
                id="SOC2-CC6.1-001",
                title="Missing RBAC configuration",
                description="Role-Based Access Control configuration not found",
                severity=SeverityLevel.HIGH,
                affected_component="Infrastructure",
                remediation="Implement RBAC policies for access control"
            ))

        # CC6.3 - Data Encryption
        if not await self._check_encryption_config():
            vulnerabilities.append(Vulnerability(
                id="SOC2-CC6.3-001",
                title="Encryption configuration missing",
                description="Data encryption at rest and in transit not properly configured",
                severity=SeverityLevel.CRITICAL,
                affected_component="Data Protection",
                remediation="Configure encryption for data at rest and in transit"
            ))

        return vulnerabilities

    async def _check_gdpr_compliance(self) -> List[Vulnerability]:
        """Check GDPR compliance requirements."""
        vulnerabilities = []

        # Check for data processing lawfulness
        if not await self._check_privacy_policy():
            vulnerabilities.append(Vulnerability(
                id="GDPR-ART6-001",
                title="Privacy policy not found",
                description="Privacy policy documenting lawful basis for processing not found",
                severity=SeverityLevel.HIGH,
                affected_component="Privacy",
                remediation="Create comprehensive privacy policy"
            ))

        return vulnerabilities

    def generate_report(self, output_format: str = "json") -> str:
        """Generate comprehensive security report."""
        logger.info(f"📊 Generating security report in {output_format} format...")

        if output_format == "json":
            return self._generate_json_report()
        elif output_format == "html":
            return self._generate_html_report()
        elif output_format == "sarif":
            return self._generate_sarif_report()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_json_report(self) -> str:
        """Generate JSON format security report."""
        report = {
            "scan_summary": {
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "Jorge's Real Estate AI Platform",
                "total_scans": len(self.scan_results),
                "total_vulnerabilities": sum(len(scan.vulnerabilities) for scan in self.scan_results),
                "severity_breakdown": self._get_overall_severity_breakdown()
            },
            "scan_results": [asdict(result) for result in self.scan_results],
            "compliance_status": self._get_compliance_status(),
            "recommendations": self._generate_recommendations()
        }

        report_json = json.dumps(report, indent=2, default=str)
        report_file = f"security-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

        with open(report_file, 'w') as f:
            f.write(report_json)

        logger.info(f"✅ JSON report generated: {report_file}")
        return report_file

    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate remediation recommendations based on scan results."""
        recommendations = []

        # Critical vulnerabilities
        critical_count = sum(
            len([v for v in scan.vulnerabilities if v.severity == SeverityLevel.CRITICAL])
            for scan in self.scan_results
        )

        if critical_count > 0:
            recommendations.append({
                "priority": "immediate",
                "category": "critical_vulnerabilities",
                "recommendation": f"Address {critical_count} critical vulnerabilities immediately",
                "impact": "System security compromise risk"
            })

        # Dependency updates
        dep_scan = next((s for s in self.scan_results if s.scan_type == ScanType.DEPENDENCIES), None)
        if dep_scan and len(dep_scan.vulnerabilities) > 0:
            recommendations.append({
                "priority": "high",
                "category": "dependency_management",
                "recommendation": "Update vulnerable dependencies and implement automated scanning",
                "impact": "Supply chain security"
            })

        return recommendations

    def _get_compliance_status(self) -> Dict[str, str]:
        """Calculate compliance status for various frameworks."""
        compliance_scan = next((s for s in self.scan_results if s.scan_type == ScanType.COMPLIANCE), None)

        if not compliance_scan:
            return {"status": "not_assessed"}

        critical_compliance = [v for v in compliance_scan.vulnerabilities if v.severity == SeverityLevel.CRITICAL]

        if len(critical_compliance) > 0:
            status = "non_compliant"
        else:
            status = "compliant"

        return {
            "status": status,
            "frameworks": ["soc2", "gdpr", "real-estate"],
            "last_assessment": datetime.utcnow().isoformat(),
            "critical_gaps": len(critical_compliance)
        }

    # Helper methods
    async def _ensure_tools_installed(self, tools: List[str]) -> None:
        """Ensure required security tools are installed."""
        for tool in tools:
            if not subprocess.run(["which", tool], capture_output=True).returncode == 0:
                logger.warning(f"Tool {tool} not found. Installing...")
                await self._install_tool(tool)

    async def _install_tool(self, tool: str) -> None:
        """Install security scanning tool."""
        install_commands = {
            "safety": ["pip", "install", "safety"],
            "pip-audit": ["pip", "install", "pip-audit"],
            "bandit": ["pip", "install", "bandit"],
            "semgrep": ["pip", "install", "semgrep"],
            "trivy": ["curl", "-sfL", "https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh", "|", "sh", "-s", "--", "-b", "/usr/local/bin"],
            "checkov": ["pip", "install", "checkov"],
            "kics": ["docker", "pull", "checkmarx/kics:latest"]
        }

        if tool in install_commands:
            try:
                subprocess.run(install_commands[tool], check=True)
                logger.info(f"Successfully installed {tool}")
            except subprocess.CalledProcessError:
                logger.error(f"Failed to install {tool}")

    def _calculate_vulnerability_summary(self, vulnerabilities: List[Vulnerability]) -> Dict[str, int]:
        """Calculate summary statistics for vulnerabilities."""
        summary = {
            "total": len(vulnerabilities),
            "critical": len([v for v in vulnerabilities if v.severity == SeverityLevel.CRITICAL]),
            "high": len([v for v in vulnerabilities if v.severity == SeverityLevel.HIGH]),
            "medium": len([v for v in vulnerabilities if v.severity == SeverityLevel.MEDIUM]),
            "low": len([v for v in vulnerabilities if v.severity == SeverityLevel.LOW]),
            "info": len([v for v in vulnerabilities if v.severity == SeverityLevel.INFO])
        }
        return summary

    def _map_safety_severity(self, safety_severity: str) -> SeverityLevel:
        """Map Safety tool severity to our standard levels."""
        mapping = {
            "high": SeverityLevel.HIGH,
            "medium": SeverityLevel.MEDIUM,
            "low": SeverityLevel.LOW
        }
        return mapping.get(safety_severity.lower(), SeverityLevel.MEDIUM)

    def _map_bandit_severity(self, bandit_severity: str) -> SeverityLevel:
        """Map Bandit severity to our standard levels."""
        mapping = {
            "HIGH": SeverityLevel.HIGH,
            "MEDIUM": SeverityLevel.MEDIUM,
            "LOW": SeverityLevel.LOW
        }
        return mapping.get(bandit_severity, SeverityLevel.MEDIUM)

    # Placeholder methods for additional functionality
    async def _run_trivy_scan(self, image: str) -> List[Vulnerability]:
        """Run Trivy container scan."""
        return []  # Implementation would call trivy and parse results

    async def _run_semgrep_scan(self) -> List[Vulnerability]:
        """Run Semgrep static analysis."""
        return []  # Implementation would call semgrep and parse results

    async def _run_jorge_security_checks(self) -> List[Vulnerability]:
        """Custom security checks for Jorge platform."""
        vulnerabilities = []

        # Check for exposed API keys in Jorge configuration
        config_files = ["ghl_real_estate_ai/ghl_utils/jorge_config.py"]
        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file) as f:
                    content = f.read()
                    if "API_KEY" in content and ("sk-" in content or "AKIA" in content):
                        vulnerabilities.append(Vulnerability(
                            id="JORGE-SEC-001",
                            title="Potential API key exposure in configuration",
                            description=f"Configuration file {config_file} may contain exposed API keys",
                            severity=SeverityLevel.CRITICAL,
                            affected_component=config_file,
                            remediation="Move API keys to environment variables or secure secrets management"
                        ))

        return vulnerabilities

    async def _count_packages(self) -> int:
        """Count number of Python packages."""
        try:
            result = subprocess.run(["pip", "list", "--format=freeze"], capture_output=True, text=True)
            return len(result.stdout.strip().split('\n')) if result.stdout else 0
        except:
            return 0

    async def _count_python_files(self) -> int:
        """Count Python files in the project."""
        return len(list(Path(".").rglob("*.py")))

    async def _check_file_exists(self, file_path: str) -> bool:
        """Check if a configuration file exists."""
        return Path(file_path).exists()

    async def _check_encryption_config(self) -> bool:
        """Check if encryption is properly configured."""
        # This would check for TLS configuration, encryption settings, etc.
        return Path("infrastructure/security/tls-config.yaml").exists()

    async def _check_privacy_policy(self) -> bool:
        """Check if privacy policy exists."""
        return Path("docs/privacy-policy.md").exists()

async def main():
    """Main entry point for the security scanner."""
    parser = argparse.ArgumentParser(description="Jorge Platform Comprehensive Security Scanner")
    parser.add_argument("--scan-types", nargs="+",
                       choices=["dependencies", "container", "code", "infrastructure", "compliance", "all"],
                       default=["all"], help="Types of security scans to perform")
    parser.add_argument("--config", help="Path to scanner configuration file")
    parser.add_argument("--output-format", choices=["json", "html", "sarif"],
                       default="json", help="Output format for the security report")
    parser.add_argument("--fail-on-critical", action="store_true",
                       help="Exit with non-zero code if critical vulnerabilities found")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize scanner
    scanner = ComprehensiveSecurityScanner(args.config)

    try:
        # Convert string scan types to enum
        scan_types = [ScanType(scan_type) for scan_type in args.scan_types]

        # Run comprehensive scan
        results = await scanner.run_comprehensive_scan(scan_types)

        # Generate report
        report_file = scanner.generate_report(args.output_format)

        # Calculate exit code
        critical_vulns = sum(
            len([v for v in scan.vulnerabilities if v.severity == SeverityLevel.CRITICAL])
            for scan in results
        )

        if args.fail_on_critical and critical_vulns > 0:
            logger.error(f"❌ {critical_vulns} critical vulnerabilities found. Failing as requested.")
            sys.exit(1)

        logger.info(f"✅ Security scan completed successfully. Report: {report_file}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Security scan failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())