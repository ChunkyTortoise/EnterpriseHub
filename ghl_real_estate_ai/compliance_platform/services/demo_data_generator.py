"""
Enterprise AI Compliance Platform - Demo Data Generator

Generates realistic synthetic data for demos and presentations.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..models.compliance_models import (
    AIModelRegistration,
    ComplianceStatus,
    PolicyViolation,
    RegulationType,
    RiskLevel,
    ViolationSeverity,
)


class DemoDataGenerator:
    """
    Generate realistic demo data for compliance platform presentations.

    Creates:
    - AI model registrations across industries
    - Compliance violations with varying severities
    - Risk assessments and scores
    - Trend data for visualizations
    """

    # Industry-specific model templates
    MODEL_TEMPLATES = [
        # Healthcare
        {
            "name": "DiagnosticAI Pro",
            "model_type": "classification",
            "provider": "internal",
            "use_case_category": "healthcare",
            "description": "Medical image analysis for diagnostic support",
            "intended_use": "Assist radiologists in identifying potential abnormalities in X-rays and CT scans",
            "data_residency": ["us", "eu"],
            "personal_data": True,
            "sensitive_data": True,
            "base_risk": RiskLevel.HIGH,
        },
        {
            "name": "PatientFlow Optimizer",
            "model_type": "prediction",
            "provider": "internal",
            "use_case_category": "healthcare",
            "description": "Hospital resource allocation and patient flow prediction",
            "intended_use": "Optimize hospital bed allocation and staff scheduling",
            "data_residency": ["us"],
            "personal_data": True,
            "sensitive_data": False,
            "base_risk": RiskLevel.LIMITED,
        },
        # Finance
        {
            "name": "FraudGuard ML",
            "model_type": "classification",
            "provider": "internal",
            "use_case_category": "finance",
            "description": "Real-time transaction fraud detection",
            "intended_use": "Identify potentially fraudulent transactions for review",
            "data_residency": ["us", "eu"],
            "personal_data": True,
            "sensitive_data": True,
            "base_risk": RiskLevel.HIGH,
        },
        {
            "name": "CreditScore AI",
            "model_type": "regression",
            "provider": "internal",
            "use_case_category": "finance",
            "description": "Automated credit scoring for loan applications",
            "intended_use": "Provide credit risk assessment for lending decisions",
            "data_residency": ["us"],
            "personal_data": True,
            "sensitive_data": True,
            "base_risk": RiskLevel.HIGH,
        },
        {
            "name": "MarketSense Predictor",
            "model_type": "prediction",
            "provider": "anthropic",
            "use_case_category": "finance",
            "description": "Market trend analysis and prediction",
            "intended_use": "Assist traders with market movement predictions",
            "data_residency": ["us"],
            "personal_data": False,
            "sensitive_data": False,
            "base_risk": RiskLevel.LIMITED,
        },
        # HR/Employment
        {
            "name": "TalentMatch AI",
            "model_type": "classification",
            "provider": "internal",
            "use_case_category": "employment",
            "description": "Resume screening and candidate matching",
            "intended_use": "Assist recruiters in identifying qualified candidates",
            "data_residency": ["eu"],
            "personal_data": True,
            "sensitive_data": False,
            "base_risk": RiskLevel.HIGH,
        },
        {
            "name": "PerformancePredict",
            "model_type": "regression",
            "provider": "internal",
            "use_case_category": "employment",
            "description": "Employee performance prediction and analytics",
            "intended_use": "Identify factors affecting employee performance",
            "data_residency": ["us", "eu"],
            "personal_data": True,
            "sensitive_data": False,
            "base_risk": RiskLevel.HIGH,
        },
        # Customer Service
        {
            "name": "CustomerBot Pro",
            "model_type": "nlp",
            "provider": "anthropic",
            "use_case_category": "customer_service",
            "description": "AI-powered customer support chatbot",
            "intended_use": "Handle customer inquiries and support requests",
            "data_residency": ["us", "eu"],
            "personal_data": True,
            "sensitive_data": False,
            "base_risk": RiskLevel.LIMITED,
        },
        {
            "name": "SentimentAnalyzer",
            "model_type": "nlp",
            "provider": "openai",
            "use_case_category": "marketing",
            "description": "Social media sentiment analysis",
            "intended_use": "Analyze customer sentiment from social media",
            "data_residency": ["us"],
            "personal_data": False,
            "sensitive_data": False,
            "base_risk": RiskLevel.MINIMAL,
        },
        # Operations
        {
            "name": "SupplyChain Optimizer",
            "model_type": "optimization",
            "provider": "internal",
            "use_case_category": "operations",
            "description": "Supply chain demand forecasting and optimization",
            "intended_use": "Optimize inventory levels and logistics",
            "data_residency": ["us"],
            "personal_data": False,
            "sensitive_data": False,
            "base_risk": RiskLevel.MINIMAL,
        },
        {
            "name": "QualityVision AI",
            "model_type": "computer_vision",
            "provider": "internal",
            "use_case_category": "manufacturing",
            "description": "Automated quality inspection system",
            "intended_use": "Detect defects in manufactured products",
            "data_residency": ["us", "eu"],
            "personal_data": False,
            "sensitive_data": False,
            "base_risk": RiskLevel.LIMITED,
        },
        # Legal/Compliance
        {
            "name": "ContractAnalyzer",
            "model_type": "nlp",
            "provider": "anthropic",
            "use_case_category": "legal",
            "description": "Contract analysis and risk identification",
            "intended_use": "Extract key terms and identify risks in contracts",
            "data_residency": ["us", "eu"],
            "personal_data": False,
            "sensitive_data": True,
            "base_risk": RiskLevel.LIMITED,
        },
    ]

    # Violation templates
    VIOLATION_TEMPLATES = [
        {
            "policy_name": "Technical Documentation",
            "regulation": RegulationType.EU_AI_ACT,
            "title": "Incomplete Technical Documentation",
            "description": "Technical documentation does not meet Annex IV requirements",
            "severity": ViolationSeverity.MEDIUM,
            "potential_fine": 7_500_000,
        },
        {
            "policy_name": "Human Oversight",
            "regulation": RegulationType.EU_AI_ACT,
            "title": "Insufficient Human Oversight Mechanisms",
            "description": "High-risk AI system lacks adequate human oversight capability",
            "severity": ViolationSeverity.HIGH,
            "potential_fine": 15_000_000,
        },
        {
            "policy_name": "Record-Keeping",
            "regulation": RegulationType.EU_AI_ACT,
            "title": "Audit Logging Not Implemented",
            "description": "Automatic event logging not enabled for high-risk system",
            "severity": ViolationSeverity.HIGH,
            "potential_fine": 15_000_000,
        },
        {
            "policy_name": "Data Governance",
            "regulation": RegulationType.EU_AI_ACT,
            "title": "Training Data Quality Issues",
            "description": "Training data does not meet quality criteria specified in Article 10",
            "severity": ViolationSeverity.HIGH,
            "potential_fine": 15_000_000,
        },
        {
            "policy_name": "PHI Encryption",
            "regulation": RegulationType.HIPAA,
            "title": "PHI Not Encrypted",
            "description": "Protected Health Information stored without encryption",
            "severity": ViolationSeverity.CRITICAL,
            "potential_fine": 1_500_000,
        },
        {
            "policy_name": "Audit Controls",
            "regulation": RegulationType.HIPAA,
            "title": "Missing HIPAA Audit Logs",
            "description": "Access to PHI not being logged per HIPAA requirements",
            "severity": ViolationSeverity.HIGH,
            "potential_fine": 250_000,
        },
        {
            "policy_name": "Business Associate Agreement",
            "regulation": RegulationType.HIPAA,
            "title": "Missing BAA with AI Provider",
            "description": "No Business Associate Agreement executed with third-party AI provider",
            "severity": ViolationSeverity.HIGH,
            "potential_fine": 1_500_000,
        },
        {
            "policy_name": "Model Risk Management",
            "regulation": RegulationType.SEC_AI_GUIDANCE,
            "title": "Insufficient Model Validation",
            "description": "AI model used in trading decisions lacks proper validation",
            "severity": ViolationSeverity.HIGH,
            "potential_fine": 0,
        },
        {
            "policy_name": "DPIA Requirement",
            "regulation": RegulationType.GDPR,
            "title": "DPIA Not Conducted",
            "description": "Data Protection Impact Assessment required but not completed",
            "severity": ViolationSeverity.HIGH,
            "potential_fine": 20_000_000,
        },
        {
            "policy_name": "Automated Decision-Making",
            "regulation": RegulationType.GDPR,
            "title": "Missing Human Review for Automated Decisions",
            "description": "No mechanism for human review of significant automated decisions",
            "severity": ViolationSeverity.HIGH,
            "potential_fine": 20_000_000,
        },
        {
            "policy_name": "Transparency",
            "regulation": RegulationType.EU_AI_ACT,
            "title": "AI System Disclosure Missing",
            "description": "Users not informed they are interacting with an AI system",
            "severity": ViolationSeverity.MEDIUM,
            "potential_fine": 7_500_000,
        },
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the Demo Data Generator.

        Args:
            seed: Random seed for reproducible demos
        """
        if seed:
            random.seed(seed)

    def generate_demo_models(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate demo AI model registrations.

        Args:
            count: Number of models to generate

        Returns:
            List of model dictionaries
        """
        models = []
        templates = random.sample(self.MODEL_TEMPLATES, min(count, len(self.MODEL_TEMPLATES)))

        for i, template in enumerate(templates):
            model = {
                "name": template["name"],
                "version": f"1.{random.randint(0, 9)}.{random.randint(0, 99)}",
                "description": template["description"],
                "model_type": template["model_type"],
                "provider": template["provider"],
                "deployment_location": random.choice(["cloud", "on_premise", "hybrid"]),
                "data_residency": template["data_residency"],
                "intended_use": template["intended_use"],
                "use_case_category": template["use_case_category"],
                "personal_data_processed": template["personal_data"],
                "sensitive_data_processed": template["sensitive_data"],
                "risk_level": template["base_risk"],
                "registered_by": f"admin_{random.randint(1, 5)}@company.com",
            }
            models.append(model)

        return models

    def generate_demo_violations(
        self,
        model_ids: List[str],
        count: int = 5,
    ) -> List[PolicyViolation]:
        """
        Generate demo violations.

        Args:
            model_ids: List of model IDs to associate violations with
            count: Number of violations to generate

        Returns:
            List of PolicyViolation instances
        """
        violations = []
        templates = random.sample(self.VIOLATION_TEMPLATES, min(count, len(self.VIOLATION_TEMPLATES)))

        for template in templates:
            model_id = random.choice(model_ids)
            days_ago = random.randint(1, 30)

            violation = PolicyViolation(
                regulation=template["regulation"],
                policy_id=f"{template['regulation'].value.upper()}-{random.randint(1, 10):03d}",
                policy_name=template["policy_name"],
                severity=template["severity"],
                title=template["title"],
                description=template["description"],
                affected_systems=[model_id],
                detected_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
                potential_fine=template["potential_fine"],
                status=random.choice(["open", "acknowledged", "in_remediation"]),
            )
            violations.append(violation)

        return violations

    def generate_compliance_scores(self, model_count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate demo compliance scores for trends.

        Args:
            model_count: Number of models

        Returns:
            List of score dictionaries
        """
        scores = []
        for _ in range(model_count):
            base_score = random.uniform(60, 98)
            scores.append(
                {
                    "overall_score": round(base_score, 1),
                    "transparency": round(random.uniform(base_score - 15, min(100, base_score + 10)), 1),
                    "fairness": round(random.uniform(base_score - 10, min(100, base_score + 10)), 1),
                    "accountability": round(random.uniform(base_score - 10, min(100, base_score + 10)), 1),
                    "robustness": round(random.uniform(base_score - 15, min(100, base_score + 10)), 1),
                    "privacy": round(random.uniform(base_score - 10, min(100, base_score + 10)), 1),
                    "security": round(random.uniform(base_score - 5, min(100, base_score + 10)), 1),
                }
            )
        return scores

    def generate_trend_data(self, days: int = 90) -> List[Dict[str, Any]]:
        """
        Generate compliance trend data for charts.

        Args:
            days: Number of days of history

        Returns:
            List of daily data points
        """
        data = []
        base_score = 75.0
        base_violations = 8

        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=days - i - 1)

            # Simulate gradual improvement with some noise
            improvement = i * 0.15  # Gradual improvement
            noise = random.uniform(-2, 2)
            score = min(98, base_score + improvement + noise)

            violation_reduction = i * 0.05
            violations = max(1, int(base_violations - violation_reduction + random.randint(-1, 1)))

            data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "compliance_score": round(score, 1),
                    "active_violations": violations,
                    "models_assessed": random.randint(8, 12),
                    "high_risk_count": random.randint(2, 4),
                }
            )

        return data

    def generate_risk_heatmap_data(self) -> List[Dict[str, Any]]:
        """
        Generate data for risk heatmap visualization.

        Returns:
            List of risk data points
        """
        categories = [
            "Transparency",
            "Fairness",
            "Accountability",
            "Robustness",
            "Privacy",
            "Security",
        ]

        regulations = [
            "EU AI Act",
            "HIPAA",
            "SEC",
            "GDPR",
        ]

        heatmap_data = []
        for category in categories:
            for regulation in regulations:
                # Generate realistic risk scores
                risk_score = random.randint(10, 85)
                heatmap_data.append(
                    {
                        "category": category,
                        "regulation": regulation,
                        "risk_score": risk_score,
                        "status": "critical" if risk_score > 70 else "warning" if risk_score > 40 else "normal",
                    }
                )

        return heatmap_data

    def generate_executive_metrics(self) -> Dict[str, Any]:
        """
        Generate executive dashboard metrics.

        Returns:
            Dictionary of executive metrics
        """
        return {
            "total_models": random.randint(10, 15),
            "compliant_models": random.randint(6, 10),
            "average_compliance_score": round(random.uniform(78, 92), 1),
            "total_violations": random.randint(3, 12),
            "critical_violations": random.randint(0, 2),
            "high_violations": random.randint(1, 4),
            "potential_exposure": random.randint(10, 50) * 1_000_000,
            "compliance_trend": round(random.uniform(1, 8), 1),
            "remediation_rate": round(random.uniform(75, 95), 1),
            "audit_readiness": round(random.uniform(80, 98), 1),
        }

    def generate_ai_demo_responses(self) -> Dict[str, Any]:
        """
        Generate AI-style demo responses for compliance analysis.

        Returns:
            Dictionary containing AI-generated explanations, summaries, and recommendations
        """
        return {
            "risk_explanations": {
                "transparency": {
                    "score": 68,
                    "explanation": (
                        "The model's transparency score of 68% indicates moderate gaps in explainability "
                        "and documentation. While the model includes feature importance outputs through "
                        "SHAP analysis, the absence of comprehensive model cards and user-facing explanations "
                        "creates friction in stakeholder trust. The high-risk healthcare context amplifies this "
                        "concern—clinicians need clear reasoning for diagnostic recommendations."
                    ),
                    "key_concerns": [
                        "Limited model documentation per Annex IV EU AI Act requirements",
                        "No user-facing explanation interfaces for clinicians",
                        "SHAP outputs not integrated into clinical workflows",
                        "Missing documentation of training data characteristics",
                        "Insufficient versioning and changelog documentation",
                    ],
                    "mitigation_strategies": [
                        "Implement SHAP values visualization in clinical UI with clinical context",
                        "Create comprehensive model cards (NIST AI 600-1, Google Model Cards)",
                        "Develop clinician-facing explanation dashboard",
                        "Establish automated documentation generation on model updates",
                        "Conduct quarterly documentation audits per EU AI Act Annex IV",
                    ],
                    "implementation_timeline": "8-12 weeks",
                    "resource_estimate": {"engineering": 320, "compliance": 80, "clinical_review": 120},
                },
                "fairness": {
                    "score": 72,
                    "explanation": (
                        "Fairness assessment reveals 72% compliance with bias detection standards. "
                        "The model demonstrates reasonable performance equity across demographic groups "
                        "(within 3-5% variance on sensitivity/specificity), but historical training data "
                        "imbalances persist in underrepresented populations. The recruitment bias inherent "
                        "to healthcare data may disadvantage certain communities."
                    ),
                    "key_concerns": [
                        "5.2% disparity in false positive rates across racial/ethnic groups",
                        "Training data skewed toward majority populations (73% vs. 27%)",
                        "No intersectional bias analysis (age + gender combinations)",
                        "Missing fairness metrics monitoring in production",
                        "Limited documentation of fairness testing methodology",
                    ],
                    "mitigation_strategies": [
                        "Conduct fairness audit quarterly using ISO/IEC 42001 framework",
                        "Implement Fairlearn/AI Fairness 360 bias detection in CI/CD",
                        "Expand training data with balanced representation (target 40%+ minority)",
                        "Add intersectional fairness monitoring (age × gender × ethnicity)",
                        "Establish clinical review board for bias assessment",
                    ],
                    "implementation_timeline": "10-14 weeks",
                    "resource_estimate": {"engineering": 240, "data_science": 160, "compliance": 100},
                },
                "accountability": {
                    "score": 81,
                    "explanation": (
                        "Accountability measures score 81%, reflecting established governance structures. "
                        "The organization has documented model ownership, change control processes, and "
                        "incident reporting mechanisms. However, audit trail completeness and incident response "
                        "timelines require enhancement to meet SEC and HIPAA standards for critical systems."
                    ),
                    "key_concerns": [
                        "Audit logs lack immutable storage (current: 90-day retention needed: 7-year)",
                        "Incident response SLA: 48 hours (required: 4 hours for HIPAA breaches)",
                        "Model change log incomplete for versions prior to 2024",
                        "No documented appeals process for AI-driven decisions",
                        "Missing human-in-the-loop verification documentation",
                    ],
                    "mitigation_strategies": [
                        "Implement immutable audit logging (blockchain or write-once storage)",
                        "Establish 4-hour incident response protocol with automated alerting",
                        "Migrate audit logs to 7-year retention with compliance indexing",
                        "Create formal appeals process documented in patient-facing materials",
                        "Implement human review checkpoints for high-confidence predictions",
                    ],
                    "implementation_timeline": "6-9 weeks",
                    "resource_estimate": {"engineering": 280, "compliance": 120, "operations": 80},
                },
                "robustness": {
                    "score": 74,
                    "explanation": (
                        "Robustness assessment yields 74% compliance. Model performance remains stable "
                        "across standard test distributions (±2% variance), but adversarial robustness testing "
                        "reveals vulnerabilities to input perturbations common in healthcare (image compression, "
                        "rotation). Production monitoring detects drift quarterly but lacks real-time thresholds."
                    ),
                    "key_concerns": [
                        "Performance degrades 8-12% under adversarial image transformations",
                        "Real-time model drift detection: 90-day lag (should be 24-48 hours)",
                        "Limited out-of-distribution detection for unusual imaging patterns",
                        "No graceful degradation path when confidence drops below threshold",
                        "Version rollback procedures not tested in 18 months",
                    ],
                    "mitigation_strategies": [
                        "Implement adversarial robustness testing (ImageNet-C, JPEG compression)",
                        "Deploy real-time drift detection with 4-hour alert threshold",
                        "Add out-of-distribution detection layer (Mahalanobis, isolation forest)",
                        "Establish automatic prediction hold when confidence < 0.65",
                        "Conduct monthly rollback drills with documented procedures",
                    ],
                    "implementation_timeline": "12-16 weeks",
                    "resource_estimate": {"ml_engineering": 400, "qa": 200, "devops": 120},
                },
                "privacy": {
                    "score": 77,
                    "explanation": (
                        "Privacy score of 77% reflects HIPAA-baseline technical controls. "
                        "PHI encryption, access logging, and de-identification processes exist but require "
                        "strengthening per HIPAA Omnibus Rule. Data retention policies are documented but "
                        "lack automated enforcement. Third-party data sharing agreements need standardization."
                    ),
                    "key_concerns": [
                        "PHI stored with AES-128 encryption (should be AES-256 per NIST guidance)",
                        "No automated data deletion after training cycle completion",
                        "Access logs retained only 180 days (HIPAA minimum: 6 years)",
                        "4 data processors lack current Business Associate Agreements",
                        "De-identification methods not validated against HIPAA Safe Harbor standards",
                    ],
                    "mitigation_strategies": [
                        "Upgrade PHI encryption to AES-256 across all storage layers",
                        "Implement automated data purging with cryptographic erasure verification",
                        "Extend access log retention to 6 years with immutable storage",
                        "Execute BAAs with remaining 4 processors within 30 days",
                        "Conduct HIPAA Safe Harbor validation audit on de-identification methods",
                    ],
                    "implementation_timeline": "8-11 weeks",
                    "resource_estimate": {"security": 280, "compliance": 160, "engineering": 120},
                },
                "security": {
                    "score": 83,
                    "explanation": (
                        "Security posture scores 83%, indicating robust fundamental controls. "
                        "Infrastructure hardening, authentication mechanisms, and vulnerability scanning are active. "
                        "However, supply chain security (model dependencies) and ML-specific attack vectors require "
                        "strengthened governance to reach enterprise resilience standards."
                    ),
                    "key_concerns": [
                        "Model dependencies: 3 packages with known CVEs (low severity, unpatched)",
                        "No model poisoning detection or input validation framework",
                        "Federated learning pipeline lacks differential privacy guarantees",
                        "Security testing: annual penetration testing (should be quarterly)",
                        "Incident response plan exists but not exercised in 14 months",
                    ],
                    "mitigation_strategies": [
                        "Patch all CVEs and implement automated dependency vulnerability scanning",
                        "Add input validation framework with anomaly detection",
                        "Integrate differential privacy into federated learning (ε=1.0 privacy budget)",
                        "Schedule quarterly penetration testing with ML-focused attack scenarios",
                        "Conduct tabletop incident response exercise quarterly",
                    ],
                    "implementation_timeline": "10-14 weeks",
                    "resource_estimate": {"security": 320, "ml_engineering": 160, "devops": 100},
                },
            },
            "violation_explanations": {
                "critical": {
                    "severity_level": "CRITICAL",
                    "significance": (
                        "Critical violations represent existential compliance gaps that expose the organization "
                        "to regulatory enforcement action, potential criminal liability, and operational suspension. "
                        "These require executive escalation and immediate remediation."
                    ),
                    "business_impact": (
                        "Potential regulatory fines up to €30 million (6% of global annual revenue) under EU AI Act. "
                        "HIPAA violations carry up to $1.5M per violation. SEC enforcement may restrict trading operations. "
                        "Reputational damage could reduce customer acquisition by 20-40% based on sector precedents."
                    ),
                    "remediation_priority": "IMMEDIATE - within 24-48 hours",
                    "escalation_path": "Chief Compliance Officer → C-Suite → Board Compliance Committee",
                    "example_violations": [
                        "Unencrypted PHI storage (HIPAA 45 CFR 164.312(a)(2)(i))",
                        "High-risk AI deployed without human oversight (EU AI Act Article 26)",
                    ],
                },
                "high": {
                    "severity_level": "HIGH",
                    "significance": (
                        "High-severity violations create substantial compliance risk and regulatory visibility. "
                        "While not immediately operational threats, they require structured remediation within defined timelines "
                        "and executive notification."
                    ),
                    "business_impact": (
                        "Potential fines €15M-€20M (3-4% of revenue). Regulatory inquiry triggers 60-90 day investigation. "
                        "May result in enhanced audit requirements costing $200K-$500K annually. Customer contracts may require "
                        "enhanced compliance certifications."
                    ),
                    "remediation_priority": "URGENT - within 2-4 weeks",
                    "escalation_path": "Compliance Director → Chief Compliance Officer → CEO",
                    "example_violations": [
                        "Insufficient human oversight mechanisms (EU AI Act Annex III)",
                        "Missing DPIA for high-risk processing (GDPR Article 35)",
                    ],
                },
                "medium": {
                    "severity_level": "MEDIUM",
                    "significance": (
                        "Medium-severity violations indicate process gaps or incomplete implementations. "
                        "These require documented remediation plans but allow extended timelines if risk mitigated through "
                        "compensating controls."
                    ),
                    "business_impact": (
                        "Potential fines €7.5M-€10M or 1.5-2% of revenue. Regulatory correspondence requires formal response. "
                        "May affect audit opinions or compliance certifications. Addressable within normal change management cycles."
                    ),
                    "remediation_priority": "PLANNED - within 6-12 weeks",
                    "escalation_path": "Compliance Team → Compliance Director",
                    "example_violations": [
                        "Incomplete technical documentation (EU AI Act Annex IV)",
                        "Missing AI system disclosure to end-users",
                    ],
                },
            },
            "executive_summary": (
                "## Compliance Executive Summary\n\n"
                "Your organization's AI governance infrastructure demonstrates **baseline competency** across "
                "core compliance dimensions (average score: 79%), but requires strategic investments in three areas:\n\n"
                "### 1. Transparency & Explainability (68%)\n"
                "Healthcare clinicians lack clear AI reasoning. Implement model cards, SHAP visualizations, and "
                "documentation per EU AI Act Annex IV within 12 weeks. *Priority: HIGH*\n\n"
                "### 2. Real-Time Monitoring & Robustness (74%)\n"
                "Production drift detection operates on 90-day lag; healthcare requires 24-48 hour thresholds. "
                "Deploy automated monitoring with alert escalation. *Priority: HIGH*\n\n"
                "### 3. Privacy & Data Retention (77%)\n"
                "Encryption meets baseline (AES-128) but not NIST guidance (AES-256). Upgrade encryption, "
                "extend audit log retention to 6 years, execute pending BAAs. *Priority: MEDIUM*\n\n"
                "### Remediation Roadmap: 90-Day Sprint\n"
                "- **Weeks 1-4**: Deploy critical fixes (encryption upgrade, access log retention, BAA execution)\n"
                "- **Weeks 5-8**: Implement monitoring & alerting infrastructure\n"
                "- **Weeks 9-12**: Establish ongoing governance (quarterly audits, tabletop exercises)\n\n"
                "**Compliance Exposure**: €25M-€50M potential regulatory fines if violations persist. "
                "Recommended immediate investment: $1.2M-$1.8M in infrastructure & staffing to achieve 90%+ compliance within 6 months.\n"
            ),
            "remediation_roadmap": {
                "overview": "Strategic 90-day compliance acceleration program",
                "total_estimated_cost": 1_500_000,
                "estimated_timeline_weeks": 12,
                "team_composition": {
                    "engineering": 1200,
                    "ml_engineering": 400,
                    "compliance": 360,
                    "security": 280,
                    "qa_testing": 200,
                    "legal_review": 80,
                    "devops": 120,
                    "clinical_review": 120,
                },
                "phases": [
                    {
                        "phase": "Phase 1: Critical Risk Mitigation",
                        "duration_weeks": 4,
                        "priority": "IMMEDIATE",
                        "objectives": [
                            "Upgrade PHI encryption AES-128 → AES-256",
                            "Extend audit log retention to 6 years",
                            "Execute pending Business Associate Agreements",
                            "Implement 24-hour model monitoring alerts",
                        ],
                        "deliverables": [
                            "Encryption migration completed with zero downtime",
                            "Audit log migration to immutable storage (S3 Object Lock / Azure Immutable Blobs)",
                            "4 executed BAAs with compliance verification",
                            "Real-time drift detection dashboard deployed",
                        ],
                        "risks": [
                            "Service interruption during encryption migration",
                            "Data compliance during migration",
                        ],
                        "mitigation": [
                            "Blue-green deployment",
                            "Data replication verification",
                            "Regulatory pre-notification",
                        ],
                    },
                    {
                        "phase": "Phase 2: Transparency & Explainability",
                        "duration_weeks": 5,
                        "priority": "HIGH",
                        "objectives": [
                            "Develop comprehensive model cards (NIST AI 600-1 standard)",
                            "Implement SHAP value visualization in clinical UI",
                            "Create automated documentation generation pipeline",
                            "Establish clinician-facing explanation dashboard",
                        ],
                        "deliverables": [
                            "Model cards for all 12 active models in production",
                            "SHAP integration in diagnostic recommendation flow",
                            "Documentation auto-generation on each model update",
                            "Clinician explanation interface with audit logging",
                        ],
                        "risks": ["Clinician workflow disruption", "Documentation maintenance burden"],
                        "mitigation": ["UX testing with 10+ clinicians", "Template-driven documentation automation"],
                    },
                    {
                        "phase": "Phase 3: Fairness & Bias Governance",
                        "duration_weeks": 4,
                        "priority": "HIGH",
                        "objectives": [
                            "Conduct intersectional bias audit (demographic + intersection)",
                            "Implement automated bias detection in CI/CD (Fairlearn)",
                            "Establish diversity in training data targets (40%+ underrepresented)",
                            "Create fairness monitoring dashboard with alerts",
                        ],
                        "deliverables": [
                            "Baseline fairness audit report (racial, gender, age, intersectional)",
                            "Fairness gates in model training pipeline",
                            "Training data diversity plan with acquisition milestones",
                            "Quarterly fairness audit schedule established",
                        ],
                        "risks": ["Data acquisition costs", "Model performance trade-offs"],
                        "mitigation": ["Partner with healthcare data providers", "Performance degradation testing"],
                    },
                    {
                        "phase": "Phase 4: Accountability & Governance",
                        "duration_weeks": 3,
                        "priority": "MEDIUM",
                        "objectives": [
                            "Implement immutable audit logging (blockchain or write-once)",
                            "Establish formal appeals process for AI-driven decisions",
                            "Create incident response protocol with 4-hour SLA",
                            "Document version control and rollback procedures",
                        ],
                        "deliverables": [
                            "Immutable audit log infrastructure deployed",
                            "Patient-facing appeals process documentation",
                            "Incident response playbook with automation",
                            "Monthly rollback drill schedule",
                        ],
                        "risks": ["Incident response overhead", "Patient communication complexity"],
                        "mitigation": ["Automated incident routing", "Template-driven patient communications"],
                    },
                ],
                "success_metrics": {
                    "transparency_score_target": 85,
                    "fairness_score_target": 85,
                    "accountability_score_target": 92,
                    "robustness_score_target": 88,
                    "privacy_score_target": 92,
                    "security_score_target": 90,
                    "overall_compliance_target": 89,
                    "critical_violations_target": 0,
                    "high_violations_target": 0,
                    "medium_violations_open_days_target": 30,
                },
                "governance": {
                    "steering_committee": "CTO + Chief Compliance Officer + VP Operations",
                    "meeting_frequency": "Weekly during 90-day sprint, then monthly",
                    "decision_authority": "Steering committee approves phase gates, escalates blockers",
                    "communication_cadence": "Daily standup (team), weekly status (leadership), bi-weekly board",
                },
            },
        }

    def generate_full_demo_dataset(self) -> Dict[str, Any]:
        """
        Generate complete demo dataset for dashboard.

        Returns:
            Complete demo data dictionary
        """
        models = self.generate_demo_models(12)
        model_ids = [str(uuid4()) for _ in models]
        ai_responses = self.generate_ai_demo_responses()

        return {
            "models": models,
            "model_ids": model_ids,
            "violations": [v.model_dump() for v in self.generate_demo_violations(model_ids, 8)],
            "scores": self.generate_compliance_scores(12),
            "trends": self.generate_trend_data(90),
            "heatmap": self.generate_risk_heatmap_data(),
            "executive_metrics": self.generate_executive_metrics(),
            "ai_responses": ai_responses,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
