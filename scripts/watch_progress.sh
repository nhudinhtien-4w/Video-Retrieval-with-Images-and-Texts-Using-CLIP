#!/bin/bash
# Monitor BEIT3 extraction progress in real-time

# Get latest log file
LATEST_LOG=$(ls -t logs/beit3_extract_*.log 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "❌ No log file found!"
    exit 1
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           BEIT3 EXTRACTION - REAL-TIME MONITOR              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Watching: $LATEST_LOG"
echo ""
echo "🔄 Real-time progress (Ctrl+C to exit):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Follow log with grep to show only important lines
tail -f "$LATEST_LOG" | grep --line-buffered -E "Progress:|loaded|Starting|completed|saved|ERROR|WARNING"
