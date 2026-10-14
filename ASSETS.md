# ELECTROCART Asset Specification Contract (ASSETS.md)

This document defines the media slot contracts for Phase 5 (The Editorial Layer), Phase 6 (Motion Craft), and Final Pass R4 (The Gallery).
All visual layouts reserve exact aspect ratios so production media drops in seamlessly without layout shifts (CLS = 0).

---

## Media Slots Inventory

| Slot ID | Filename | Page & Section | Format | Dimensions | Aspect Ratio | Target Size | Handover Status |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|
| `home-hero-poster` | `home-hero-poster.webp` | Home — Act 1 Cover / Hero | webp | 1920x1080 | 16:9 | < 180 KB | Generated (WebP) |
| `home-hero-loop` | `home-hero-loop.mp4` | Home — Act 1 Cover / Hero | mp4 (H.264, muted) | 1920x1080 | 16:9 | < 2.5 MB | **OWNER-PROVIDED** |
| `home-hero-loop-webm` | `home-hero-loop.webm` | Home — Act 1 Cover / Hero | webm (VP9, muted) | 1920x1080 | 16:9 | < 2.0 MB | **OWNER-PROVIDED** |
| `home-hero-loop-m` | `home-hero-loop-m.mp4` | Home — Act 1 Cover / Hero Mobile | mp4 (H.264, muted) | 720x1280 | 9:16 | < 1.0 MB | **OWNER-PROVIDED** |
| `hero-model-1` | `hero-model-1.glb` | Home — Act 1 Cover / WebGL Plinth | glb (draco compressed) | Vector / 3D | 1:1 | < 1.8 MB | **OWNER-PROVIDED** |
| `product-secondary-poster` | `product-secondary-poster.webp` | Product Detail — Secondary Media Exhibition | webp | 800x800 | 1:1 | < 70 KB | Generated (WebP) |
| `product-secondary-video` | `product-secondary-video.mp4` | Product Detail — Secondary Media Exhibition | mp4 (H.264, muted) | 800x800 | 1:1 | < 1.5 MB | **OWNER-PROVIDED** |
| `og-default` | `og-default.webp` | Global Meta — Open Graph Share Card | webp | 1200x630 | 1.91:1 | < 120 KB | Generated (WebP) |
| `category-earphones-headphones-marquee-poster` | `category-earphones-headphones-marquee-poster.webp` | Category: Earphones & Headphones — Marquee Backdrop Slot | webp | 1920x1080 | 16:9 | < 150 KB | Generated (WebP) |
| `category-earphones-headphones-film` | `category-earphones-headphones-film.mp4` | Category: Earphones & Headphones — Marquee Backdrop Slot | mp4 (H.264, muted) | 1920x1080 | 16:9 | < 2.0 MB | **OWNER-PROVIDED** |
| `category-speakers-marquee-poster` | `category-speakers-marquee-poster.webp` | Category: Acoustics & Speakers — Marquee Backdrop Slot | webp | 1920x1080 | 16:9 | < 150 KB | Generated (WebP) |
| `category-speakers-film` | `category-speakers-film.mp4` | Category: Acoustics & Speakers — Marquee Backdrop Slot | mp4 (H.264, muted) | 1920x1080 | 16:9 | < 2.0 MB | **OWNER-PROVIDED** |
| `category-smartphones-marquee-poster` | `category-smartphones-marquee-poster.webp` | Category: Smartphones & Devices — Marquee Backdrop Slot | webp | 1920x1080 | 16:9 | < 150 KB | Generated (WebP) |
| `category-smartphones-film` | `category-smartphones-film.mp4` | Category: Smartphones & Devices — Marquee Backdrop Slot | mp4 (H.264, muted) | 1920x1080 | 16:9 | < 2.0 MB | **OWNER-PROVIDED** |
| `category-smartwatches-bands-marquee-poster` | `category-smartwatches-bands-marquee-poster.webp` | Category: Smartwatches & Wearables — Marquee Backdrop Slot | webp | 1920x1080 | 16:9 | < 150 KB | Generated (WebP) |
| `category-smartwatches-bands-film` | `category-smartwatches-bands-film.mp4` | Category: Smartwatches & Wearables — Marquee Backdrop Slot | mp4 (H.264, muted) | 1920x1080 | 16:9 | < 2.0 MB | **OWNER-PROVIDED** |
| `category-cameras-marquee-poster` | `category-cameras-marquee-poster.webp` | Category: Cameras & Optics — Marquee Backdrop Slot | webp | 1920x1080 | 16:9 | < 150 KB | Generated (WebP) |
| `category-cameras-film` | `category-cameras-film.mp4` | Category: Cameras & Optics — Marquee Backdrop Slot | mp4 (H.264, muted) | 1920x1080 | 16:9 | < 2.0 MB | **OWNER-PROVIDED** |
| `category-tvs-marquee-poster` | `category-tvs-marquee-poster.webp` | Category: Displays & Televisions — Marquee Backdrop Slot | webp | 1920x1080 | 16:9 | < 150 KB | Generated (WebP) |
| `category-tvs-film` | `category-tvs-film.mp4` | Category: Displays & Televisions — Marquee Backdrop Slot | mp4 (H.264, muted) | 1920x1080 | 16:9 | < 2.0 MB | **OWNER-PROVIDED** |
| `category-keyboards-mice-marquee-poster` | `category-keyboards-mice-marquee-poster.webp` | Category: Keyboards & Pointers — Marquee Backdrop Slot | webp | 1920x1080 | 16:9 | < 150 KB | Generated (WebP) |
| `category-keyboards-mice-film` | `category-keyboards-mice-film.mp4` | Category: Keyboards & Pointers — Marquee Backdrop Slot | mp4 (H.264, muted) | 1920x1080 | 16:9 | < 2.0 MB | **OWNER-PROVIDED** |
| `category-cables-chargers-powerbanks-marquee-poster` | `category-cables-chargers-powerbanks-marquee-poster.webp` | Category: Cables, Chargers & Power — Marquee Backdrop Slot | webp | 1920x1080 | 16:9 | < 150 KB | Generated (WebP) |
| `category-cables-chargers-powerbanks-film` | `category-cables-chargers-powerbanks-film.mp4` | Category: Cables, Chargers & Power — Marquee Backdrop Slot | mp4 (H.264, muted) | 1920x1080 | 16:9 | < 2.0 MB | **OWNER-PROVIDED** |
| `category-cases-protectors-marquee-poster` | `category-cases-protectors-marquee-poster.webp` | Category: Cases & Protectors — Marquee Backdrop Slot | webp | 1920x1080 | 16:9 | < 150 KB | Generated (WebP) |
| `category-cases-protectors-film` | `category-cases-protectors-film.mp4` | Category: Cases & Protectors — Marquee Backdrop Slot | mp4 (H.264, muted) | 1920x1080 | 16:9 | < 2.0 MB | **OWNER-PROVIDED** |
| `category-other-marquee-poster` | `category-other-marquee-poster.webp` | Category: Sundry Electronics — Marquee Backdrop Slot | webp | 1920x1080 | 16:9 | < 150 KB | Generated (WebP) |
| `category-other-film` | `category-other-film.mp4` | Category: Sundry Electronics — Marquee Backdrop Slot | mp4 (H.264, muted) | 1920x1080 | 16:9 | < 2.0 MB | **OWNER-PROVIDED** |
| `home-chapter-1-poster` | `home-chapter-1-poster.webp` | Home — Act 3 Chapter 01 (Earphones & Headphones) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |
| `home-chapter-2-poster` | `home-chapter-2-poster.webp` | Home — Act 3 Chapter 02 (Acoustics & Speakers) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |
| `home-chapter-3-poster` | `home-chapter-3-poster.webp` | Home — Act 3 Chapter 03 (Smartphones & Devices) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |
| `home-chapter-4-poster` | `home-chapter-4-poster.webp` | Home — Act 3 Chapter 04 (Smartwatches & Wearables) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |
| `home-chapter-5-poster` | `home-chapter-5-poster.webp` | Home — Act 3 Chapter 05 (Cameras & Optics) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |
| `home-chapter-6-poster` | `home-chapter-6-poster.webp` | Home — Act 3 Chapter 06 (Displays & Televisions) | webp | 800x800 | 1:1 | < 80 KB | Generated (WebP) |

