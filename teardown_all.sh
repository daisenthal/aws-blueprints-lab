#!/bin/bash
set -e
echo "🧹 Destroying all blueprints..."

FOLDERS=(
  "00_foundation"
  "01_ai_healthcheck_api"
)

for DIR in "${FOLDERS[@]}"; do
  if [ -d "$DIR" ]; then
    echo "🧨 Destroying stacks in: $DIR"
    cd "$DIR"
    cdk destroy --all --force --require-approval never || echo "⚠️  Failed in $DIR"
    cd ..
  fi
done

echo "✅ All teardown operations complete."
