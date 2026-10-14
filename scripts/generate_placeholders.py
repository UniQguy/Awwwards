#!/usr/bin/env python3
"""
Placeholder Asset Generator & Contract Synchronizer for ELECTROCART (Pass R4).
Generates calibrated WebP placeholder posters with Pillow matching category world palettes,
and outputs ASSETS.md with layout contracts, aspect ratios, and owner ffmpeg encoding commands.
"""

from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDERS_DIR = BASE_DIR / "static" / "media" / "placeholders"
ASSETS_MD_PATH = BASE_DIR / "ASSETS.md"

WORLD_PALETTES = {
    "earphones-headphones": {"bg": "#F5F2EB", "surface": "#EDE8DE", "accent": "#9E3D24"},
    "speakers": {"bg": "#F2EFE9", "surface": "#E8E3DA", "accent": "#7C4A2D"},
    "smartphones": {"bg": "#EBF0ED", "surface": "#DEE7E2", "accent": "#1B5E4B"},
    "smartwatches-bands": {"bg": "#EDECE8", "surface": "#E2E0D8", "accent": "#2C5282"},
    "cameras": {"bg": "#F0EDE6", "surface": "#E5E0D5", "accent": "#8C3A27"},
    "tvs": {"bg": "#EBF0F5", "surface": "#DFE7EE", "accent": "#1A5276"},
    "keyboards-mice": {"bg": "#EDF2EA", "surface": "#E1E9DD", "accent": "#2E6930"},
    "cables-chargers-powerbanks": {"bg": "#F3EFEA", "surface": "#E8E2DA", "accent": "#824C28"},
    "cases-protectors": {"bg": "#EFECEE", "surface": "#E4DFE3", "accent": "#5E3A4D"},
    "other": {"bg": "#EFF0F1", "surface": "#E3E5E7", "accent": "#3D4852"},
}

