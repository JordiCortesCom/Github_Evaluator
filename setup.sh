#!/bin/bash

# Setup script for GitHub Evaluator
# Installs dependencies and creates necessary directories

echo "🔧 GitHub Evaluator Setup"
echo "=========================="

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python $(python3 --version) found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p reports
mkdir -p config

echo "✓ Directories created"

# Check for GitHub token
echo ""
echo "🔑 GitHub Token Setup"
echo "-------------------"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN environment variable not set"
    echo ""
    echo "To use this tool, you need to:"
    echo "1. Go to https://github.com/settings/tokens"
    echo "2. Create a Personal Access Token"
    echo "3. Grant 'repo:public_repo' and 'read:org' permissions"
    echo "4. Set the token: export GITHUB_TOKEN=ghp_xxxxx"
else
    echo "✓ GITHUB_TOKEN is set"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure: Edit config/default_config.yaml"
echo "2. Set token: export GITHUB_TOKEN=<your_token>"
echo "3. Run: python main.py --org <organization> --pattern <pattern>"
echo ""
echo "For more info, see README.md"
