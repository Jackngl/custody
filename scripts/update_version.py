#!/usr/bin/env python3
"""Update the integration version inside manifest.json and README.md badge."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "custom_components" / "custody_schedule" / "manifest.json"
README_PATH = PROJECT_ROOT / "README.md"


def increment_version(version: str) -> str:
    """Increment the patch version (1.0.x + 1)."""
    # Match version pattern like "1.0.5"
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}. Expected format: X.Y.Z")

    major, minor, patch = map(int, match.groups())
    new_patch = patch + 1
    return f"{major}.{minor}.{new_patch}"


def get_current_version() -> str:
    """Read the current version from manifest.json."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"manifest not found at {MANIFEST_PATH}")

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise RuntimeError(f"Failed to load manifest: {err}") from err

    version = manifest.get("version")
    if not version:
        raise ValueError("Version field not found in manifest")

    return version


def update_version(version: str) -> None:
    """Replace the manifest version field with the provided value and update README badge."""
    if not MANIFEST_PATH.exists():
        print(f"manifest not found at {MANIFEST_PATH}")
        sys.exit(1)

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        print(f"Failed to load manifest: {err}")
        sys.exit(1)

    old_version = manifest.get("version", "unknown")
    manifest["version"] = version

    try:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as err:
        print(f"Failed to write manifest: {err}")
        sys.exit(1)

    print(f"Version updated in manifest.json: {old_version} -> {version}")

    # Update README.md badge
    if README_PATH.exists():
        try:
            readme_content = README_PATH.read_text(encoding="utf-8")
            # Pattern to match the version badge: ![Version](https://img.shields.io/badge/version-X.Y.Z-blue.svg)
            pattern = r"!\[Version\]\(https://img\.shields\.io/badge/version-[\d.]+-blue\.svg\)"
            replacement = f"![Version](https://img.shields.io/badge/version-{version}-blue.svg)"
            new_content = re.sub(pattern, replacement, readme_content)

            if new_content != readme_content:
                README_PATH.write_text(new_content, encoding="utf-8")
                print(f"Version badge updated in README.md: {old_version} -> {version}")
            else:
                print("Warning: Version badge pattern not found in README.md")
        except OSError as err:
            print(f"Warning: Failed to update README.md: {err}")
    else:
        print("Warning: README.md not found, skipping badge update")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Auto-increment mode
        try:
            current_version = get_current_version()
            new_version = increment_version(current_version)
            update_version(new_version)
        except (FileNotFoundError, ValueError, RuntimeError) as err:
            print(f"Error: {err}")
            sys.exit(1)
    elif len(sys.argv) == 2:
        # Manual version mode
        update_version(sys.argv[1])
    else:
        print("Usage:")
        print("  python scripts/update_version.py          # Auto-increment version (1.0.x + 1)")
        print("  python scripts/update_version.py <version>  # Set specific version")
        sys.exit(1)
