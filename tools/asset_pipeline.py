"""
MINARAM CUP — Asset Processing & Enhancement Pipeline
Performs image quality auditing, non-destructive enhancement, background removal
for logos, responsive web variant generation, and manifest logging.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import cv2

# Set UTF-8 encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("asset_pipeline")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BGS_DIR = PROJECT_ROOT / "Bgs"
LOGO_DIR = PROJECT_ROOT / "Logo"

OUT_ASSETS = PROJECT_ROOT / "frontend" / "public" / "assets"
OUT_BGS = OUT_ASSETS / "backgrounds"
OUT_BGS_MOBILE = OUT_BGS / "mobile"
OUT_LOGOS = OUT_ASSETS / "logos"
OUT_LOGOS_TRANSPARENT = OUT_LOGOS / "transparent"
OUT_THUMBS = OUT_ASSETS / "thumbnails"
MANIFEST_PATH = PROJECT_ROOT / "tools" / "asset_manifest.json"


def ensure_directories():
    for d in [OUT_BGS, OUT_BGS_MOBILE, OUT_LOGOS, OUT_LOGOS_TRANSPARENT, OUT_THUMBS]:
        d.mkdir(parents=True, exist_ok=True)


def enhance_photo(pil_img: Image.Image, sharpness_factor: float = 1.3, contrast_factor: float = 1.1) -> Image.Image:
    """
    Non-destructive photo enhancement:
    - Orientation correction via EXIF
    - Edge-preserving unsharp mask via OpenCV
    - Conservative tonal and contrast optimization
    """
    # 1. Orientation
    img = ImageOps.exif_transpose(pil_img)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # 2. OpenCV unsharp masking for edge definition without over-sharpening noise
    cv_img = np.array(img)[:, :, ::-1]  # RGB to BGR
    # Denoise subtle JPEG chroma noise
    denoised = cv2.bilateralFilter(cv_img, d=5, sigmaColor=30, sigmaSpace=30)
    # Unsharp mask
    gaussian = cv2.GaussianBlur(denoised, (0, 0), 1.8)
    unsharp = cv2.addWeighted(denoised, 1.45, gaussian, -0.45, 0)

    # Back to PIL
    res_pil = Image.fromarray(unsharp[:, :, ::-1])

    # 3. Fine contrast tuning
    enh_contrast = ImageEnhance.Contrast(res_pil).enhance(contrast_factor)
    enh_sharp = ImageEnhance.Sharpness(enh_contrast).enhance(sharpness_factor)
    return enh_sharp


def extract_transparent_logos():
    """
    Extract and optimize official branding from 'Minaram Cup Championship Branding Set.png'
    and fallback to 'Logo diffrent types.png'.
    Preserves exact anti-aliasing and native alpha transparency.
    """
    branding_set_path = LOGO_DIR / "Minaram Cup Championship Branding Set.png"
    crest_master_path = LOGO_DIR / "minaram_crest_master.png"
    horiz_path = LOGO_DIR / "minaram_horizontal_white.png"
    badge_path = LOGO_DIR / "minaram_badge_compact.png"

    # If the branding set is present, extract or load the segmented components
    if branding_set_path.exists():
        logger.info(f"Processing Championship Branding Set from {branding_set_path}...")
        brand_img = Image.open(branding_set_path).convert("RGBA")
        bw, bh = brand_img.size

        # Segment 1: Master Crest (Left side: approx X:[50, 825], Y:[10, 775])
        crest_crop = brand_img.crop((45, 10, min(835, bw), min(780, bh)))
        crest_bbox = crest_crop.split()[-1].getbbox()
        if crest_bbox:
            pad = 6
            c_box = (
                max(0, crest_bbox[0] - pad),
                max(0, crest_bbox[1] - pad),
                min(crest_crop.width, crest_bbox[2] + pad),
                min(crest_crop.height, crest_bbox[3] + pad)
            )
            master_crest = crest_crop.crop(c_box)
        else:
            master_crest = crest_crop

        # Segment 2: Horizontal Wordmark (Top-right: X:[860, 1930], Y:[95, 390])
        horiz_crop = brand_img.crop((855, 90, min(1935, bw), min(395, bh)))
        horiz_bbox = horiz_crop.split()[-1].getbbox()
        if horiz_bbox:
            pad = 6
            h_box = (
                max(0, horiz_bbox[0] - pad),
                max(0, horiz_bbox[1] - pad),
                min(horiz_crop.width, horiz_bbox[2] + pad),
                min(horiz_crop.height, horiz_bbox[3] + pad)
            )
            horiz_logo = horiz_crop.crop(h_box)
        else:
            horiz_logo = horiz_crop

        # Segment 3: Compact Badge (Bottom-right: X:[1155, 1525], Y:[390, 760])
        badge_crop = brand_img.crop((1150, 390, min(1530, bw), min(760, bh)))
        badge_bbox = badge_crop.split()[-1].getbbox()
        if badge_bbox:
            pad = 6
            b_box = (
                max(0, badge_bbox[0] - pad),
                max(0, badge_bbox[1] - pad),
                min(badge_crop.width, badge_bbox[2] + pad),
                min(badge_crop.height, badge_bbox[3] + pad)
            )
            compact_badge = badge_crop.crop(b_box)
        else:
            compact_badge = badge_crop

        # Save extracted master pieces in Logo/
        master_crest.save(crest_master_path, format="PNG", optimize=True)
        horiz_logo.save(horiz_path, format="PNG", optimize=True)
        compact_badge.save(badge_path, format="PNG", optimize=True)

        logo_white = master_crest
    else:
        # Fallback to sheet
        sheet_path = LOGO_DIR / "Logo diffrent types.png"
        sheet = Image.open(sheet_path).convert("RGBA")
        w, h = sheet.size
        br_crop = sheet.crop((w // 2, h // 2, w, h))
        alpha_box = br_crop.split()[-1].getbbox()
        logo_white = br_crop.crop(alpha_box) if alpha_box else br_crop
        horiz_logo = logo_white
        compact_badge = logo_white

    # Save to frontend public assets
    p_crest = OUT_LOGOS_TRANSPARENT / "minaram_crest_master.png"
    p_crest_root = OUT_LOGOS / "minaram_crest_master.png"
    logo_white.save(p_crest, format="PNG", optimize=True)
    logo_white.save(p_crest_root, format="PNG", optimize=True)

    # Primary white logo (used across navbar, footer, etc.)
    p_white = OUT_LOGOS_TRANSPARENT / "minaram_logo_white.png"
    p_white_root = OUT_LOGOS / "minaram_logo_white.png"
    logo_white.save(p_white, format="PNG", optimize=True)
    logo_white.save(p_white_root, format="PNG", optimize=True)

    # Horizontal wordmark
    p_horiz = OUT_LOGOS_TRANSPARENT / "minaram_horizontal_white.png"
    p_horiz_root = OUT_LOGOS / "minaram_horizontal_white.png"
    horiz_logo.save(p_horiz, format="PNG", optimize=True)
    horiz_logo.save(p_horiz_root, format="PNG", optimize=True)

    # Compact Badge
    p_badge = OUT_LOGOS_TRANSPARENT / "minaram_badge_compact.png"
    p_badge_root = OUT_LOGOS / "minaram_badge_compact.png"
    compact_badge.save(p_badge, format="PNG", optimize=True)
    compact_badge.save(p_badge_root, format="PNG", optimize=True)

    # Dark emblem fallback
    sheet_path = LOGO_DIR / "Logo diffrent types.png"
    if sheet_path.exists():
        sheet = Image.open(sheet_path).convert("RGBA")
        w, h = sheet.size
        bl_crop = sheet.crop((0, h // 2, w // 2, h))
        alpha_box_bl = bl_crop.split()[-1].getbbox()
        logo_dark = bl_crop.crop(alpha_box_bl) if alpha_box_bl else bl_crop
        p_dark = OUT_LOGOS_TRANSPARENT / "minaram_logo_dark.png"
        logo_dark.save(p_dark, format="PNG", optimize=True)

    # Generate crisp website favicon & desktop app icon
    favicon_img = logo_white.copy()
    favicon_img.thumbnail((64, 64), Image.Resampling.LANCZOS)
    p_favicon_png = PROJECT_ROOT / "frontend" / "public" / "favicon.png"
    p_favicon_assets_png = PROJECT_ROOT / "frontend" / "public" / "assets" / "favicon.png"
    p_favicon_ico = PROJECT_ROOT / "frontend" / "public" / "favicon.ico"
    p_app_ico = LOGO_DIR / "minaram_app_icon.ico"
    p_app_png = LOGO_DIR / "minaram_app_icon.png"

    favicon_img.save(p_favicon_png, format="PNG")
    favicon_img.save(p_favicon_assets_png, format="PNG")
    favicon_img.save(p_favicon_ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    favicon_img.save(p_app_ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    favicon_img.save(p_app_png, format="PNG")

    logger.info("Successfully extracted official Minaram Cup Championship Branding Set variants and generated favicons/icons.")
    return [str(p_crest), str(p_white), str(p_horiz), str(p_badge), str(p_favicon_png)]


def process_akhadha_sponsor():
    """
    Process 'Akhadha Logo.jpg'.
    Create:
    1. Clean trimmed version
    2. Transparent keyed version where near-black background is smoothly transitioned to alpha
    """
    logo_path = LOGO_DIR / "Akhadha Logo.jpg"
    if not logo_path.exists():
        logger.warning(f"Akhadha logo not found at {logo_path}")
        return []

    img = Image.open(logo_path).convert("RGB")
    cv_img = np.array(img)[:, :, ::-1]

    # Clean version
    clean_path = OUT_LOGOS / "akhadha_sponsor_clean.jpg"
    img.save(clean_path, quality=95)

    # Transparent background version:
    # Convert black background (RGB values < 30) to smooth alpha mask
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    # Mask: where gray > 25 is foreground
    alpha = np.zeros_like(gray, dtype=np.uint8)
    alpha[gray > 20] = 255
    # Smooth edges with slight blur to prevent jagged edges or white halos
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

    # Combine BGR + alpha
    rgba = cv2.cvtColor(cv_img, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha

    trans_pil = Image.fromarray(rgba[:, :, [2, 1, 0, 3]])
    p_trans = OUT_LOGOS_TRANSPARENT / "akhadha_sponsor_transparent.png"
    p_trans_root = OUT_LOGOS / "akhadha_sponsor_transparent.png"
    trans_pil.save(p_trans, format="PNG", optimize=True)
    trans_pil.save(p_trans_root, format="PNG", optimize=True)

    logger.info("Successfully processed Akhadha sponsor logo variants.")
    return [str(clean_path), str(p_trans)]


def process_background_images() -> List[Dict[str, Any]]:
    """
    Process each supplied background image:
    - Assess quality & aspect ratio
    - Apply edge-preserving enhancement
    - Generate full desktop WebP & JPEG
    - Generate mobile responsive crop (9:16 or centered)
    - Generate thumbnail
    """
    bg_mapping = [
        {
            "src": "07.jpg",
            "slug": "bg_ronaldo_07",
            "desc": "Cristiano Ronaldo dramatic spotlight profile (3:2)",
            "placement": "Homepage featured action panel & results backdrop",
            "is_portrait": False
        },
        {
            "src": "Leomessi wallpaper ✨.jpg",
            "slug": "bg_messi_portrait",
            "desc": "Lionel Messi monochrome studio wallpaper (9:16)",
            "placement": "Player showcase editorial panel & mobile hero",
            "is_portrait": True
        },
        {
            "src": "389420699052302337.jpg",
            "slug": "bg_stadium_cinematic",
            "desc": "Widescreen cinematic pitch and night stadium floodlights (16:9)",
            "placement": "Primary Homepage Hero Background",
            "is_portrait": False
        },
        {
            "src": "626000416992730335.jpg",
            "slug": "bg_match_action",
            "desc": "Intense football pitch action and floodlit duel (3:2)",
            "placement": "Fixtures & Tournament Schedule page backdrop",
            "is_portrait": False
        },
        {
            "src": "🤝.jpg",
            "slug": "bg_rivalry_handshake",
            "desc": "Football handshake between rivals (16:9 respect & fair play)",
            "placement": "About / Fair Play & Rules section background",
            "is_portrait": False
        },
        {
            "src": "2462974793505365.jpg",
            "slug": "bg_player_portrait_1",
            "desc": "Vertical footballer wallpaper (9:16 portrait)",
            "placement": "Teams directory banner & editorial sidebar",
            "is_portrait": True
        },
        {
            "src": "46373071159563432.jpg",
            "slug": "bg_player_portrait_2",
            "desc": "Vertical action wallpaper (9:16 portrait)",
            "placement": "Standings and Points Table backdrop",
            "is_portrait": True
        },
    ]

    manifest_entries = []

    for item in bg_mapping:
        src_path = BGS_DIR / item["src"]
        if not src_path.exists():
            logger.warning(f"File not found: {src_path}")
            continue

        orig_pil = Image.open(src_path)
        orig_w, orig_h = orig_pil.size
        aspect = round(orig_w / orig_h, 2)

        # Quality assessment
        if orig_w < 800 and orig_h < 600:
            quality = "Medium resolution, slightly soft - enhanced with bilateral sharpening"
        else:
            quality = "Good resolution, enhanced with tonal curve & unsharp mask"

        # Enhance photo
        enhanced = enhance_photo(orig_pil, sharpness_factor=1.25, contrast_factor=1.12)

        # 1. Desktop full variant
        p_desktop_webp = OUT_BGS / f"{item['slug']}.webp"
        p_desktop_jpg = OUT_BGS / f"{item['slug']}.jpg"
        enhanced.save(p_desktop_webp, format="WEBP", quality=90)
        enhanced.save(p_desktop_jpg, format="JPEG", quality=92)

        # 2. Mobile responsive crop (centered, max 720px width)
        mobile_img = enhanced.copy()
        if mobile_img.width > 720:
            scale = 720 / mobile_img.width
            mobile_img = mobile_img.resize((720, int(mobile_img.height * scale)), Image.Resampling.LANCZOS)
        p_mobile_webp = OUT_BGS_MOBILE / f"{item['slug']}_mobile.webp"
        mobile_img.save(p_mobile_webp, format="WEBP", quality=85)

        # 3. Small thumbnail (320px wide)
        thumb_img = enhanced.copy()
        thumb_img.thumbnail((320, 240), Image.Resampling.LANCZOS)
        p_thumb_webp = OUT_THUMBS / f"{item['slug']}_thumb.webp"
        thumb_img.save(p_thumb_webp, format="WEBP", quality=80)

        entry = {
            "original_filename": item["src"],
            "slug": item["slug"],
            "description": item["desc"],
            "original_dimensions": [orig_w, orig_h],
            "aspect_ratio": aspect,
            "quality_assessment": quality,
            "enhancement_applied": "Bilateral filter artifact reduction + unsharp mask + tonal leveling",
            "background_removal": "Preserved full photographic wallpaper for rich atmospheric background",
            "intended_placement": item["placement"],
            "outputs": {
                "desktop_webp": f"/assets/backgrounds/{item['slug']}.webp",
                "desktop_jpg": f"/assets/backgrounds/{item['slug']}.jpg",
                "mobile_webp": f"/assets/backgrounds/mobile/{item['slug']}_mobile.webp",
                "thumbnail": f"/assets/thumbnails/{item['slug']}_thumb.webp"
            }
        }
        manifest_entries.append(entry)
        logger.info(f"Processed background: {item['src']} -> {item['slug']}")

    return manifest_entries


def run_pipeline():
    ensure_directories()
    logger.info("Starting MINARAM CUP Image Processing Pipeline...")

    logo_outputs = extract_transparent_logos()
    sponsor_outputs = process_akhadha_sponsor()
    bg_entries = process_background_images()

    manifest = {
        "project": "MINARAM CUP — ELITE ESPORTS PLATFORM",
        "version": "2.0.0",
        "status": "Enhanced & Optimized",
        "logos": {
            "white_emblem": "/assets/logos/transparent/minaram_logo_white.png",
            "dark_emblem": "/assets/logos/transparent/minaram_logo_dark.png",
            "sponsor_akhadha": "/assets/logos/transparent/akhadha_sponsor_transparent.png",
            "sponsor_clean": "/assets/logos/akhadha_sponsor_clean.jpg",
            "favicon": "/favicon.png"
        },
        "backgrounds": bg_entries
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info(f"Asset pipeline complete! Manifest saved to {MANIFEST_PATH}")
    return manifest


if __name__ == "__main__":
    run_pipeline()
