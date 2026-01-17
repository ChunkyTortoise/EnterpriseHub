#!/usr/bin/env python3
"""
Test installation and configuration of Perplexity MCP Server
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass


async def test_environment():
    """Test environment configuration"""
    print("=" * 60)
    print("PERPLEXITY MCP SERVER - INSTALLATION TEST")
    print("=" * 60)
    print()

    # Check API key
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ PERPLEXITY_API_KEY not found in environment")
        print("   Please set in .env file:")
        print("   PERPLEXITY_API_KEY=your-key-here")
        return False

    # Mask the key for display
    masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
    print(f"✅ API Key found: {masked_key}")
    print()

    return True


async def test_dependencies():
    """Test required dependencies"""
    print("Checking dependencies...")
    print()

    required = {
        "httpx": "HTTP client for Perplexity API",
        "mcp": "Model Context Protocol SDK"
    }

    all_installed = True

    for package, description in required.items():
        try:
            __import__(package)
            print(f"✅ {package:20} - {description}")
        except ImportError:
            print(f"❌ {package:20} - NOT INSTALLED")
            all_installed = False

    print()

    if not all_installed:
        print("Install missing dependencies:")
        print("pip install -r .claude/mcp-servers/perplexity/requirements.txt")
        print()

    return all_installed


async def test_server_import():
    """Test server module import"""
    print("Testing server import...")
    print()

    try:
        # Change to server directory for import
        server_dir = os.path.dirname(__file__)
        sys.path.insert(0, server_dir)

        from server import PerplexityMCPServer

        print("✅ Server module imported successfully")
        print()
        return True

    except Exception as e:
        print(f"❌ Failed to import server: {e}")
        print()
        return False


async def test_basic_search():
    """Test basic search functionality"""
    print("Testing basic search...")
    print()

    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("⏭️  Skipping (no API key)")
        print()
        return True

    try:
        from server import PerplexityMCPServer

        server = PerplexityMCPServer()

        # Simple test query
        result = await server.search(
            query="What is 2+2?",
            max_tokens=100
        )

        if result.get("status") == "success":
            print("✅ Search successful")
            print(f"   Answer: {result['answer'][:100]}...")
            print(f"   Citations: {len(result.get('citations', []))}")
            print()
            return True
        else:
            print(f"❌ Search failed: {result.get('error')}")
            print()
            return False

    except Exception as e:
        print(f"❌ Search test failed: {e}")
        print()
        return False


async def main():
    """Run all tests"""
    print()

    results = []

    # Test 1: Environment
    results.append(await test_environment())

    # Test 2: Dependencies
    results.append(await test_dependencies())

    # Test 3: Server Import
    results.append(await test_server_import())

    # Test 4: Basic Search (optional)
    if all(results):
        results.append(await test_basic_search())

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if all(results):
        print("✅ All tests passed!")
        print()
        print("Perplexity MCP Server is ready to use.")
        print()
        print("Next steps:")
        print("1. Restart Claude Code to load the MCP server")
        print("2. Switch to 'research' profile to use Perplexity")
        print("3. Try: 'Search Perplexity for Python 3.13 features'")
    else:
        print("❌ Some tests failed")
        print()
        print("Please fix the issues above and run again:")
        print("python .claude/mcp-servers/perplexity/test_installation.py")

    print()


if __name__ == "__main__":
    asyncio.run(main())