SLOTS = [
    # 1. Home Hero
    {
        "id": "home-hero-poster",
        "filename": "home-hero-poster.webp",
        "page": "Home",
        "section": "Act 1 Cover / Hero",
        "purpose": "Primary exhibition background poster for desktop hero composition.",
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "format": "webp",
        "target_size": "< 180 KB",
        "bg_color": "#F5F2EB",
        "text_color": "#9E3D24",
        "owner_provided": False,
        "desktop_notes": "Reserved 16:9 aspect ratio behind lead collectible plate.",
        "mobile_notes": "Serves as static backdrop poster for coarse pointer devices.",
        "ffmpeg": "ffmpeg -ss 00:00:01 -i hero.mov -vframes 1 -q:v 85 home-hero-poster.webp",
    },
    {
        "id": "home-hero-loop",
        "filename": "home-hero-loop.mp4",
        "page": "Home",
        "section": "Act 1 Cover / Hero",
        "purpose": "Cinematic ambient loop of rotating precision hardware.",
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "format": "mp4 (H.264, muted)",
        "target_size": "< 2.5 MB",
        "bg_color": "#F5F2EB",
        "text_color": "#9E3D24",
        "owner_provided": True,
        "desktop_notes": "Tier 1 fine pointer desktop autoplay loop; paused when out of view or tab hidden.",
        "mobile_notes": "Not downloaded on mobile or under save-data / reduced-motion.",
        "ffmpeg": "ffmpeg -i hero_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart -pix_fmt yuv420p static/media/video/home-hero-loop.mp4",
    },
    {
        "id": "home-hero-loop-webm",
        "filename": "home-hero-loop.webm",
        "page": "Home",
        "section": "Act 1 Cover / Hero",
        "purpose": "WebM modern codec variant for hero video loop.",
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "format": "webm (VP9, muted)",
        "target_size": "< 2.0 MB",
        "bg_color": "#F5F2EB",
        "text_color": "#9E3D24",
        "owner_provided": True,
        "desktop_notes": "Secondary source for modern browsers.",
        "mobile_notes": "Not downloaded on mobile.",
        "ffmpeg": "ffmpeg -i hero_raw.mov -c:v libvpx-vp9 -b:v 0 -crf 30 -an static/media/video/home-hero-loop.webm",
    },
    {
        "id": "home-hero-loop-m",
        "filename": "home-hero-loop-m.mp4",
        "page": "Home",
        "section": "Act 1 Cover / Hero Mobile",
        "purpose": "Vertical 9:16 video loop variant for high-DPI mobile devices.",
        "width": 720,
        "height": 1280,
        "aspect_ratio": "9:16",
        "format": "mp4 (H.264, muted)",
        "target_size": "< 1.0 MB",
        "bg_color": "#F5F2EB",
        "text_color": "#9E3D24",
        "owner_provided": True,
        "desktop_notes": "Omitted on desktop.",
        "mobile_notes": "Optional mobile playback under fine Wi-Fi connections.",
        "ffmpeg": "ffmpeg -i hero_vertical.mov -vf 'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280' -c:v libx264 -preset slow -crf 23 -an -movflags +faststart static/media/video/home-hero-loop-m.mp4",
    },
    {
        "id": "hero-model-1",
        "filename": "hero-model-1.glb",
        "page": "Home",
        "section": "Act 1 Cover / WebGL Plinth",
        "purpose": "Interactive 3D GLTF turntable asset for desktop pointer tilt.",
        "width": 0,
        "height": 0,
        "aspect_ratio": "1:1",
        "format": "glb (draco compressed)",
        "target_size": "< 1.8 MB",
        "bg_color": "#F5F2EB",
        "text_color": "#9E3D24",
        "owner_provided": True,
        "desktop_notes": "Lazy-loaded Three.js canvas layer.",
        "mobile_notes": "Completely omitted on mobile devices.",
        "ffmpeg": "gltf-pipeline -i raw_model.gltf -o static/media/models/hero-model-1.glb -d",
    },

    # 2. Product Detail Secondary Video & Poster
    {
        "id": "product-secondary-poster",
        "filename": "product-secondary-poster.webp",
        "page": "Product Detail",
        "section": "Secondary Media Exhibition",
        "purpose": "Poster for secondary video or hardware teardown slot.",
        "width": 800,
        "height": 800,
        "aspect_ratio": "1:1",
        "format": "webp",
        "target_size": "< 70 KB",
        "bg_color": "#EDE8DE",
        "text_color": "#9E3D24",
        "owner_provided": False,
        "desktop_notes": "Displays under exhibition frame when video is not playing.",
        "mobile_notes": "Static card fallback on touch devices.",
        "ffmpeg": "ffmpeg -ss 00:00:01 -i product_video.mp4 -vframes 1 -q:v 85 product-secondary-poster.webp",
    },
    {
        "id": "product-secondary-video",
        "filename": "product-secondary-video.mp4",
        "page": "Product Detail",
        "section": "Secondary Media Exhibition",
        "purpose": "Disassembly or hardware finish rotation video loop.",
        "width": 800,
        "height": 800,
        "aspect_ratio": "1:1",
        "format": "mp4 (H.264, muted)",
        "target_size": "< 1.5 MB",
        "bg_color": "#EDE8DE",
        "text_color": "#9E3D24",
        "owner_provided": True,
        "desktop_notes": "6s seamless loop attached to ProductMedia records.",
        "mobile_notes": "Hidden on cellular connections.",
        "ffmpeg": "ffmpeg -i product_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/product-secondary-video.mp4",
    },

    # 3. Social & Brand Assets
    {
        "id": "og-default",
        "filename": "og-default.webp",
        "page": "Global Meta",
        "section": "Open Graph Share Card",
        "purpose": "Open Graph social preview image for external shares.",
        "width": 1200,
        "height": 630,
        "aspect_ratio": "1.91:1",
        "format": "webp",
        "target_size": "< 120 KB",
        "bg_color": "#F5F2EB",
        "text_color": "#1C1917",
        "owner_provided": False,
        "desktop_notes": "Shared in <meta property='og:image'> tag.",
        "mobile_notes": "Shared in social app link cards.",
        "ffmpeg": "N/A",
    },
]

# Add the 10 category marquee posters and video films
CATEGORIES = [
    ("earphones-headphones", "Earphones & Headphones"),
    ("speakers", "Acoustics & Speakers"),
    ("smartphones", "Smartphones & Devices"),
    ("smartwatches-bands", "Smartwatches & Wearables"),
    ("cameras", "Cameras & Optics"),
    ("tvs", "Displays & Televisions"),
    ("keyboards-mice", "Keyboards & Pointers"),
    ("cables-chargers-powerbanks", "Cables, Chargers & Power"),
    ("cases-protectors", "Cases & Protectors"),
    ("other", "Sundry Electronics"),
]

