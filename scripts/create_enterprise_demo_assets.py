#!/usr/bin/env python3
"""
Create Enterprise Demo Assets Package
Packages all performance, security, and demo materials for sales handoff.
"""

import os
import shutil
from datetime import datetime

def main():
    print("📦 Packaging Enterprise Demo Assets...")
    
    # Create deliverables directory
    timestamp = datetime.now().strftime("%Y%m%d")
    output_dir = f"deliverables/enterprise_demo_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    files_to_package = [
        "CLIENT_PERFORMANCE_BENCHMARK.md",
        "VOICE_AI_DEMO_SCRIPT.md",
        "SOC2_READINESS_REPORT.md",
        "ENTERPRISE_PERFORMANCE_REPORT.md",
        "VOICE_AI_QA_REPORT.json",
        "PERFORMANCE_DASHBOARD.md",
        "monitoring_config.json",
        "ENTERPRISE_SCALABILITY_REPORT.md",
        "load_test_results.json"
    ]
    
    copied_count = 0
    for filename in files_to_package:
        if os.path.exists(filename):
            shutil.copy(filename, os.path.join(output_dir, filename))
            print(f"  ✅ Included: {filename}")
            copied_count += 1
        else:
            print(f"  ⚠️  Missing: {filename}")
            
    print(f"\n🎉 Package created at: {output_dir}")
    print(f"   Contains {copied_count} assets ready for sales team.")

if __name__ == "__main__":
    main()
