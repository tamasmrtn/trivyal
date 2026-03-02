#!/usr/bin/env bash
# Usage: ./scripts/bump-version.sh 0.2.0   (v prefix is stripped if present)
set -euo pipefail

NEW_VERSION="${1:?Usage: bump-version.sh <version>}"
NEW_VERSION="${NEW_VERSION#v}"  # strip leading v if present
OLD_VERSION=$(grep -m1 '^version = ' hub/pyproject.toml | sed 's/version = "\(.*\)"/\1/')

echo "Bumping $OLD_VERSION → $NEW_VERSION"

# Python services
sed -i "s/^version = \"$OLD_VERSION\"/version = \"$NEW_VERSION\"/" hub/pyproject.toml
sed -i "s/^version = \"$OLD_VERSION\"/version = \"$NEW_VERSION\"/" agent/pyproject.toml
sed -i "s/^version = \"$OLD_VERSION\"/version = \"$NEW_VERSION\"/" integration/pyproject.toml

# UI
cd ui && npm version "$NEW_VERSION" --no-git-tag-version && cd ..

echo "Done. Verify with: grep -r '$NEW_VERSION' hub/pyproject.toml agent/pyproject.toml ui/package.json integration/pyproject.toml"
