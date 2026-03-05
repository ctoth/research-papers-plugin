#!/bin/bash
# Generate papers/AGENTS.md from all description.md files
# Run from project root: bash scripts/generate-paper-agents-md.sh

{
  echo "# Paper References"
  echo ""
  echo "Quick reference for papers in this collection."
  echo ""
  echo "## How to Read Papers"
  echo ""
  echo "Each paper folder contains:"
  echo "- **notes.md** - Implementation-focused notes extracted from the paper (START HERE)"
  echo "- **description.md** - Brief summary of the paper's contribution"
  echo "- **paper.pdf** or similar - The original PDF"
  echo "- **pngs/** - Page images for large PDFs (use when PDF is too large to read directly)"
  echo "- **chunks/** - Text chunks for very large papers"
  echo ""
  echo "**For implementation work**: Always read notes.md first - it contains the specific values, formulas, and parameters you need."
  echo ""
  echo "**For large PDFs**: Use the pngs/ folder. ImageMagick is installed for PDF-to-image conversion if needed."
  echo ""
  echo "---"
  echo ""
  for d in papers/*/; do
    name=$(basename "$d")
    if [ -f "$d/description.md" ] && [ "$name" != "pages" ]; then
      echo "## $name"
      cat "$d/description.md"
      echo ""
    fi
  done
} > papers/AGENTS.md

echo "Generated papers/AGENTS.md with $(grep -c '^## ' papers/AGENTS.md) paper entries"