---

## Slot Specifications & Layout Contracts

### `home-hero-poster`
- **File Path**: `static/media/placeholders/home-hero-poster.webp`
- **Page / Placement**: Home (Act 1 Cover / Hero)
- **Purpose**: Primary exhibition background poster for desktop hero composition.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webp (< 180 KB)
- **Desktop Layout Contract**: Reserved 16:9 aspect ratio behind lead collectible plate.
- **Mobile Layout Contract**: Serves as static backdrop poster for coarse pointer devices.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i hero.mov -vframes 1 -q:v 85 home-hero-poster.webp`

### `home-hero-loop`
- **File Path**: `static/media/video/home-hero-loop.mp4`
- **Page / Placement**: Home (Act 1 Cover / Hero)
- **Purpose**: Cinematic ambient loop of rotating precision hardware.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264, muted) (< 2.5 MB)
- **Desktop Layout Contract**: Tier 1 fine pointer desktop autoplay loop; paused when out of view or tab hidden.
- **Mobile Layout Contract**: Not downloaded on mobile or under save-data / reduced-motion.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i hero_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart -pix_fmt yuv420p static/media/video/home-hero-loop.mp4`

### `home-hero-loop-webm`
- **File Path**: `static/media/video/home-hero-loop.webm`
- **Page / Placement**: Home (Act 1 Cover / Hero)
- **Purpose**: WebM modern codec variant for hero video loop.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webm (VP9, muted) (< 2.0 MB)
- **Desktop Layout Contract**: Secondary source for modern browsers.
- **Mobile Layout Contract**: Not downloaded on mobile.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i hero_raw.mov -c:v libvpx-vp9 -b:v 0 -crf 30 -an static/media/video/home-hero-loop.webm`

### `home-hero-loop-m`
- **File Path**: `static/media/video/home-hero-loop-m.mp4`
- **Page / Placement**: Home (Act 1 Cover / Hero Mobile)
- **Purpose**: Vertical 9:16 video loop variant for high-DPI mobile devices.
- **Dimensions**: 720 × 1280 px (Aspect Ratio: `9:16`)
- **Format & Budget**: mp4 (H.264, muted) (< 1.0 MB)
- **Desktop Layout Contract**: Omitted on desktop.
- **Mobile Layout Contract**: Optional mobile playback under fine Wi-Fi connections.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i hero_vertical.mov -vf 'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280' -c:v libx264 -preset slow -crf 23 -an -movflags +faststart static/media/video/home-hero-loop-m.mp4`

