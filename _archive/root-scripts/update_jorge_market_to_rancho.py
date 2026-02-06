#!/usr/bin/env python3
"""
Jorge Market Update Script: Rancho Cucamonga CA → Rancho Cucamonga CA

This script comprehensively updates the Jorge bot ecosystem from Rancho Cucamonga, CA
market focus to Rancho Cucamonga, CA market focus. Updates include:

1. Market location and geography
2. Price ranges (CA → CA)
3. Regulatory compliance (DRE → DRE)
4. Neighborhood references
5. Local market expertise
6. Compliance messaging

Author: Claude Code Assistant
Created: 2026-01-25
Purpose: Market transition from Rancho Cucamonga CA to Rancho Cucamonga CA
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple


class JorgeMarketUpdater:
    """Updates Jorge bot files from Rancho Cucamonga CA to Rancho Cucamonga CA"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.updated_files = []
        self.transformation_log = []

    # ========== TRANSFORMATION MAPPINGS ==========

    MARKET_TRANSFORMATIONS = {
        # Geographic updates
        "rancho_cucamonga": "rancho_cucamonga",
        "Rancho Cucamonga": "Rancho Cucamonga",
        "RANCHO_CUCAMONGA": "RANCHO_CUCAMONGA",
        "california": "california",
        "California": "California",
        "CALIFORNIA": "CALIFORNIA",
        "CA": "CA",
        " ca": " ca",

        # Regulatory updates
        "DRE": "DRE",
        "California Real Estate Commission": "California Department of Real Estate",
        "California Real Estate": "California Real Estate",

        # Price range updates (CA → CA market)
        "700000": "700000",  # Entry level min
        "700000": "700000",  # Entry level max → mid level min
        "1200000": "1200000", # Mid level max → luxury min
        "$700k": "$700k",
        "$700k": "$700k",
        "$1.2M": "$1.2M",
        "700k": "700k",
        "700k": "700k",

        # Neighborhood updates
        "Central RC": "Central RC",
        "central_rc": "central_rc",
        "Alta Loma": "Alta Loma",
        "alta_loma": "alta_loma",
        "alta_loma": "alta_loma",
        "Etiwanda": "Etiwanda",
        "etiwanda": "etiwanda",
        "Victoria Gardens": "Victoria Gardens",
        "victoria_gardens": "victoria_gardens",
        "Day Creek": "Day Creek",
        "day_creek": "day_creek",

        # Market-specific updates
        "Family-oriented suburban growth": "Family-oriented suburban growth",
        "families and logistics professionals": "families and logistics professionals",
        "moderate inventory levels": "moderate inventory levels",
        "stable appreciation trends": "stable appreciation trends",
    }

    NEIGHBORHOOD_MAPPING = {
        # Rancho Cucamonga → Rancho Cucamonga neighborhoods
        "alta_loma": "alta_loma",
        "tarrytown": "terra_vista",
        "zilker": "central_rc",
        "central_rc": "central_rc",
        "south_congress": "victoria_gardens",
        "east_rancho_cucamonga": "etiwanda",
        "etiwanda": "etiwanda",
        "victoria_gardens": "victoria_gardens",
        "day_creek": "day_creek",
        "central_rancho_cucamonga": "central_rc"
    }

    def update_all_jorge_files(self):
        """Update all Jorge-related files in the project"""
        print("🚀 Starting Jorge Market Update: Rancho Cucamonga CA → Rancho Cucamonga CA")
        print("=" * 60)

        # Find all Jorge-related files
        jorge_files = self._find_jorge_files()
        print(f"📁 Found {len(jorge_files)} Jorge-related files to update")

        # Update each file
        for file_path in jorge_files:
            try:
                self._update_file(file_path)
            except Exception as e:
                print(f"❌ Error updating {file_path}: {e}")

        # Update configuration files
        self._update_claude_md()

        # Generate summary
        self._generate_update_summary()

    def _find_jorge_files(self) -> List[Path]:
        """Find all Jorge-related files"""
        patterns = [
            "**/jorge*.py",
            "**/jorge*.md",
            "**/jorge*.json",
            "**/jorge*.sql",
            "**/*jorge*",
            "**/agents/*.py",
            "**/services/jorge/*.py",
            "**/streamlit_demo/*jorge*.py",
            "**/api/**/*jorge*.py"
        ]

        files = set()
        for pattern in patterns:
            files.update(self.base_path.rglob(pattern))

        # Filter to actual files only
        return [f for f in files if f.is_file() and not f.name.startswith('.')]

    def _update_file(self, file_path: Path):
        """Update a single file with market transformations"""
        if not file_path.exists():
            return

        print(f"📝 Updating: {file_path.relative_to(self.base_path)}")

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            original_content = content
        except Exception as e:
            print(f"⚠️  Could not read {file_path}: {e}")
            return

        # Apply transformations
        changes_made = []

        # 1. Market location transformations
        for old_term, new_term in self.MARKET_TRANSFORMATIONS.items():
            if old_term in content:
                content = content.replace(old_term, new_term)
                changes_made.append(f"{old_term} → {new_term}")

        # 2. Neighborhood function updates
        content = self._update_neighborhood_functions(content)

        # 3. Price validation updates
        content = self._update_price_validations(content)

        # 4. Comment and documentation updates
        content = self._update_comments_and_docs(content)

        # Write updated content if changes were made
        if content != original_content:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.updated_files.append(str(file_path))
                self.transformation_log.append({
                    "file": str(file_path.relative_to(self.base_path)),
                    "changes": changes_made
                })
                print(f"✅ Updated: {len(changes_made)} transformations applied")
            except Exception as e:
                print(f"❌ Could not write {file_path}: {e}")
        else:
            print(f"ℹ️  No changes needed")

    def _update_neighborhood_functions(self, content: str) -> str:
        """Update neighborhood detection functions"""

        # Update Rancho Cucamonga neighborhood detection
        rancho_cucamonga_detection_pattern = r'def _detect_rancho_cucamonga_neighborhood\(.*?\):(.*?)return "central_rancho_cucamonga"'
        rancho_replacement = '''def _detect_rancho_neighborhood(self, address: Optional[str]) -> Optional[str]:
        """Extract Rancho Cucamonga neighborhood from address for market-specific skills."""
        if not address:
            return None

        rancho_neighborhoods = {
            "alta_loma": ["alta loma", "alta_loma", "91737"],
            "central_rc": ["central", "baseline", "foothill", "91730"],
            "etiwanda": ["etiwanda", "91739"],
            "victoria_gardens": ["victoria", "gardens", "town square"],
            "terra_vista": ["terra vista", "terra_vista"],
            "day_creek": ["day creek", "day_creek"],
            "north_rc": ["north rancho", "highland"],
            "south_rc": ["south rancho", "arrow route"]
        }

        address_lower = address.lower()
        for neighborhood, keywords in rancho_neighborhoods.items():
            if any(keyword in address_lower for keyword in keywords):
                return neighborhood

        return "central_rc"  # Default for Rancho Cucamonga addresses'''

        content = re.sub(rancho_cucamonga_detection_pattern, rancho_replacement, content, flags=re.DOTALL)

        # Update property detection function
        rancho_cucamonga_property_pattern = r'def _is_rancho_cucamonga_property\(.*?\):(.*?)return any\(\[(.*?)\]\)'
        rancho_property_replacement = '''def _is_rancho_property(self, address: Optional[str]) -> bool:
        """Detect if property is in Rancho Cucamonga market for progressive skills enhancement."""
        if not address:
            return False
        address_lower = address.lower()
        return any([
            "rancho cucamonga" in address_lower,
            "ca 917" in address_lower,  # Rancho Cucamonga zip codes
            " rc " in address_lower,
            "rancho cucamonga, ca" in address_lower,
            "inland empire" in address_lower
        ])'''

        content = re.sub(rancho_cucamonga_property_pattern, rancho_property_replacement, content, flags=re.DOTALL)

        return content

    def _update_price_validations(self, content: str) -> str:
        """Update price validation ranges for California market"""

        # Update price range definitions
        price_patterns = [
            (r'"entry_level".*"min":\s*700000', '"entry_level": {"min": 700000'),
            (r'"entry_level".*"max":\s*700000', '"entry_level": {"max": 700000'),
            (r'"mid_market".*"min":\s*700000', '"mid_market": {"min": 700000'),
            (r'"mid_market".*"max":\s*1200000', '"mid_market": {"max": 1200000'),
            (r'"luxury".*"min":\s*1200000', '"luxury": {"min": 1200000'),
        ]

        for pattern, replacement in price_patterns:
            content = re.sub(pattern, replacement, content)

        return content

    def _update_comments_and_docs(self, content: str) -> str:
        """Update comments and documentation strings"""

        # Update comment references
        comment_updates = [
            ("# Default to Rancho Cucamonga market", "# Default to Rancho Cucamonga market"),
            ("# Rancho Cucamonga market context", "# Rancho Cucamonga market context"),
            ("Enhanced discovery context with Rancho Cucamonga market intelligence",
             "Enhanced discovery context with Rancho Cucamonga market intelligence"),
            ("Rancho Cucamonga market context injection", "Rancho Cucamonga market context injection"),
            ("Extract Rancho Cucamonga neighborhood", "Extract Rancho Cucamonga neighborhood"),
            ("Rancho Cucamonga market for progressive", "Rancho Cucamonga market for progressive"),
            ("Rancho Cucamonga addresses", "Rancho Cucamonga addresses")
        ]

        for old_comment, new_comment in comment_updates:
            content = content.replace(old_comment, new_comment)

        return content

    def _update_claude_md(self):
        """Update the main CLAUDE.md project documentation"""
        claude_md_path = self.base_path / "CLAUDE.md"

        if not claude_md_path.exists():
            print("⚠️  CLAUDE.md not found, skipping documentation update")
            return

        print("📝 Updating project documentation (CLAUDE.md)")

        with open(claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update Rancho Cucamonga Market Specifics section
        rancho_cucamonga_section = '''### Rancho Cucamonga Market Specifics
- **Price Ranges**: Entry-level $300-700k, Mid-market $700k-1M, Luxury $1.2M+
- **Key Areas**: Central RC, Alta Loma, Etiwanda, Victoria Gardens, Day Creek
- **Market Dynamics**: Family-oriented suburban growth, moderate inventory levels, stable appreciation trends
- **Buyer Personas**: Tech professionals, families relocating, investors'''

        rancho_section = '''### Rancho Cucamonga Market Specifics
- **Price Ranges**: Entry-level $500-700k, Mid-market $700k-1.2M, Luxury $1.2M+
- **Key Areas**: Alta Loma, Central RC, Etiwanda, Victoria Gardens, Terra Vista
- **Market Dynamics**: Family-oriented growth, stable appreciation, good schools
- **Buyer Personas**: Families, young professionals, Orange County relocators, retirees'''

        content = content.replace(rancho_cucamonga_section, rancho_section)

        # Update regulatory section
        content = content.replace("**DRE**: California Real Estate Commission regulations",
                                "**DRE**: California Department of Real Estate regulations")

        with open(claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Updated project documentation")

    def _generate_update_summary(self):
        """Generate summary of all updates made"""
        print("\n" + "=" * 60)
        print("🎯 JORGE MARKET UPDATE COMPLETE")
        print("=" * 60)
        print(f"📊 Summary:")
        print(f"   • Files Updated: {len(self.updated_files)}")
        print(f"   • Total Transformations: {sum(len(log['changes']) for log in self.transformation_log)}")
        print(f"   • Market: Rancho Cucamonga CA → Rancho Cucamonga CA")
        print(f"   • Regulatory: DRE → California DRE")
        print(f"   • Price Ranges: Updated for California market")

        print(f"\n📁 Updated Files:")
        for file_path in self.updated_files[:10]:  # Show first 10
            print(f"   ✅ {Path(file_path).name}")
        if len(self.updated_files) > 10:
            print(f"   ... and {len(self.updated_files) - 10} more files")

        print(f"\n🔧 Key Transformations:")
        print(f"   • rancho_cucamonga → rancho_cucamonga")
        print(f"   • Rancho Cucamonga → Rancho Cucamonga")
        print(f"   • CA → CA")
        print(f"   • DRE → DRE")
        print(f"   • $700k-700k → $700k-700k (entry level)")
        print(f"   • $700k-1M → $700k-1.2M (mid market)")
        print(f"   • Alta Loma → Alta Loma")
        print(f"   • Etiwanda → Etiwanda")
        print(f"   • Victoria Gardens → Victoria Gardens")

        # Write detailed log
        log_path = self.base_path / "jorge_market_update_log.json"
        with open(log_path, 'w') as f:
            json.dump({
                "update_date": "2026-01-25",
                "market_transition": "Rancho Cucamonga CA → Rancho Cucamonga CA",
                "files_updated": self.updated_files,
                "transformation_log": self.transformation_log,
                "summary": {
                    "total_files": len(self.updated_files),
                    "total_transformations": sum(len(log['changes']) for log in self.transformation_log)
                }
            }, f, indent=2)

        print(f"\n📄 Detailed log saved: {log_path}")
        print("\n✅ Jorge is now configured for Rancho Cucamonga, California market!")


def main():
    """Run the Jorge market update"""
    # Get the project root directory
    script_path = Path(__file__).parent
    project_root = script_path

    # Initialize updater
    updater = JorgeMarketUpdater(project_root)

    # Run the update
    updater.update_all_jorge_files()


if __name__ == "__main__":
    main()