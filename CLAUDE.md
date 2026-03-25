# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QR Contact Generator — a single-file web app that generates business-card-style QR codes (vCard 3.0) entirely client-side. No build step, no server, no dependencies beyond a CDN-loaded QR library.

## Development

Open `index.html` directly in a browser. There is no build system, bundler, or dev server. The entire app (HTML, CSS, JS) lives in one file.

The only external dependency is `qrcode-generator` loaded via CDN (`<script>` tag). Everything else is vanilla JS using Canvas API.

## Architecture

`index.html` (~1200 lines) is structured in three sections, top to bottom:

1. **`<head>`** (lines 1–485): Meta/SEO tags, then all CSS in a single `<style>` block. CSS uses custom properties (`:root` vars) for theming.
2. **`<body>` HTML** (lines 487–685): Two-column grid layout — left column is the form (contact fields, pattern picker, color/shadow/logo options), right column is the live preview + download button.
3. **`<script>`** (lines 686–1208): All application logic:
   - Constants (`BOX_SIZE`, `BORDER`, `FONT_FAMILY`) and DOM refs
   - Logo upload handling (drag & drop + file input)
   - Pattern selection (7 styles: standard, rounded, diamond, dots, star, smooth, horizontal)
   - Debounced auto-regeneration on any input change (300ms)
   - `generateVCard()` — builds vCard 3.0 string with proper escaping
   - `createQRMatrix()` — wraps qrcode-generator library
   - `drawQRWithPattern()` — renders QR modules to canvas using selected pattern
   - `applyColorGradient()` — pixel-level diagonal gradient via ImageData
   - `addShadow()` — optional drop shadow on a padded canvas
   - `addLogoToCanvas()` — centers a logo image over the QR code
   - `renderBusinessCard()` — composites QR + contact details into a card layout canvas
   - `generateQRCode()` — main pipeline orchestrating all the above
   - `downloadQRCode()` — exports canvas as PNG blob

## Key Conventions

- Bilingual project (German/English/Italian in README, English in code and UI)
- All rendering is canvas-based — no DOM-based QR output
- vCard field escaping uses backslash notation per RFC 6350
- Name field is required; all others are optional
- The business card layout is fixed-width (440px details panel) with text ellipsis overflow
