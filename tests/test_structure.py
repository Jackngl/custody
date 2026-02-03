import json
import os
from pathlib import Path

def test_manifest_structure():
    """Test that the manifest.json file is valid and has the correct domain."""
    manifest_path = Path("custom_components/custody_schedule/manifest.json")
    assert manifest_path.exists(), "manifest.json not found"
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    assert "domain" in manifest
    assert manifest["domain"] == "custody_schedule"
    assert "documentation" in manifest
    assert "iot_class" in manifest
