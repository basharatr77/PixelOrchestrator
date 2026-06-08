#!/bin/bash

echo "🧠 PixelOrchestrator Analysis Running..."

echo "📁 Git Status:"
git status

echo ""
echo "📊 Change Summary:"
git diff --stat

echo ""
echo "🔥 Top Modified Files:"
git diff --name-only | head -20

echo ""
echo "💾 Repo Size Check:"
du -sh .

echo ""
echo "⚡ Done."