### `hero-model-1`
- **File Path**: `static/media/models/hero-model-1.glb`
- **Page / Placement**: Home (Act 1 Cover / WebGL Plinth)
- **Purpose**: Interactive 3D GLTF turntable asset for desktop pointer tilt.
- **Dimensions**: 0 × 0 px (Aspect Ratio: `1:1`)
- **Format & Budget**: glb (draco compressed) (< 1.8 MB)
- **Desktop Layout Contract**: Lazy-loaded Three.js canvas layer.
- **Mobile Layout Contract**: Completely omitted on mobile devices.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `gltf-pipeline -i raw_model.gltf -o static/media/models/hero-model-1.glb -d`

### `product-secondary-poster`
- **File Path**: `static/media/placeholders/product-secondary-poster.webp`
- **Page / Placement**: Product Detail (Secondary Media Exhibition)
- **Purpose**: Poster for secondary video or hardware teardown slot.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 70 KB)
- **Desktop Layout Contract**: Displays under exhibition frame when video is not playing.
- **Mobile Layout Contract**: Static card fallback on touch devices.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i product_video.mp4 -vframes 1 -q:v 85 product-secondary-poster.webp`

### `product-secondary-video`
- **File Path**: `static/media/video/product-secondary-video.mp4`
- **Page / Placement**: Product Detail (Secondary Media Exhibition)
- **Purpose**: Disassembly or hardware finish rotation video loop.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: mp4 (H.264, muted) (< 1.5 MB)
- **Desktop Layout Contract**: 6s seamless loop attached to ProductMedia records.
- **Mobile Layout Contract**: Hidden on cellular connections.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i product_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/product-secondary-video.mp4`

