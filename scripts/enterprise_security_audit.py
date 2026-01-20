#!/usr/bin/env python3
"""
Enterprise Security Audit Script (SOC2 Prep)
Extends validation with specific compliance checks.
"""

import argparse
import asyncio
import sys
from scripts.validate_enterprise_security import SecurityValidator, Colors

async def main():
    parser = argparse.ArgumentParser(description='Enterprise Security Audit')
    parser.add_argument('--soc2-prep', action='store_true', help='Focus on SOC2 compliance')
    args = parser.parse_args()

    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("="*80)
    print("ENTERPRISE SECURITY AUDIT")
    print(f"Mode: {'SOC2 Preparation' if args.soc2_prep else 'Standard Audit'}")
    print("="*80)
    print(f"{Colors.ENDC}\n")

    validator = SecurityValidator()

    # Run checks
    validator.validate_authentication()
    validator.validate_data_protection()
    validator.validate_api_security()
    validator.validate_infrastructure_security()
    validator.validate_compliance()

    # Generate report
    report = validator.generate_report()
    
    if args.soc2_prep:
        # Save specific SOC2 report
        filename = "SOC2_READINESS_REPORT.md"
        with open(filename, 'w') as f:
            f.write("# SOC2 Readiness Assessment\n\n")
            f.write(f"**Date:** {report['timestamp']}\n\n")
            f.write("## Compliance Summary\n\n")
            f.write(f"- **SOC2 Status:** {report['compliance_assessment']['SOC2']}\n")
            f.write(f"- **Risk Score:** {report['risk_score']}\n\n")
            
            f.write("## Control Gaps\n\n")
            for severity in ["critical", "high"]:
                for finding in report['findings'][severity]:
                     if any("SOC2" in i for i in finding.get("compliance_impact", [])):
                         f.write(f"- [ ] **{finding['title']}**: {finding['remediation']}\n")
                         
        print(f"\n{Colors.OKGREEN}SOC2 Readiness Report saved to: {filename}{Colors.ENDC}")

    validator.save_report()
    
    if len(validator.findings["critical"]) > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
