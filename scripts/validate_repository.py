"""Offline package checks; authoritative HACS/hassfest validation runs in CI."""

import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
component = ROOT / "custom_components/enbw_mobilityplus"
manifest = json.loads((component / "manifest.json").read_text())
hacs = json.loads((ROOT / "hacs.json").read_text())
assert manifest["domain"] == component.name
assert manifest["codeowners"] == ["@sluggyly1991"]
assert (
    manifest["documentation"] == "https://github.com/sluggyly1991/enbw-mobilityplus-homeassistant"
)
assert manifest["issue_tracker"] == manifest["documentation"] + "/issues"
assert hacs["homeassistant"] == "2026.3.0"
assert len(list((ROOT / "custom_components").iterdir())) == 1
for path in component.rglob("*.json"):
    json.loads(path.read_text())
for name, size in [("icon.png", 256), ("icon@2x.png", 512)]:
    content = (component / "brand" / name).read_bytes()
    assert content[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", content[16:24]) == (size, size)
print("Repository metadata, JSON and packaged brand assets OK")