### `og-default`
- **File Path**: `static/media/placeholders/og-default.webp`
- **Page / Placement**: Global Meta (Open Graph Share Card)
- **Purpose**: Open Graph social preview image for external shares.
- **Dimensions**: 1200 × 630 px (Aspect Ratio: `1.91:1`)
- **Format & Budget**: webp (< 120 KB)
- **Desktop Layout Contract**: Shared in <meta property='og:image'> tag.
- **Mobile Layout Contract**: Shared in social app link cards.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `N/A`

### `category-earphones-headphones-marquee-poster`
- **File Path**: `static/media/placeholders/category-earphones-headphones-marquee-poster.webp`
- **Page / Placement**: Category: Earphones & Headphones (Marquee Backdrop Slot)
- **Purpose**: Atmospheric world backdrop poster for Earphones & Headphones marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webp (< 150 KB)
- **Desktop Layout Contract**: Fills marquee framed slot without competing with typography.
- **Mobile Layout Contract**: Poster fallback.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i earphones-headphones.mov -vframes 1 -q:v 85 category-earphones-headphones-marquee-poster.webp`

### `category-earphones-headphones-film`
- **File Path**: `static/media/video/category-earphones-headphones-film.mp4`
- **Page / Placement**: Category: Earphones & Headphones (Marquee Backdrop Slot)
- **Purpose**: Atmospheric 6-8s video loop for Earphones & Headphones marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264, muted) (< 2.0 MB)
- **Desktop Layout Contract**: Plays on Tier 1 desktop only; pauses when scrolled out of view.
- **Mobile Layout Contract**: Poster only.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i earphones-headphones_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/category-earphones-headphones-film.mp4`

### `category-speakers-marquee-poster`
- **File Path**: `static/media/placeholders/category-speakers-marquee-poster.webp`
- **Page / Placement**: Category: Acoustics & Speakers (Marquee Backdrop Slot)
- **Purpose**: Atmospheric world backdrop poster for Acoustics & Speakers marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webp (< 150 KB)
- **Desktop Layout Contract**: Fills marquee framed slot without competing with typography.
- **Mobile Layout Contract**: Poster fallback.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i speakers.mov -vframes 1 -q:v 85 category-speakers-marquee-poster.webp`

### `category-speakers-film`
- **File Path**: `static/media/video/category-speakers-film.mp4`
- **Page / Placement**: Category: Acoustics & Speakers (Marquee Backdrop Slot)
- **Purpose**: Atmospheric 6-8s video loop for Acoustics & Speakers marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264, muted) (< 2.0 MB)
- **Desktop Layout Contract**: Plays on Tier 1 desktop only; pauses when scrolled out of view.
- **Mobile Layout Contract**: Poster only.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i speakers_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/category-speakers-film.mp4`

### `category-smartphones-marquee-poster`
- **File Path**: `static/media/placeholders/category-smartphones-marquee-poster.webp`
- **Page / Placement**: Category: Smartphones & Devices (Marquee Backdrop Slot)
- **Purpose**: Atmospheric world backdrop poster for Smartphones & Devices marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webp (< 150 KB)
- **Desktop Layout Contract**: Fills marquee framed slot without competing with typography.
- **Mobile Layout Contract**: Poster fallback.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i smartphones.mov -vframes 1 -q:v 85 category-smartphones-marquee-poster.webp`

### `category-smartphones-film`
- **File Path**: `static/media/video/category-smartphones-film.mp4`
- **Page / Placement**: Category: Smartphones & Devices (Marquee Backdrop Slot)
- **Purpose**: Atmospheric 6-8s video loop for Smartphones & Devices marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264, muted) (< 2.0 MB)
- **Desktop Layout Contract**: Plays on Tier 1 desktop only; pauses when scrolled out of view.
- **Mobile Layout Contract**: Poster only.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i smartphones_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/category-smartphones-film.mp4`

