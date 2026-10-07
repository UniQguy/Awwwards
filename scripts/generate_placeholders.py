#!/usr/bin/env python3
"""
Placeholder Asset Generator & Contract Synchronizer for ELECTROCART (Phase 5).
Generates neutral, clearly labeled webp placeholder posters using Pillow,
and generates ASSETS.md documenting all media slots, aspect ratios, and owner handover requirements.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDERS_DIR = BASE_DIR / "static" / "media" / "placeholders"
ASSETS_MD_PATH = BASE_DIR / "ASSETS.md"

SLOTS = [
    {
        "id": "home-hero-poster",
        "filename": "home-hero-1.webp",
        "page": "Home",
        "section": "Hero Exhibition",
        "purpose": "Primary exhibition background poster for desktop hero composition.",
        "width": 1200,
        "height": 800,
        "aspect_ratio": "3:2",
        "format": "webp",
        "duration": "N/A",
        "target_size": "< 120 KB",
        "bg_color": "#F4EFEA",
        "text_color": "#8C531B",
        "mobile_notes": "Hidden under 768px in favor of single product plate.",
        "desktop_notes": "Fills right-column exhibition canvas.",
        "owner_provided": False,
    },
    {
        "id": "home-hero-video",
        "filename": "home-hero-video.mp4",
        "page": "Home",
        "section": "Hero Exhibition",
        "purpose": "Cinematic ambient loop of rotating precision hardware.",
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "format": "mp4 (H.264 / AAC)",
        "duration": "8-12 seconds (seamless loop)",
        "target_size": "< 2.5 MB",
        "bg_color": "#E5E5E5",
        "text_color": "#333333",
        "mobile_notes": "Omitted on cellular connections or autoplay-restricted browsers.",
        "desktop_notes": "Muted, playsinline, loop attribute.",
        "owner_provided": True,
    },
    {
        "id": "home-hero-model",
        "filename": "home-hero-model-1.glb",
        "page": "Home",
        "section": "Hero Exhibition",
        "purpose": "Interactive 3D GLTF/GLB asset for pointer tilt in Phase 6.",
        "width": 0,
        "height": 0,
        "aspect_ratio": "1:1",
        "format": "glb (draco compressed)",
        "duration": "N/A",
        "target_size": "< 1.8 MB",
        "bg_color": "#E5E5E5",
        "text_color": "#333333",
        "mobile_notes": "Disabled on low-power devices in favor of WebP poster.",
        "desktop_notes": "Three.js / WebGL canvas interactive layer.",
        "owner_provided": True,
    },
    {
        "id": "home-chapter-1-poster",
        "filename": "home-chapter-1.webp",
        "page": "Home",
        "section": "Chapter 01 (Audio & Monitors)",
        "purpose": "Chapter backdrop showcasing acoustic driver diaphragm.",
        "width": 800,
        "height": 800,
        "aspect_ratio": "1:1",
        "format": "webp",
        "duration": "N/A",
        "target_size": "< 80 KB",
        "bg_color": "#F4EFEA",
        "text_color": "#8C531B",
        "mobile_notes": "Stacks cleanly above product snap row.",
        "desktop_notes": "Anchor image for chapter split.",
        "owner_provided": False,
    },
    {
        "id": "home-chapter-2-poster",
        "filename": "home-chapter-2.webp",
        "page": "Home",
        "section": "Chapter 02 (Acoustic Speakers)",
        "purpose": "Chapter backdrop showcasing acoustic speaker mesh.",
        "width": 800,
        "height": 800,
        "aspect_ratio": "1:1",
        "format": "webp",
        "duration": "N/A",
        "target_size": "< 80 KB",
        "bg_color": "#EDF3F0",
        "text_color": "#2D5A4C",
        "mobile_notes": "Mobile scroll-snap card.",
        "desktop_notes": "Left-column illustration.",
        "owner_provided": False,
    },
    {
        "id": "home-chapter-3-poster",
        "filename": "home-chapter-3.webp",
        "page": "Home",
        "section": "Chapter 03 (Slate Smartphones)",
        "purpose": "Chapter backdrop showcasing surgical steel chassis.",
        "width": 800,
        "height": 800,
        "aspect_ratio": "1:1",
        "format": "webp",
        "duration": "N/A",
        "target_size": "< 80 KB",
        "bg_color": "#F6EEF1",
        "text_color": "#8A3D52",
        "mobile_notes": "Mobile scroll-snap card.",
        "desktop_notes": "Left-column illustration.",
        "owner_provided": False,
    },
    {
        "id": "home-chapter-4-poster",
        "filename": "home-chapter-4.webp",
        "page": "Home",
        "section": "Chapter 04 (Smartwatches & Bands)",
        "purpose": "Chapter backdrop showcasing bead-blasted titanium.",
        "width": 800,
        "height": 800,
        "aspect_ratio": "1:1",
        "format": "webp",
        "duration": "N/A",
        "target_size": "< 80 KB",
        "bg_color": "#F2EEF5",
        "text_color": "#5C4A6F",
        "mobile_notes": "Mobile scroll-snap card.",
        "desktop_notes": "Left-column illustration.",
        "owner_provided": False,
    },
    {
        "id": "home-chapter-5-poster",
        "filename": "home-chapter-5.webp",
        "page": "Home",
        "section": "Chapter 05 (Optical Cameras)",
        "purpose": "Chapter backdrop showcasing knurled brass aperture dial.",
        "width": 800,
        "height": 800,
        "aspect_ratio": "1:1",
        "format": "webp",
        "duration": "N/A",
        "target_size": "< 80 KB",
        "bg_color": "#F5F0EB",
        "text_color": "#6E4F32",
        "mobile_notes": "Mobile scroll-snap card.",
        "desktop_notes": "Left-column illustration.",
        "owner_provided": False,
    },
    {
        "id": "home-chapter-6-poster",
        "filename": "home-chapter-6.webp",
        "page": "Home",
        "section": "Chapter 06 (Television Displays)",
        "purpose": "Chapter backdrop showcasing micro-edge OLED glass.",
        "width": 800,
        "height": 800,
        "aspect_ratio": "1:1",
        "format": "webp",
        "duration": "N/A",
        "target_size": "< 80 KB",
        "bg_color": "#EBF0F5",
        "text_color": "#1E3F5A",
        "mobile_notes": "Mobile scroll-snap card.",
        "desktop_notes": "Left-column illustration.",
        "owner_provided": False,
    },
    {
        "id": "category-earphones-headphones-marquee",
        "filename": "category-earphones-headphones-marquee.webp",
        "page": "Category Detail",
        "section": "Marquee Banner",
        "purpose": "Editorial marquee header backdrop for earphones-headphones.",
        "width": 1200,
        "height": 500,
        "aspect_ratio": "12:5",
        "format": "webp",
        "duration": "N/A",
        "target_size": "< 100 KB",
        "bg_color": "#F4EFEA",
        "text_color": "#8C531B",
        "mobile_notes": "Scaled to full-width header.",
        "desktop_notes": "Wide panoramic header banner.",
        "owner_provided": False,
    },
    {
        "id": "product-secondary-poster",
        "filename": "product-secondary-1.webp",
        "page": "Product Detail",
        "section": "Secondary Media Exhibition",
        "purpose": "Quiet secondary exhibition slot for accessory disassembly or exploded diagram.",
        "width": 600,
        "height": 600,
        "aspect_ratio": "1:1",
        "format": "webp",
        "duration": "N/A",
        "target_size": "< 60 KB",
        "bg_color": "#F5F5F3",
        "text_color": "#555555",
        "mobile_notes": "Stacked beneath primary photo frame.",
        "desktop_notes": "Secondary frame beneath sticky left column.",
        "owner_provided": False,
    },
    {
        "id": "product-model-slot",
        "filename": "product-model-1.glb",
        "page": "Product Detail",
        "section": "3D Inspection Viewer",
        "purpose": "3D turntable model for product detail view in Phase 6.",
        "width": 0,
        "height": 0,
        "aspect_ratio": "1:1",
        "format": "glb",
        "duration": "N/A",
        "target_size": "< 2.0 MB",
        "bg_color": "#F0F0F0",
        "text_color": "#222222",
        "mobile_notes": "Loaded only upon explicit user touch.",
        "desktop_notes": "WebGL model-viewer slot.",
        "owner_provided": True,
    },
]


def generate_posters():
    PLACEHOLDERS_DIR.mkdir(parents=True, exist_ok=True)
    created_count = 0

    for slot in SLOTS:
        if slot["owner_provided"]:
            continue

        filepath = PLACEHOLDERS_DIR / slot["filename"]
        w = slot["width"]
        h = slot["height"]
        bg = slot["bg_color"]
        fg = slot["text_color"]

        img = Image.new("RGB", (w, h), color=bg)
        draw = ImageDraw.Draw(img)

        # Draw a subtle double inner border
        draw.rectangle([(8, 8), (w - 9, h - 9)], outline=fg, width=1)
        draw.rectangle([(16, 16), (w - 17, h - 17)], outline=fg, width=1)

        # Center typography
        label_text = f"PLACEHOLDER: {slot['id']}"
        dims_text = f"{w} x {h} px ({slot['aspect_ratio']})"
        notice_text = "ELECTROCART EXHIBITION SLOT"

        # Simple text drawing with default font
        draw.text((w // 2, h // 2 - 24), label_text, fill=fg, anchor="mm")
        draw.text((w // 2, h // 2), dims_text, fill=fg, anchor="mm")
        draw.text((w // 2, h // 2 + 24), notice_text, fill=fg, anchor="mm")

        img.save(filepath, "WEBP", quality=85)
        created_count += 1
        print(f"Generated WebP poster: {slot['filename']} ({w}x{h})")

    print(f"Successfully generated {created_count} placeholder poster assets.")


def write_assets_md():
    content = [
        "# ELECTROCART Asset Specification Contract (ASSETS.md)",
        "",
        "This document defines the media slot contracts for Phase 5 (The Editorial Layer) and Phase 6 (Motion & Sensory Craft).",
        "All visual layouts reserve exact aspect ratios so production media drops in seamlessly without layout shifts (CLS = 0).",
        "",
        "---",
        "",
        "## Media Slots Inventory",
        "",
        "| Slot ID | Filename | Page & Section | Format | Dimensions | Aspect Ratio | Target Size | Handover Status |",
        "|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|",
    ]

    for slot in SLOTS:
        dims = f"{slot['width']}x{slot['height']}" if slot["width"] > 0 else "Vector / 3D"
        status = "**OWNER-PROVIDED**" if slot["owner_provided"] else "Generated (WebP)"
        content.append(
            f"| `{slot['id']}` | `{slot['filename']}` | {slot['page']} — {slot['section']} | {slot['format']} | {dims} | {slot['aspect_ratio']} | {slot['target_size']} | {status} |"
        )

    content.extend([
        "",
        "---",
        "",
        "## Slot Specifications & Layout Contracts",
        "",
    ])

    for slot in SLOTS:
        content.extend([
            f"### `{slot['id']}`",
            f"- **File Path**: `static/media/placeholders/{slot['filename']}`",
            f"- **Page / Placement**: {slot['page']} ({slot['section']})",
            f"- **Purpose**: {slot['purpose']}",
            f"- **Dimensions**: {slot['width']} × {slot['height']} px (Aspect Ratio: `{slot['aspect_ratio']}`)",
            f"- **Format & Budget**: {slot['format']} ({slot['target_size']})",
            f"- **Desktop Layout Contract**: {slot['desktop_notes']}",
            f"- **Mobile Layout Contract**: {slot['mobile_notes']}",
            f"- **Handover Requirement**: {'Requires production asset from site owner.' if slot['owner_provided'] else 'Generated locally as neutral WebP calibration poster.'}",
            "",
        ])

    content.extend([
        "---",
        "",
        "## Owner Handover Action Items",
        "1. **3D Assets (`.glb`)**: Provide Draco-compressed GLB files for `home-hero-model-1.glb` and `product-model-1.glb` to activate Three.js turntable interactions in Phase 6.",
        "2. **Cinematic Loop (`.mp4`)**: Provide seamless 8-12 second video for `home-hero-video.mp4` encoded with H.264 video at 1080p, audio muted.",
        "3. **Template Tolerance**: Storefront templates gracefully tolerate absent owner files and display the calibrated WebP posters or fall back to typography.",
    ])

    with open(ASSETS_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(content) + "\n")

    print(f"Successfully generated ASSETS.md at {ASSETS_MD_PATH}")


if __name__ == "__main__":
    generate_posters()
    write_assets_md()
