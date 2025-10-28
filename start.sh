#!/bin/bash

# Quick start script for the Agno AI Service

echo "=========================================="
echo "  Agno AI Service - Quick Start"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_KEY"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after you've set your OPENAI_KEY in .env..."
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "  Starting Agno AI Service"
echo "=========================================="
echo ""

# Run the service
python main.py
