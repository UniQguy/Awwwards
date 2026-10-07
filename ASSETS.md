# ELECTROCART Asset Specification Contract (ASSETS.md)

This document defines the media slot contracts for Phase 5 (The Editorial Layer) and Phase 6 (Motion & Sensory Craft).
All visual layouts reserve exact aspect ratios so production media drops in seamlessly without layout shifts (CLS = 0).

---

## Media Slots Inventory

| Slot ID | Filename | Page & Section | Format | Dimensions | Aspect Ratio | Target Size | Handover Status |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|
| `home-hero-poster` | `home-hero-1.webp` | Home — Hero Exhibition | webp | 1200x800 | 3:2 | < 120 KB | Generated (WebP) |
| `home-hero-video` | `home-hero-video.mp4` | Home — Hero Exhibition | mp4 (H.264 / AAC) | 1920x1080 | 16:9 | < 2.5 MB | **OWNER-PROVIDED** |
| `home-hero-model` | `home-hero-model-1.glb` | Home — Hero Exhibition | glb (draco compressed) | Vector / 3D | 1:1 | < 1.8 MB | **OWNER-PROVIDED** |
| `home-chapter-1-poster` | `home-chapter-1.webp` | Home — Chapter 01 (Audio & Monitors) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |
| `home-chapter-2-poster` | `home-chapter-2.webp` | Home — Chapter 02 (Acoustic Speakers) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |
| `home-chapter-3-poster` | `home-chapter-3.webp` | Home — Chapter 03 (Slate Smartphones) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |
| `home-chapter-4-poster` | `home-chapter-4.webp` | Home — Chapter 04 (Smartwatches & Bands) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |
| `home-chapter-5-poster` | `home-chapter-5.webp` | Home — Chapter 05 (Optical Cameras) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |
| `home-chapter-6-poster` | `home-chapter-6.webp` | Home — Chapter 06 (Television Displays) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |
| `category-earphones-headphones-marquee` | `category-earphones-headphones-marquee.webp` | Category Detail — Marquee Banner | webp | 1200x500 | 12:5 | < 100 KB | Generated (WebP) |
| `product-secondary-poster` | `product-secondary-1.webp` | Product Detail — Secondary Media Exhibition | webp | 600x600 | 1:1 | < 60 KB | Generated (WebP) |
| `product-model-slot` | `product-model-1.glb` | Product Detail — 3D Inspection Viewer | glb | Vector / 3D | 1:1 | < 2.0 MB | **OWNER-PROVIDED** |

---

## Slot Specifications & Layout Contracts

### `home-hero-poster`
- **File Path**: `static/media/placeholders/home-hero-1.webp`
- **Page / Placement**: Home (Hero Exhibition)
- **Purpose**: Primary exhibition background poster for desktop hero composition.
- **Dimensions**: 1200 × 800 px (Aspect Ratio: `3:2`)
- **Format & Budget**: webp (< 120 KB)
- **Desktop Layout Contract**: Fills right-column exhibition canvas.
- **Mobile Layout Contract**: Hidden under 768px in favor of single product plate.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.

### `home-hero-video`
- **File Path**: `static/media/placeholders/home-hero-video.mp4`
- **Page / Placement**: Home (Hero Exhibition)
- **Purpose**: Cinematic ambient loop of rotating precision hardware.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264 / AAC) (< 2.5 MB)
- **Desktop Layout Contract**: Muted, playsinline, loop attribute.
- **Mobile Layout Contract**: Omitted on cellular connections or autoplay-restricted browsers.
- **Handover Requirement**: Requires production asset from site owner.

### `home-hero-model`
- **File Path**: `static/media/placeholders/home-hero-model-1.glb`
- **Page / Placement**: Home (Hero Exhibition)
- **Purpose**: Interactive 3D GLTF/GLB asset for pointer tilt in Phase 6.
- **Dimensions**: 0 × 0 px (Aspect Ratio: `1:1`)
- **Format & Budget**: glb (draco compressed) (< 1.8 MB)
- **Desktop Layout Contract**: Three.js / WebGL canvas interactive layer.
- **Mobile Layout Contract**: Disabled on low-power devices in favor of WebP poster.
- **Handover Requirement**: Requires production asset from site owner.

