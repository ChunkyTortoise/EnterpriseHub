#!/bin/bash
set -e

# PyPI Publishing Script for docqa-engine and insight-engine
# Requires: TWINE_USERNAME and TWINE_PASSWORD env vars (or use PyPI token)
#
# Usage:
#   export TWINE_USERNAME=__token__
#   export TWINE_PASSWORD=pypi-AgEIcH...
#   ./scripts/publish_pypi.sh

echo "==> Publishing packages to PyPI..."

# Verify environment variables
if [ -z "$TWINE_USERNAME" ] || [ -z "$TWINE_PASSWORD" ]; then
    echo "ERROR: TWINE_USERNAME and TWINE_PASSWORD must be set"
    echo "Example:"
    echo "  export TWINE_USERNAME=__token__"
    echo "  export TWINE_PASSWORD=pypi-your-token-here"
    exit 1
fi

# docqa-engine
echo ""
echo "==> Publishing docqa-engine..."
cd /Users/cave/Documents/GitHub/docqa-engine

# Clean and rebuild
rm -rf dist/ build/ *.egg-info
python3 -m build

# Verify with twine
twine check dist/*

# Upload to PyPI
twine upload dist/*

echo "✓ docqa-engine published successfully"

# insight-engine
echo ""
echo "==> Publishing insight-engine..."
cd /Users/cave/Documents/GitHub/insight-engine

# Clean and rebuild
rm -rf dist/ build/ *.egg-info
python3 -m build

# Verify with twine
twine check dist/*

# Upload to PyPI
twine upload dist/*

echo "✓ insight-engine published successfully"

echo ""
echo "==> All packages published to PyPI!"
echo "Verify at:"
echo "  - https://pypi.org/project/docqa-engine/"
echo "  - https://pypi.org/project/insight-engine/"
