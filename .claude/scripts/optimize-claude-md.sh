#!/bin/bash
# CLAUDE.md Optimization Script v2.0.0
# Automated optimization with progressive disclosure

set -e

# Configuration
CLAUDE_FILE="CLAUDE.md"
REFERENCE_DIR=".claude/reference"
BACKUP_DIR=".claude/backups"
SCRIPTS_DIR=".claude/scripts"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create directories
mkdir -p "$REFERENCE_DIR" "$BACKUP_DIR"

backup_current_state() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/claude_${TIMESTAMP}"

    echo "Creating backup: $BACKUP_PATH"
    cp "$CLAUDE_FILE" "${BACKUP_PATH}.md"

    if [[ -d "$REFERENCE_DIR" ]]; then
        cp -r "$REFERENCE_DIR" "${BACKUP_PATH}_references"
    fi

    echo -e "${GREEN}✅ Backup created${NC}"
}

check_optimization_needed() {
    FILE_SIZE=$(wc -c < "$CLAUDE_FILE")

    if [[ $FILE_SIZE -lt 35000 ]]; then
        echo -e "${GREEN}✅ File size optimal ($FILE_SIZE chars) - no optimization needed${NC}"
        return 1
    fi

    echo -e "${YELLOW}⚠️  File size ($FILE_SIZE chars) - optimization recommended${NC}"
    return 0
}

extract_large_sections() {
    echo "Analyzing sections for extraction opportunities..."

    # Create extraction candidates report
    awk '
    /^##/ {
        if (section && chars > 1500) {
            print section ": " chars " chars"
        }
        section = $0
        chars = 0
    }
    {
        chars += length($0)
    }
    END {
        if (section && chars > 1500) {
            print section ": " chars " chars"
        }
    }' "$CLAUDE_FILE" > /tmp/extraction_candidates.txt

    if [[ -s /tmp/extraction_candidates.txt ]]; then
        echo "Large sections found:"
        cat /tmp/extraction_candidates.txt
        echo ""
        echo "Consider extracting these to reference files."
    else
        echo "No large sections requiring extraction found."
    fi
}

validate_references() {
    echo "Validating existing references..."

    BROKEN_REFS=0

    while IFS= read -r ref; do
        if [[ -n "$ref" ]]; then
            file_path=".claude/${ref#@}"
            if [[ ! -f "$file_path" ]]; then
                echo -e "${RED}❌ Missing: $ref${NC}"
                BROKEN_REFS=$((BROKEN_REFS + 1))
            fi
        fi
    done < <(grep -o "@reference/[^)]*" "$CLAUDE_FILE" 2>/dev/null || true)

    if [[ $BROKEN_REFS -eq 0 ]]; then
        echo -e "${GREEN}✅ All references valid${NC}"
    else
        echo -e "${RED}❌ Found $BROKEN_REFS broken references${NC}"
        return 1
    fi
}

generate_optimization_report() {
    echo ""
    echo "=== OPTIMIZATION REPORT ==="
    echo "Timestamp: $(date)"
    echo ""

    # File metrics
    FILE_SIZE=$(wc -c < "$CLAUDE_FILE")
    REFERENCE_COUNT=$(grep -o "@reference/" "$CLAUDE_FILE" | wc -l || echo "0")
    SECTION_COUNT=$(grep -c "^##" "$CLAUDE_FILE" || echo "1")

    echo "Current Metrics:"
    echo "  File size: $FILE_SIZE characters"
    echo "  Reference links: $REFERENCE_COUNT"
    echo "  Sections: $SECTION_COUNT"

    if [[ $SECTION_COUNT -gt 0 ]]; then
        DISCLOSURE_RATIO=$(echo "scale=1; $REFERENCE_COUNT * 100 / $SECTION_COUNT" | bc -l 2>/dev/null || echo "0")
        echo "  Progressive disclosure: ${DISCLOSURE_RATIO}%"
    fi

    echo ""

    # Performance analysis
    if [[ $FILE_SIZE -gt 40000 ]]; then
        echo -e "${RED}🚨 CRITICAL: Exceeds 40k threshold${NC}"
    elif [[ $FILE_SIZE -gt 35000 ]]; then
        echo -e "${YELLOW}⚠️  WARNING: Approaching threshold${NC}"
    else
        echo -e "${GREEN}✅ OPTIMAL: Size within limits${NC}"
    fi
}

create_quick_reference() {
    local quick_ref_file="$REFERENCE_DIR/quick-reference.md"

    echo "Creating quick reference guide..."

    cat > "$quick_ref_file" << 'EOF'
# Quick Reference Guide

## Common Tasks

| I need to... | Trigger | Reference |
|-------------|---------|-----------|
| Add tests | "implement TDD" | @reference/tdd-implementation-guide.md |
| Debug issues | "systematic debug" | @reference/debugging-guide.md |
| Secure code | "security review" | @reference/security-implementation-guide.md |
| Design UI | "frontend design" | @reference/frontend-patterns.md |
| Deploy app | "deploy production" | @reference/deployment-guide.md |

## Quick Commands

```bash
# Performance monitoring
./.claude/scripts/validate-performance.sh --report

# Optimization check
./.claude/scripts/optimize-claude-md.sh --dry-run

# Reference validation
./.claude/scripts/validate-references.sh
```

## Progressive Disclosure

- **Main file**: Core principles and quick references only
- **Reference files**: Detailed implementation guides
- **Skills**: Automated workflows and patterns
- **Scripts**: Automation and monitoring tools
EOF

    echo -e "${GREEN}✅ Quick reference created${NC}"
}

main() {
    echo "=== CLAUDE.md Optimization Script ==="
    echo ""

    # Parse arguments
    DRY_RUN=false
    FORCE=false
    REPORT_ONLY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --report)
                REPORT_ONLY=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --dry-run    Analyze without making changes"
                echo "  --force      Proceed without confirmation"
                echo "  --report     Generate optimization report only"
                echo "  --help       Show this help"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Check if file exists
    if [[ ! -f "$CLAUDE_FILE" ]]; then
        echo -e "${RED}❌ ERROR: $CLAUDE_FILE not found${NC}"
        exit 1
    fi

    # Generate report
    if [[ "$REPORT_ONLY" == true ]]; then
        generate_optimization_report
        extract_large_sections
        validate_references
        exit 0
    fi

    # Check if optimization needed
    if ! check_optimization_needed && [[ "$FORCE" != true ]]; then
        exit 0
    fi

    # Dry run mode
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${BLUE}🔍 DRY RUN MODE - No changes will be made${NC}"
        echo ""
        generate_optimization_report
        extract_large_sections
        validate_references
        exit 0
    fi

    # Confirmation
    if [[ "$FORCE" != true ]]; then
        echo -n "Proceed with optimization? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Optimization cancelled"
            exit 0
        fi
    fi

    # Perform optimization
    backup_current_state
    create_quick_reference
    validate_references
    generate_optimization_report

    echo ""
    echo -e "${GREEN}✅ Optimization complete${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./.claude/scripts/validate-performance.sh --report"
    echo "  2. Test the optimized system"
    echo "  3. Review reference files in $REFERENCE_DIR"
}

# Execute main function
main "$@"