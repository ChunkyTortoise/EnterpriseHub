#!/bin/bash

# Jorge's Seller Bot - Quick Development Setup Script
# Run this script to set up the development environment for Jorge's seller bot

echo "🚀 Setting up Jorge's Seller Bot Development Environment..."

# Create directory structure for new Jorge components
echo "📁 Creating directory structure..."
mkdir -p ghl_real_estate_ai/services/jorge
mkdir -p ghl_real_estate_ai/schemas
mkdir -p tests/jorge_seller
mkdir -p ghl_real_estate_ai/ghl_utils

echo "✅ Directory structure created"

# Create empty files for Jorge's components
echo "📝 Creating component files..."

# Jorge Seller Engine (main logic)
touch ghl_real_estate_ai/services/jorge/jorge_seller_engine.py

# Confrontational Tone Engine
touch ghl_real_estate_ai/services/jorge/jorge_tone_engine.py

# Follow-up Automation Engine
touch ghl_real_estate_ai/services/jorge/jorge_followup_engine.py

# Seller Data Schema
touch ghl_real_estate_ai/schemas/seller_data.py

# Jorge Configuration
touch ghl_real_estate_ai/ghl_utils/jorge_config.py

# Test files
touch tests/jorge_seller/test_seller_engine.py
touch tests/jorge_seller/test_temperature_classifier.py
touch tests/jorge_seller/test_tone_engine.py
touch tests/jorge_seller/test_followup_engine.py
touch tests/jorge_seller/test_data_extraction.py

echo "✅ Component files created"

# Copy existing environment file for Jorge modifications
if [ -f ".env.example" ]; then
    cp .env.example .env.jorge
    echo "✅ Created .env.jorge from .env.example"
fi

echo ""
echo "🎯 Jorge's Seller Bot Development Environment Ready!"
echo ""
echo "Next steps:"
echo "1. Review the complete specification: JORGE_SELLER_BOT_REFERENCE.md"
echo "2. Start with Phase 1: Foundation Adaptation (4 hours)"
echo "3. Key files to modify first:"
echo "   - ghl_real_estate_ai/prompts/system_prompts.py (lines 27-35)"
echo "   - ghl_real_estate_ai/services/lead_scorer.py (adapt for 4 questions)"
echo "   - ghl_real_estate_ai/api/routes/webhook.py (add Jorge mode detection)"
echo ""
echo "📋 Development phases:"
echo "   Phase 1: Foundation Adaptation (4h) - Basic question flow"
echo "   Phase 2: Temperature Classification (3h) - Hot/Warm/Cold logic"
echo "   Phase 3: Confrontational Tone (4h) - Direct messaging style"
echo "   Phase 4: Follow-up Automation (5h) - 2-3 day → 14 day sequences"
echo "   Phase 5: Testing & Integration (4h) - End-to-end validation"
echo ""
echo "🔧 Key configuration needed:"
echo "   - Set JORGE_SELLER_MODE=true in environment"
echo "   - Configure GHL workflow IDs for agent handoff"
echo "   - Set up Hot-Seller, Warm-Seller, Cold-Seller tags"
echo ""
echo "📊 Success criteria:"
echo "   - All 4 questions work in sequence"
echo "   - Confrontational tone (direct, no emojis, no hyphens)"
echo "   - SMS under 160 characters"
echo "   - Hot leads trigger agent notification"
echo "   - Proper follow-up timing (2-3d → 14d)"
echo ""
echo "Happy coding! 🎉"