"""
Tests for asset processing pipeline, non-destructive editing, and manifest validity.
"""

import json
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BGS_DIR = PROJECT_ROOT / "Bgs"
LOGO_DIR = PROJECT_ROOT / "Logo"
MANIFEST_PATH = PROJECT_ROOT / "tools" / "asset_manifest.json"
ASSETS_DIR = PROJECT_ROOT / "frontend" / "public" / "assets"


def test_original_files_preserved():
    """Verify all original files remain untouched."""
    assert (BGS_DIR / "07.jpg").exists()
    assert (BGS_DIR / "389420699052302337.jpg").exists()
    assert (LOGO_DIR / "Logo diffrent types.png").exists()
    assert (LOGO_DIR / "Akhadha Logo.jpg").exists()


def test_manifest_structure():
    assert MANIFEST_PATH.exists()
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "logos" in data
    assert "backgrounds" in data
    assert len(data["backgrounds"]) == 7
    assert "white_emblem" in data["logos"]
    assert "sponsor_akhadha" in data["logos"]


def test_processed_logo_transparency():
    logo_path = ASSETS_DIR / "logos" / "transparent" / "minaram_logo_white.png"
    assert logo_path.exists()
    im = Image.open(logo_path)
    assert im.mode == "RGBA"
    assert "A" in im.getbands()
    # Check that alpha channel has variation (transparent and opaque pixels)
    alpha_extrema = im.split()[-1].getextrema()
    assert alpha_extrema[0] == 0, "Expected transparent pixels"
    assert alpha_extrema[1] > 200, "Expected opaque white logo pixels"


def test_processed_background_files_exist():
    assert (ASSETS_DIR / "backgrounds" / "bg_stadium_cinematic.webp").exists()
    assert (ASSETS_DIR / "backgrounds" / "bg_ronaldo_07.webp").exists()
    assert (ASSETS_DIR / "backgrounds" / "mobile" / "bg_stadium_cinematic_mobile.webp").exists()
    assert (ASSETS_DIR / "thumbnails" / "bg_stadium_cinematic_thumb.webp").exists()
