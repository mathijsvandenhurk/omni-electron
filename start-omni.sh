#!/bin/bash

# Omni Clean Start Script
echo "🛑 Stopping existing processes..."
pkill -f electron 2>/dev/null || true
pkill -f vite 2>/dev/null || true
pkill -f concurrently 2>/dev/null || true
sleep 1

echo "🧹 Cleaning Python cache..."
rm -rf backend/__pycache__ backend/*/__pycache__ 2>/dev/null

echo "🚀 Starting Omni..."
npm run dev