### `home-chapter-1-poster`
- **File Path**: `static/media/placeholders/home-chapter-1.webp`
- **Page / Placement**: Home (Chapter 01 (Audio & Monitors))
- **Purpose**: Chapter backdrop showcasing acoustic driver diaphragm.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Anchor image for chapter split.
- **Mobile Layout Contract**: Stacks cleanly above product snap row.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.

### `home-chapter-2-poster`
- **File Path**: `static/media/placeholders/home-chapter-2.webp`
- **Page / Placement**: Home (Chapter 02 (Acoustic Speakers))
- **Purpose**: Chapter backdrop showcasing acoustic speaker mesh.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Left-column illustration.
- **Mobile Layout Contract**: Mobile scroll-snap card.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.

### `home-chapter-3-poster`
- **File Path**: `static/media/placeholders/home-chapter-3.webp`
- **Page / Placement**: Home (Chapter 03 (Slate Smartphones))
- **Purpose**: Chapter backdrop showcasing surgical steel chassis.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Left-column illustration.
- **Mobile Layout Contract**: Mobile scroll-snap card.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.

### `home-chapter-4-poster`
- **File Path**: `static/media/placeholders/home-chapter-4.webp`
- **Page / Placement**: Home (Chapter 04 (Smartwatches & Bands))
- **Purpose**: Chapter backdrop showcasing bead-blasted titanium.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Left-column illustration.
- **Mobile Layout Contract**: Mobile scroll-snap card.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.

### `home-chapter-5-poster`
- **File Path**: `static/media/placeholders/home-chapter-5.webp`
- **Page / Placement**: Home (Chapter 05 (Optical Cameras))
- **Purpose**: Chapter backdrop showcasing knurled brass aperture dial.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Left-column illustration.
- **Mobile Layout Contract**: Mobile scroll-snap card.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.

### `home-chapter-6-poster`
- **File Path**: `static/media/placeholders/home-chapter-6.webp`
- **Page / Placement**: Home (Chapter 06 (Television Displays))
- **Purpose**: Chapter backdrop showcasing micro-edge OLED glass.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Left-column illustration.
- **Mobile Layout Contract**: Mobile scroll-snap card.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.

### `category-earphones-headphones-marquee`
- **File Path**: `static/media/placeholders/category-earphones-headphones-marquee.webp`
- **Page / Placement**: Category Detail (Marquee Banner)
- **Purpose**: Editorial marquee header backdrop for earphones-headphones.
- **Dimensions**: 1200 × 500 px (Aspect Ratio: `12:5`)
- **Format & Budget**: webp (< 100 KB)
- **Desktop Layout Contract**: Wide panoramic header banner.
- **Mobile Layout Contract**: Scaled to full-width header.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.

### `product-secondary-poster`
- **File Path**: `static/media/placeholders/product-secondary-1.webp`
- **Page / Placement**: Product Detail (Secondary Media Exhibition)
- **Purpose**: Quiet secondary exhibition slot for accessory disassembly or exploded diagram.
- **Dimensions**: 600 × 600 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 60 KB)
- **Desktop Layout Contract**: Secondary frame beneath sticky left column.
- **Mobile Layout Contract**: Stacked beneath primary photo frame.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.

### `product-model-slot`
- **File Path**: `static/media/placeholders/product-model-1.glb`
- **Page / Placement**: Product Detail (3D Inspection Viewer)
- **Purpose**: 3D turntable model for product detail view in Phase 6.
- **Dimensions**: 0 × 0 px (Aspect Ratio: `1:1`)
- **Format & Budget**: glb (< 2.0 MB)
- **Desktop Layout Contract**: WebGL model-viewer slot.
- **Mobile Layout Contract**: Loaded only upon explicit user touch.
- **Handover Requirement**: Requires production asset from site owner.

---

## Owner Handover Action Items
1. **3D Assets (`.glb`)**: Provide Draco-compressed GLB files for `home-hero-model-1.glb` and `product-model-1.glb` to activate Three.js turntable interactions in Phase 6.
2. **Cinematic Loop (`.mp4`)**: Provide seamless 8-12 second video for `home-hero-video.mp4` encoded with H.264 video at 1080p, audio muted.
3. **Template Tolerance**: Storefront templates gracefully tolerate absent owner files and display the calibrated WebP posters or fall back to typography.