### `category-smartwatches-bands-marquee-poster`
- **File Path**: `static/media/placeholders/category-smartwatches-bands-marquee-poster.webp`
- **Page / Placement**: Category: Smartwatches & Wearables (Marquee Backdrop Slot)
- **Purpose**: Atmospheric world backdrop poster for Smartwatches & Wearables marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webp (< 150 KB)
- **Desktop Layout Contract**: Fills marquee framed slot without competing with typography.
- **Mobile Layout Contract**: Poster fallback.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i smartwatches-bands.mov -vframes 1 -q:v 85 category-smartwatches-bands-marquee-poster.webp`

### `category-smartwatches-bands-film`
- **File Path**: `static/media/video/category-smartwatches-bands-film.mp4`
- **Page / Placement**: Category: Smartwatches & Wearables (Marquee Backdrop Slot)
- **Purpose**: Atmospheric 6-8s video loop for Smartwatches & Wearables marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264, muted) (< 2.0 MB)
- **Desktop Layout Contract**: Plays on Tier 1 desktop only; pauses when scrolled out of view.
- **Mobile Layout Contract**: Poster only.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i smartwatches-bands_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/category-smartwatches-bands-film.mp4`

### `category-cameras-marquee-poster`
- **File Path**: `static/media/placeholders/category-cameras-marquee-poster.webp`
- **Page / Placement**: Category: Cameras & Optics (Marquee Backdrop Slot)
- **Purpose**: Atmospheric world backdrop poster for Cameras & Optics marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webp (< 150 KB)
- **Desktop Layout Contract**: Fills marquee framed slot without competing with typography.
- **Mobile Layout Contract**: Poster fallback.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i cameras.mov -vframes 1 -q:v 85 category-cameras-marquee-poster.webp`

### `category-cameras-film`
- **File Path**: `static/media/video/category-cameras-film.mp4`
- **Page / Placement**: Category: Cameras & Optics (Marquee Backdrop Slot)
- **Purpose**: Atmospheric 6-8s video loop for Cameras & Optics marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264, muted) (< 2.0 MB)
- **Desktop Layout Contract**: Plays on Tier 1 desktop only; pauses when scrolled out of view.
- **Mobile Layout Contract**: Poster only.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i cameras_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/category-cameras-film.mp4`

### `category-tvs-marquee-poster`
- **File Path**: `static/media/placeholders/category-tvs-marquee-poster.webp`
- **Page / Placement**: Category: Displays & Televisions (Marquee Backdrop Slot)
- **Purpose**: Atmospheric world backdrop poster for Displays & Televisions marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webp (< 150 KB)
- **Desktop Layout Contract**: Fills marquee framed slot without competing with typography.
- **Mobile Layout Contract**: Poster fallback.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i tvs.mov -vframes 1 -q:v 85 category-tvs-marquee-poster.webp`

### `category-tvs-film`
- **File Path**: `static/media/video/category-tvs-film.mp4`
- **Page / Placement**: Category: Displays & Televisions (Marquee Backdrop Slot)
- **Purpose**: Atmospheric 6-8s video loop for Displays & Televisions marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264, muted) (< 2.0 MB)
- **Desktop Layout Contract**: Plays on Tier 1 desktop only; pauses when scrolled out of view.
- **Mobile Layout Contract**: Poster only.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i tvs_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/category-tvs-film.mp4`