for slug, name in CATEGORIES:
    pal = WORLD_PALETTES.get(slug, WORLD_PALETTES["other"])
    SLOTS.append({
        "id": f"category-{slug}-marquee-poster",
        "filename": f"category-{slug}-marquee-poster.webp",
        "page": f"Category: {name}",
        "section": "Marquee Backdrop Slot",
        "purpose": f"Atmospheric world backdrop poster for {name} marquee.",
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "format": "webp",
        "target_size": "< 150 KB",
        "bg_color": pal["surface"],
        "text_color": pal["accent"],
        "owner_provided": False,
        "desktop_notes": "Fills marquee framed slot without competing with typography.",
        "mobile_notes": "Poster fallback.",
        "ffmpeg": f"ffmpeg -ss 00:00:01 -i {slug}.mov -vframes 1 -q:v 85 category-{slug}-marquee-poster.webp",
    })
    SLOTS.append({
        "id": f"category-{slug}-film",
        "filename": f"category-{slug}-film.mp4",
        "page": f"Category: {name}",
        "section": "Marquee Backdrop Slot",
        "purpose": f"Atmospheric 6-8s video loop for {name} marquee.",
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "format": "mp4 (H.264, muted)",
        "target_size": "< 2.0 MB",
        "bg_color": pal["surface"],
        "text_color": pal["accent"],
        "owner_provided": True,
        "desktop_notes": "Plays on Tier 1 desktop only; pauses when scrolled out of view.",
        "mobile_notes": "Poster only.",
        "ffmpeg": f"ffmpeg -i {slug}_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/category-{slug}-film.mp4",
    })

# Add the 6 Home Chapter stage backdrop posters
for idx in range(1, 7):
    slug, name = CATEGORIES[idx - 1]
    pal = WORLD_PALETTES.get(slug, WORLD_PALETTES["other"])
    SLOTS.append({
        "id": f"home-chapter-{idx}-poster",
        "filename": f"home-chapter-{idx}-poster.webp",
        "page": "Home",
        "section": f"Act 3 Chapter {idx:02d} ({name})",
        "purpose": f"Stage backdrop plate for Chapter {idx:02d}.",
        "width": 800,
        "height": 800,
        "aspect_ratio": "1:1",
        "format": "webp",
        "target_size": "< 80 KB",
        "bg_color": pal["surface"],
        "text_color": pal["accent"],
        "owner_provided": False,
        "desktop_notes": "Subtle architectural plate backing the collectible stage.",
        "mobile_notes": "Mobile snap card plate.",
        "ffmpeg": "N/A",
    })


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

        # Draw clean 1px hairline double inner border
        draw.rectangle([(12, 12), (w - 13, h - 13)], outline=fg, width=1)
        draw.rectangle([(24, 24), (w - 25, h - 25)], outline=fg, width=1)

        label_text = f"PLACEHOLDER: {slot['id']}"
        dims_text = f"{w} x {h} px ({slot['aspect_ratio']})"
        notice_text = "ELECTROCART CALIBRATED MEDIA SLOT"

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
        "This document defines the media slot contracts for Phase 5 (The Editorial Layer), Phase 6 (Motion Craft), and Final Pass R4 (The Gallery).",
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
            f"- **File Path**: `static/media/{'video' if '.mp4' in slot['filename'] or '.webm' in slot['filename'] else 'models' if '.glb' in slot['filename'] else 'placeholders'}/{slot['filename']}`",
            f"- **Page / Placement**: {slot['page']} ({slot['section']})",
            f"- **Purpose**: {slot['purpose']}",
            f"- **Dimensions**: {slot['width']} × {slot['height']} px (Aspect Ratio: `{slot['aspect_ratio']}`)",
            f"- **Format & Budget**: {slot['format']} ({slot['target_size']})",
            f"- **Desktop Layout Contract**: {slot['desktop_notes']}",
            f"- **Mobile Layout Contract**: {slot['mobile_notes']}",
            f"- **Handover Requirement**: {'Requires production asset from site owner.' if slot['owner_provided'] else 'Generated locally as neutral WebP calibration poster.'}",
            f"- **Owner Encoding Command**: `{slot['ffmpeg']}`",
            "",
        ])

    content.extend([
        "---",
        "",
        "## Owner Video Encoding Standard (ffmpeg Reference)",
        "",
        "### 1. Seamless MP4 Loops (1080p, H.264, Muted, Faststart)",
        "```bash",
        "ffmpeg -i input_master.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart -pix_fmt yuv420p output.mp4",
        "```",
        "",
        "### 2. Modern WebM Loop (VP9, Muted)",
        "```bash",
        "ffmpeg -i input_master.mov -c:v libvpx-vp9 -b:v 0 -crf 30 -an output.webm",
        "```",
        "",
        "### 3. Mobile Vertical Variant (720x1280 9:16)",
        "```bash",
        "ffmpeg -i input_master.mov -vf \"scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280\" -c:v libx264 -preset slow -crf 23 -an -movflags +faststart output.mp4",
        "```",
        "",
        "### 4. Poster Extraction from Video Frame",
        "```bash",
        "ffmpeg -ss 00:00:01 -i input.mp4 -vframes 1 -q:v 85 poster.webp",
        "```",
    ])

    with open(ASSETS_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(content) + "\n")

    print(f"Successfully generated ASSETS.md at {ASSETS_MD_PATH}")


if __name__ == "__main__":
    generate_posters()
    write_assets_md()
