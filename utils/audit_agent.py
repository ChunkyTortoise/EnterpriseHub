"""
Audit Agent - Simulated Code & Architecture Analysis Logic.
Provides intelligent findings for the Technical Due Diligence (S2) module.
"""

import json
import random
import re
from typing import Any, Dict, List, Optional


class AuditAgent:
    """Simulated AI Architect performing an automated audit."""

    def __init__(
        self,
        target_name: str,
        tech_stack: str,
        compliance_needs: List[str],
        uploaded_file_content: Optional[str] = None,
        file_type: Optional[str] = None,
    ):
        self.target_name = target_name
        self.tech_stack = tech_stack.lower()
        self.compliance_needs = compliance_needs
        self.uploaded_file_content = uploaded_file_content
        self.file_type = file_type
        self.file_findings = []

        # Analyze uploaded file if present
        if uploaded_file_content and file_type:
            self._analyze_uploaded_file()

    def analyze_architecture(self) -> List[Dict[str, Any]]:
        """Generates detailed findings based on inputs."""
        findings = []

        # 1. Dependency Analysis
        if any(x in self.tech_stack for x in ["openai", "anthropic", "llm", "api"]):
            findings.append(
                {
                    "category": "Dependency",
                    "severity": "High",
                    "issue": "Critical Vendor Lock-in (LLM API)",
                    "details": "The system lacks a model-agnostic abstraction layer. Outages or pricing changes at the primary provider create existential risk.",
                    "remediation": "Implement an orchestrator (e.g., LiteLLM or custom proxy) to enable multi-model failover.",
                }
            )

        # 2. Infrastructure Analysis
        if "aws" in self.tech_stack:
            findings.append(
                {
                    "category": "Infrastructure",
                    "severity": "Medium",
                    "issue": "Stateless Scaling Limits",
                    "details": f"AWS architecture for {self.target_name} shows use of Lambdas for long-running LLM tasks, risking timeouts.",
                    "remediation": "Migrate long-running inference tasks to ECS or EKS with dedicated GPU instances.",
                }
            )
        elif "azure" in self.tech_stack:
            findings.append(
                {
                    "category": "Infrastructure",
                    "severity": "Medium",
                    "issue": "Regional Quota Constraints",
                    "details": "Azure OpenAI instances are often region-locked with strict TPM limits.",
                    "remediation": "Implement global load balancing across multiple Azure regions.",
                }
            )

        # 3. Security & Compliance
        if "hipaa" in self.compliance_needs:
            findings.append(
                {
                    "category": "Security",
                    "severity": "Critical",
                    "issue": "PII Leakage in LLM Logs",
                    "details": "Default logging configurations for LLM providers often capture full prompt context containing PHI.",
                    "remediation": "Implement a local PII/PHI scrubbing layer before data leaves the VPC.",
                }
            )
        elif "gdpr" in self.compliance_needs or "soc2" in self.compliance_needs:
            findings.append(
                {
                    "category": "Security",
                    "severity": "High",
                    "issue": "Data Residency Audit Gap",
                    "details": "System cannot guarantee that data processed by 3rd party APIs remains within required jurisdictions.",
                    "remediation": "Switch to regionally-pinned API endpoints or deploy self-hosted models.",
                }
            )

        # 4. Technical Debt (Architecture)
        if any(x in self.tech_stack for x in ["modular", "microservices"]):
            findings.append(
                {
                    "category": "Architecture",
                    "severity": "Low",
                    "issue": "Inter-service Latency",
                    "details": "Modular design is robust but increases inference latency due to multiple network hops.",
                    "remediation": "Optimize with gRPC or shared-memory buffers for high-throughput nodes.",
                }
            )
        else:
            findings.append(
                {
                    "category": "Architecture",
                    "severity": "Medium",
                    "issue": "Monolithic Bottleneck",
                    "details": "Tight coupling between UI and Model logic prevents independent scaling of the inference engine.",
                    "remediation": "De-couple model serving into a dedicated microservice.",
                }
            )

        return findings

    def get_system_debt_data(self) -> Dict[str, Any]:
        """Generates mock data for a debt visualization graph."""
        # Nodes: Component names, Edges: Debt levels
        return {
            "nodes": ["Frontend", "API Gateway", "Auth", "LLM Orchestrator", "Vector DB", "Main DB"],
            "debt_scores": [
                random.randint(10, 30),
                random.randint(20, 50),
                random.randint(5, 15),
                random.randint(40, 80),
                random.randint(15, 45),
                random.randint(30, 60),
            ],
        }

    def _analyze_uploaded_file(self):
        """Analyzes uploaded architecture files for red flags."""
        content = self.uploaded_file_content.lower()

        # JSON/Terraform red flag patterns
        red_flags = {
            "hardcoded_credentials": [
                r'api[_-]?key\s*[:=]\s*["\'][a-zA-Z0-9]{20,}["\']',
                r'password\s*[:=]\s*["\'].+["\']',
                r'secret\s*[:=]\s*["\'].+["\']',
                r'token\s*[:=]\s*["\'][a-zA-Z0-9]{20,}["\']',
            ],
            "public_access": [
                r"public[_-]?access\s*[:=]\s*true",
                r"0\.0\.0\.0/0",
                r"ingress.*0\.0\.0\.0",
                r"publicly[_-]?accessible\s*[:=]\s*true",
            ],
            "unencrypted": [
                r"encrypt(ed|ion)?\s*[:=]\s*false",
                r"ssl[_-]?enabled\s*[:=]\s*false",
                r"tls\s*[:=]\s*false",
            ],
            "deprecated_versions": [
                r'python\s*[:=]\s*["\']2\.',
                r'node\s*[:=]\s*["\'][0-9]\.',
                r'tensorflow\s*[:=]\s*["\']1\.',
            ],
        }

        for category, patterns in red_flags.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.file_findings.append(
                        {
                            "category": "File Analysis",
                            "severity": "Critical"
                            if category in ["hardcoded_credentials", "public_access"]
                            else "High",
                            "issue": f"🚨 {category.replace('_', ' ').title()} Detected",
                            "details": f"Found {len(matches)} instance(s) of {category.replace('_', ' ')} in uploaded {self.file_type} file. Example: {matches[0][:50]}...",
                            "remediation": self._get_remediation_for_category(category),
                        }
                    )

    def _get_remediation_for_category(self, category: str) -> str:
        """Returns remediation advice for specific categories."""
        remediations = {
            "hardcoded_credentials": "Move all secrets to AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault. Use environment variables with proper IAM roles.",
            "public_access": "Implement VPC security groups, private subnets, and bastion hosts. Never expose databases or internal services to 0.0.0.0/0.",
            "unencrypted": "Enable encryption at rest and in transit. Use TLS 1.2+ for all network communication and AES-256 for storage.",
            "deprecated_versions": "Upgrade to supported versions immediately. Deprecated software lacks security patches and creates compliance violations.",
        }
        return remediations.get(category, "Consult security best practices for this issue.")

    def get_all_findings(self) -> List[Dict[str, Any]]:
        """Returns combined findings from architecture analysis and file upload."""
        base_findings = self.analyze_architecture()
        return base_findings + self.file_findings

    def generate_audit_report_markdown(self) -> str:
        """Generates a downloadable Markdown audit report."""
        findings = self.get_all_findings()

        report = f"""# Technical Audit Report: {self.target_name}
**Generated by**: EnterpriseHub AI Audit System  
**Date**: {self._get_current_date()}  
**Compliance Requirements**: {", ".join(self.compliance_needs) if self.compliance_needs else "None specified"}

---

## Executive Summary

This report identifies **{len(findings)}** priority findings across architecture, security, and infrastructure domains.

### Severity Breakdown
- **Critical**: {len([f for f in findings if f["severity"] == "Critical"])} issues
- **High**: {len([f for f in findings if f["severity"] == "High"])} issues
- **Medium**: {len([f for f in findings if f["severity"] == "Medium"])} issues
- **Low**: {len([f for f in findings if f["severity"] == "Low"])} issues

---

## Technology Stack Analysis

**Provided Stack**: {self.tech_stack}

"""

        # Add findings by severity
        for severity in ["Critical", "High", "Medium", "Low"]:
            severity_findings = [f for f in findings if f["severity"] == severity]
            if severity_findings:
                report += f"\n## {severity} Priority Findings\n\n"
                for i, finding in enumerate(severity_findings, 1):
                    report += f"""### {i}. {finding["issue"]}

**Category**: {finding.get("category", "General")}  
**Details**: {finding["details"]}

**Recommended Action**:  
{finding["remediation"]}

---

"""

        # Add recommendations
        report += """
## Next Steps

1. **Immediate**: Address all Critical severity issues within 48 hours
2. **Short-term**: Resolve High severity issues within 2 weeks
3. **Medium-term**: Plan remediation for Medium/Low issues in next sprint
4. **Continuous**: Implement automated security scanning in CI/CD pipeline

## Implementation Support

For detailed implementation guidance, contact:  
📧 caymanroden@gmail.com  
🌐 EnterpriseHub Technical Due Diligence (Service S2)

---

*This report is generated by AI-assisted analysis and should be validated by human architects before making critical decisions.*
"""

        return report

    def _get_current_date(self) -> str:
        """Returns current date string."""
        from datetime import datetime

        return datetime.now().strftime("%B %d, %Y")