### `category-keyboards-mice-marquee-poster`
- **File Path**: `static/media/placeholders/category-keyboards-mice-marquee-poster.webp`
- **Page / Placement**: Category: Keyboards & Pointers (Marquee Backdrop Slot)
- **Purpose**: Atmospheric world backdrop poster for Keyboards & Pointers marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webp (< 150 KB)
- **Desktop Layout Contract**: Fills marquee framed slot without competing with typography.
- **Mobile Layout Contract**: Poster fallback.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i keyboards-mice.mov -vframes 1 -q:v 85 category-keyboards-mice-marquee-poster.webp`

### `category-keyboards-mice-film`
- **File Path**: `static/media/video/category-keyboards-mice-film.mp4`
- **Page / Placement**: Category: Keyboards & Pointers (Marquee Backdrop Slot)
- **Purpose**: Atmospheric 6-8s video loop for Keyboards & Pointers marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264, muted) (< 2.0 MB)
- **Desktop Layout Contract**: Plays on Tier 1 desktop only; pauses when scrolled out of view.
- **Mobile Layout Contract**: Poster only.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i keyboards-mice_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/category-keyboards-mice-film.mp4`

### `category-cables-chargers-powerbanks-marquee-poster`
- **File Path**: `static/media/placeholders/category-cables-chargers-powerbanks-marquee-poster.webp`
- **Page / Placement**: Category: Cables, Chargers & Power (Marquee Backdrop Slot)
- **Purpose**: Atmospheric world backdrop poster for Cables, Chargers & Power marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webp (< 150 KB)
- **Desktop Layout Contract**: Fills marquee framed slot without competing with typography.
- **Mobile Layout Contract**: Poster fallback.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i cables-chargers-powerbanks.mov -vframes 1 -q:v 85 category-cables-chargers-powerbanks-marquee-poster.webp`

### `category-cables-chargers-powerbanks-film`
- **File Path**: `static/media/video/category-cables-chargers-powerbanks-film.mp4`
- **Page / Placement**: Category: Cables, Chargers & Power (Marquee Backdrop Slot)
- **Purpose**: Atmospheric 6-8s video loop for Cables, Chargers & Power marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264, muted) (< 2.0 MB)
- **Desktop Layout Contract**: Plays on Tier 1 desktop only; pauses when scrolled out of view.
- **Mobile Layout Contract**: Poster only.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i cables-chargers-powerbanks_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/category-cables-chargers-powerbanks-film.mp4`

### `category-cases-protectors-marquee-poster`
- **File Path**: `static/media/placeholders/category-cases-protectors-marquee-poster.webp`
- **Page / Placement**: Category: Cases & Protectors (Marquee Backdrop Slot)
- **Purpose**: Atmospheric world backdrop poster for Cases & Protectors marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webp (< 150 KB)
- **Desktop Layout Contract**: Fills marquee framed slot without competing with typography.
- **Mobile Layout Contract**: Poster fallback.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i cases-protectors.mov -vframes 1 -q:v 85 category-cases-protectors-marquee-poster.webp`

### `category-cases-protectors-film`
- **File Path**: `static/media/video/category-cases-protectors-film.mp4`
- **Page / Placement**: Category: Cases & Protectors (Marquee Backdrop Slot)
- **Purpose**: Atmospheric 6-8s video loop for Cases & Protectors marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264, muted) (< 2.0 MB)
- **Desktop Layout Contract**: Plays on Tier 1 desktop only; pauses when scrolled out of view.
- **Mobile Layout Contract**: Poster only.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i cases-protectors_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/category-cases-protectors-film.mp4`

### `category-other-marquee-poster`
- **File Path**: `static/media/placeholders/category-other-marquee-poster.webp`
- **Page / Placement**: Category: Sundry Electronics (Marquee Backdrop Slot)
- **Purpose**: Atmospheric world backdrop poster for Sundry Electronics marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: webp (< 150 KB)
- **Desktop Layout Contract**: Fills marquee framed slot without competing with typography.
- **Mobile Layout Contract**: Poster fallback.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `ffmpeg -ss 00:00:01 -i other.mov -vframes 1 -q:v 85 category-other-marquee-poster.webp`

