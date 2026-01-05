#!/usr/bin/env python3
"""
Data Quality Agent - Fix JSON formatting issues
Fast-running agent focused on data integrity
"""

import json
import re
from pathlib import Path
from typing import Tuple, Dict, Any, List
import shutil
from datetime import datetime


class DataQualityAgent:
    """Fixes JSON formatting and validates data quality."""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.files_fixed = []
        self.errors_found = []
    
    def backup_file(self, file_path: Path) -> Path:
        """Create backup before modification."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f'.backup_{timestamp}.json')
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def fix_common_json_errors(self, content: str) -> Tuple[str, List[str]]:
        """Apply common JSON fixes."""
        fixes_applied = []
        original = content
        
        # Fix 1: Double closing braces }} → }
        pattern1 = r'}\s*}'
        if re.search(pattern1, content):
            content = re.sub(pattern1, '}', content)
            count = len(re.findall(pattern1, original))
            fixes_applied.append(f"Removed {count} double closing braces")
        
        # Fix 2: Double closing braces with comma }}, → },
        pattern2 = r'}\s*},\s*'
        if re.search(pattern2, content):
            content = re.sub(pattern2, '},\n', content)
            count = len(re.findall(pattern2, original))
            fixes_applied.append(f"Fixed {count} double braces with comma")
        
        # Fix 3: Trailing commas before closing brace
        pattern3 = r',(\s*[}\]])'
        if re.search(pattern3, content):
            content = re.sub(pattern3, r'\1', content)
            fixes_applied.append("Removed trailing commas")
        
        # Fix 4: Missing commas between objects
        # This is more complex and risky, skip for now
        
        return content, fixes_applied
    
    def validate_json(self, file_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate JSON file and return status."""
        try:
            content = file_path.read_text()
            data = json.loads(content)
            
            # Calculate stats
            stats = {
                "size_bytes": len(content),
                "size_kb": round(len(content) / 1024, 2)
            }
            
            if isinstance(data, dict):
                stats["keys"] = len(data.keys())
                stats["type"] = "object"
            elif isinstance(data, list):
                stats["items"] = len(data)
                stats["type"] = "array"
            
            return True, "Valid JSON", stats
            
        except json.JSONDecodeError as e:
            return False, f"JSON Error at line {e.lineno}, col {e.colno}: {e.msg}", {}
        except Exception as e:
            return False, f"Error: {str(e)}", {}
    
    def fix_json_file(self, file_path: Path, dry_run: bool = False) -> Dict[str, Any]:
        """Fix a JSON file and return results."""
        result = {
            "file": str(file_path),
            "status": "unknown",
            "backup_created": None,
            "fixes_applied": [],
            "stats": {}
        }
        
        # Check if file exists
        if not file_path.exists():
            result["status"] = "not_found"
            return result
        
        # Initial validation
        is_valid, message, stats = self.validate_json(file_path)
        
        if is_valid:
            result["status"] = "valid"
            result["stats"] = stats
            return result
        
        # File has errors, attempt to fix
        result["original_error"] = message
        
        # Create backup
        if not dry_run:
            backup_path = self.backup_file(file_path)
            result["backup_created"] = str(backup_path)
        
        # Read and attempt fixes
        content = file_path.read_text()
        fixed_content, fixes = self.fix_common_json_errors(content)
        result["fixes_applied"] = fixes
        
        # Try to parse fixed content
        try:
            data = json.loads(fixed_content)
            
            # Success! Save formatted JSON
            if not dry_run:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                result["status"] = "fixed"
                
                # Get new stats
                _, _, stats = self.validate_json(file_path)
                result["stats"] = stats
            else:
                result["status"] = "fixable"
            
        except json.JSONDecodeError as e:
            result["status"] = "unfixable"
            result["remaining_error"] = f"Line {e.lineno}, col {e.colno}: {e.msg}"
        
        return result
    
    def process_all_files(self, dry_run: bool = False) -> Dict[str, Any]:
        """Process all target JSON files."""
        target_files = [
            "data/sample_transcripts.json",
            "data/demo_aapl_data.json",
            "data/demo_content_posts.json",
            "data/demo_googl_data.json",
            "data/demo_msft_data.json",
            "data/demo_tsla_data.json",
            "data/demo_spy_data.json",
            "data/demo_sentiment_timeline.json",
            "data/demo_aapl_fundamentals.json"
        ]
        
        results = []
        summary = {
            "total": 0,
            "valid": 0,
            "fixed": 0,
            "unfixable": 0,
            "not_found": 0
        }
        
        for file_rel in target_files:
            file_path = self.base_dir / file_rel
            result = self.fix_json_file(file_path, dry_run=dry_run)
            results.append(result)
            
            summary["total"] += 1
            summary[result["status"]] = summary.get(result["status"], 0) + 1
        
        return {
            "summary": summary,
            "results": results
        }
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate detailed report."""
        report = []
        report.append("=" * 80)
        report.append("DATA QUALITY AGENT REPORT")
        report.append("=" * 80)
        report.append("")
        
        summary = results["summary"]
        report.append(f"📊 Summary:")
        report.append(f"  Total files: {summary['total']}")
        report.append(f"  ✅ Valid: {summary['valid']}")
        report.append(f"  🔧 Fixed: {summary['fixed']}")
        report.append(f"  ❌ Unfixable: {summary['unfixable']}")
        report.append(f"  ⚠️  Not found: {summary['not_found']}")
        report.append("")
        
        report.append("📋 Detailed Results:")
        report.append("")
        
        for result in results["results"]:
            status_icon = {
                "valid": "✅",
                "fixed": "🔧",
                "unfixable": "❌",
                "not_found": "⚠️",
                "fixable": "🔧"
            }.get(result["status"], "❓")
            
            report.append(f"{status_icon} {result['file']}")
            report.append(f"   Status: {result['status']}")
            
            if result.get("fixes_applied"):
                report.append("   Fixes applied:")
                for fix in result["fixes_applied"]:
                    report.append(f"     - {fix}")
            
            if result.get("backup_created"):
                report.append(f"   Backup: {result['backup_created']}")
            
            if result.get("stats"):
                stats = result["stats"]
                report.append(f"   Stats: {stats.get('size_kb', 0)}KB, {stats.get('type', 'unknown')} type")
            
            if result.get("remaining_error"):
                report.append(f"   ❌ Error: {result['remaining_error']}")
            
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Run data quality agent."""
    print("🤖 Data Quality Agent Starting...\n")
    
    agent = DataQualityAgent()
    
    # First do a dry run to see what would be fixed
    print("Phase 1: Analyzing files (dry run)...\n")
    dry_results = agent.process_all_files(dry_run=True)
    print(agent.generate_report(dry_results))
    
    # Ask for confirmation
    print("\nPhase 2: Apply fixes? (y/n): ", end="")
    response = input().strip().lower()
    
    if response == 'y':
        print("\nApplying fixes...\n")
        results = agent.process_all_files(dry_run=False)
        print(agent.generate_report(results))
        
        # Save report
        report_path = Path("ghl_real_estate_ai") / "DATA_QUALITY_REPORT.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(agent.generate_report(results))
        print(f"\n📄 Report saved to: {report_path}")
    else:
        print("\nNo changes made.")


if __name__ == "__main__":
    main()
