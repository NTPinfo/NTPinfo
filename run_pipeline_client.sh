#!/bin/bash
set -e  # Stop on error

echo "📁 Navigating to client directory..."
cd client

echo "📦 Installing dependencies..."
npm install

echo "✅ Running TypeScript type checking..."
npx tsc -b

echo "🔍 Running ESLint (lint)..."
npm run lint

echo "🧪 Running tests with coverage..."
npm run test

echo "🎉 All client stages passed."