### `category-other-film`
- **File Path**: `static/media/video/category-other-film.mp4`
- **Page / Placement**: Category: Sundry Electronics (Marquee Backdrop Slot)
- **Purpose**: Atmospheric 6-8s video loop for Sundry Electronics marquee.
- **Dimensions**: 1920 × 1080 px (Aspect Ratio: `16:9`)
- **Format & Budget**: mp4 (H.264, muted) (< 2.0 MB)
- **Desktop Layout Contract**: Plays on Tier 1 desktop only; pauses when scrolled out of view.
- **Mobile Layout Contract**: Poster only.
- **Handover Requirement**: Requires production asset from site owner.
- **Owner Encoding Command**: `ffmpeg -i other_raw.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart static/media/video/category-other-film.mp4`

### `home-chapter-1-poster`
- **File Path**: `static/media/placeholders/home-chapter-1-poster.webp`
- **Page / Placement**: Home (Act 3 Chapter 01 (Earphones & Headphones))
- **Purpose**: Stage backdrop plate for Chapter 01.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Subtle architectural plate backing the collectible stage.
- **Mobile Layout Contract**: Mobile snap card plate.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `N/A`

### `home-chapter-2-poster`
- **File Path**: `static/media/placeholders/home-chapter-2-poster.webp`
- **Page / Placement**: Home (Act 3 Chapter 02 (Acoustics & Speakers))
- **Purpose**: Stage backdrop plate for Chapter 02.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Subtle architectural plate backing the collectible stage.
- **Mobile Layout Contract**: Mobile snap card plate.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `N/A`

### `home-chapter-3-poster`
- **File Path**: `static/media/placeholders/home-chapter-3-poster.webp`
- **Page / Placement**: Home (Act 3 Chapter 03 (Smartphones & Devices))
- **Purpose**: Stage backdrop plate for Chapter 03.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Subtle architectural plate backing the collectible stage.
- **Mobile Layout Contract**: Mobile snap card plate.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `N/A`

### `home-chapter-4-poster`
- **File Path**: `static/media/placeholders/home-chapter-4-poster.webp`
- **Page / Placement**: Home (Act 3 Chapter 04 (Smartwatches & Wearables))
- **Purpose**: Stage backdrop plate for Chapter 04.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Subtle architectural plate backing the collectible stage.
- **Mobile Layout Contract**: Mobile snap card plate.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `N/A`

### `home-chapter-5-poster`
- **File Path**: `static/media/placeholders/home-chapter-5-poster.webp`
- **Page / Placement**: Home (Act 3 Chapter 05 (Cameras & Optics))
- **Purpose**: Stage backdrop plate for Chapter 05.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Subtle architectural plate backing the collectible stage.
- **Mobile Layout Contract**: Mobile snap card plate.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `N/A`

### `home-chapter-6-poster`
- **File Path**: `static/media/placeholders/home-chapter-6-poster.webp`
- **Page / Placement**: Home (Act 3 Chapter 06 (Displays & Televisions))
- **Purpose**: Stage backdrop plate for Chapter 06.
- **Dimensions**: 800 × 800 px (Aspect Ratio: `1:1`)
- **Format & Budget**: webp (< 80 KB)
- **Desktop Layout Contract**: Subtle architectural plate backing the collectible stage.
- **Mobile Layout Contract**: Mobile snap card plate.
- **Handover Requirement**: Generated locally as neutral WebP calibration poster.
- **Owner Encoding Command**: `N/A`

---

## Owner Video Encoding Standard (ffmpeg Reference)

### 1. Seamless MP4 Loops (1080p, H.264, Muted, Faststart)
```bash
ffmpeg -i input_master.mov -c:v libx264 -preset slow -crf 22 -an -movflags +faststart -pix_fmt yuv420p output.mp4
```

### 2. Modern WebM Loop (VP9, Muted)
```bash
ffmpeg -i input_master.mov -c:v libvpx-vp9 -b:v 0 -crf 30 -an output.webm
```

### 3. Mobile Vertical Variant (720x1280 9:16)
```bash
ffmpeg -i input_master.mov -vf "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280" -c:v libx264 -preset slow -crf 23 -an -movflags +faststart output.mp4
```

### 4. Poster Extraction from Video Frame
```bash
ffmpeg -ss 00:00:01 -i input.mp4 -vframes 1 -q:v 85 poster.webp
```
