from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import qrcode
import io
import base64
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

def generate_contact_vcard(contact):
    """Generate vCard format from contact info"""
    vcard = "BEGIN:VCARD\nVERSION:3.0\n"

    if contact.get('name'):
        # Format: LASTNAME;FIRSTNAME
        parts = contact['name'].split(' ', 1)
        if len(parts) == 2:
            vcard += f"N:{parts[1]};{parts[0]};;;\n"
        else:
            vcard += f"N:{parts[0]};;;;\n"
        vcard += f"FN:{contact['name']}\n"

    if contact.get('phone'):
        vcard += f"TEL:{contact['phone']}\n"

    if contact.get('email'):
        vcard += f"EMAIL:{contact['email']}\n"

    if contact.get('organization'):
        vcard += f"ORG:{contact['organization']}\n"

    if contact.get('url'):
        vcard += f"URL:{contact['url']}\n"

    if contact.get('address'):
        vcard += f"ADR:;;{contact['address']};;;;\n"

    vcard += "END:VCARD"
    return vcard

def create_qr_code(data, error_correction, transparent=False):
    """Create QR code from data"""
    error_levels = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'H': qrcode.constants.ERROR_CORRECT_H,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
    }

    qr = qrcode.QRCode(
        version=1,
        error_correction=error_levels.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    if transparent:
        # Create RGBA image with transparent background
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
        # Make white background transparent
        data = qr_img.getdata()
        new_data = []
        for item in data:
            if item[:3] == (255, 255, 255):  # If white
                new_data.append((255, 255, 255, 0))  # Make transparent
            else:
                new_data.append(item)
        qr_img.putdata(new_data)
        return qr_img
    else:
        return qr.make_image(fill_color="black", back_color="white")

def add_shadow(img, offset=6, blur=8, opacity=120):
    """Add a strong drop shadow under a transparent QR code."""
    if img.mode != 'RGBA':
        qr = img.convert('RGBA')
    else:
        qr = img.copy()

    pad = offset + blur * 2
    canvas_w = qr.size[0] + pad * 2
    canvas_h = qr.size[1] + pad * 2

    # Build shadow from the QR alpha channel
    alpha = qr.split()[3]  # extract alpha
    # Create a solid-black image masked by the QR's alpha, but at higher opacity
    shadow_base = Image.new('RGBA', qr.size, (0, 0, 0, 0))
    shadow_alpha = alpha.point(lambda p: opacity if p > 0 else 0)
    shadow_base.putalpha(shadow_alpha)

    # Place shadow on canvas with offset
    shadow_canvas = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    shadow_canvas.paste(shadow_base, (pad + offset, pad + offset), shadow_base)

    # Heavy blur for soft spread
    shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(radius=blur))

    # Place QR on top (no offset — shadow peeks out below/right)
    shadow_canvas.paste(qr, (pad, pad), qr)

    return shadow_canvas

def apply_pattern_style(img, pattern_style):
    """Apply different pattern styles to QR code, preserving transparency."""
    if pattern_style == 'standard':
        return img

    # Work on an RGB copy to read which pixels are dark
    src = img.convert('RGB')
    src_px = src.load()
    width, height = src.size

    # Build result as RGBA — dark pixels opaque, light pixels transparent
    is_transparent = (img.mode == 'RGBA')
    result = Image.new('RGBA', (width, height), (255, 255, 255, 0 if is_transparent else 255))
    rpx = result.load()

    dark = (0, 0, 0, 255)
    light = (255, 255, 255, 0 if is_transparent else 255)
    box_size = 10

    for by in range(0, height, box_size):
        for bx in range(0, width, box_size):
            cx, cy = bx + box_size // 2, by + box_size // 2
            if cx >= width or cy >= height:
                continue
            is_dark = src_px[cx, cy][0] < 128

            for dy in range(box_size):
                for dx in range(box_size):
                    px, py = bx + dx, by + dy
                    if px >= width or py >= height:
                        continue

                    fill = False
                    if is_dark:
                        if pattern_style == 'rounded':
                            dist = ((dx - box_size // 2) ** 2 + (dy - box_size // 2) ** 2) ** 0.5
                            fill = dist <= box_size // 2 - 1
                        elif pattern_style == 'diamond':
                            dist = abs(dx - box_size // 2) + abs(dy - box_size // 2)
                            fill = dist <= box_size // 2 - 1
                        elif pattern_style == 'dots':
                            fill = (3 <= dx <= 6 and 3 <= dy <= 6)

                    rpx[px, py] = dark if fill else light

    if not is_transparent:
        return result.convert('RGB')
    return result

def apply_color_transition(img, color1, color2):
    """Apply color transition from color1 (dark) to color2 (light)"""
    img_rgb = img.convert('RGB')
    pixels = img_rgb.load()

    # Parse hex colors
    c1 = tuple(int(color1[i:i+2], 16) for i in (0, 2, 4))
    c2 = tuple(int(color2[i:i+2], 16) for i in (0, 2, 4))

    for y in range(img_rgb.size[1]):
        for x in range(img_rgb.size[0]):
            r, g, b = pixels[x, y]
            # White pixels become color2, black become color1
            if r > 128:  # Light pixel
                pixels[x, y] = c2
            else:  # Dark pixel
                pixels[x, y] = c1

    return img_rgb

def _load_font(size):
    """Try to load a nice font, fall back gracefully."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSText.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


def add_contact_name(img, name, organization=''):
    """Add a styled banner with the contact name (and org) below the QR code."""
    if not name:
        return img

    # Flatten to RGBA so we can composite nicely
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    qr_w, qr_h = img.size

    # Fonts
    name_font = _load_font(28)
    org_font = _load_font(18)

    # Measure text
    tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    name_bbox = tmp.textbbox((0, 0), name, font=name_font)
    name_tw = name_bbox[2] - name_bbox[0]
    name_th = name_bbox[3] - name_bbox[1]

    org_th = 0
    if organization:
        org_bbox = tmp.textbbox((0, 0), organization, font=org_font)
        org_tw = org_bbox[2] - org_bbox[0]
        org_th = org_bbox[3] - org_bbox[1]

    # Banner dimensions
    banner_h = 30 + name_th + (org_th + 6 if organization else 0) + 30
    spacing = 16  # gap between QR and banner
    banner_w = qr_w

    # Build banner with rounded-rect background and gradient
    banner = Image.new('RGBA', (banner_w, banner_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(banner)

    # Draw rounded rectangle pill
    r = 16
    fill_color = (40, 40, 60, 220)
    draw.rounded_rectangle([(0, 0), (banner_w - 1, banner_h - 1)], radius=r, fill=fill_color)

    # Subtle highlight line at top
    draw.rounded_rectangle([(2, 2), (banner_w - 3, 4)], radius=2, fill=(255, 255, 255, 35))

    # Draw name (centered, white)
    name_x = (banner_w - name_tw) // 2
    name_y = 24
    draw.text((name_x, name_y), name, fill=(255, 255, 255, 255), font=name_font)

    # Draw organization (centered, lighter)
    if organization:
        org_x = (banner_w - org_tw) // 2
        org_y = name_y + name_th + 6
        draw.text((org_x, org_y), organization, fill=(180, 180, 210, 255), font=org_font)

    # Compose final image: QR + spacing + banner
    final_h = qr_h + spacing + banner_h
    final = Image.new('RGBA', (qr_w, final_h), (0, 0, 0, 0))
    final.paste(img, (0, 0), img)
    final.paste(banner, (0, qr_h + spacing), banner)

    return final

def add_icon_to_qr(qr_img, icon_path, icon_size_ratio=0.2):
    """Add icon to center of QR code"""
    try:
        icon = Image.open(icon_path).convert('RGBA')

        # Calculate icon size
        qr_width = qr_img.size[0]
        icon_final_size = int(qr_width * icon_size_ratio)
        icon = icon.resize((icon_final_size, icon_final_size), Image.Resampling.LANCZOS)

        # Create white background for icon
        icon_bg = Image.new('RGB', (icon_final_size + 10, icon_final_size + 10), 'white')
        icon_bg.paste(icon, (5, 5), icon)

        # Paste on center of QR
        qr_result = qr_img.convert('RGB')
        offset = ((qr_result.size[0] - icon_final_size) // 2, (qr_result.size[1] - icon_final_size) // 2)
        qr_result.paste(icon_bg, offset)

        return qr_result
    except:
        return qr_img

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_qr():
    try:
        data = request.json

        contact = {
            'name': data.get('name', ''),
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'organization': data.get('organization', ''),
            'url': data.get('url', ''),
            'address': data.get('address', ''),
        }

        # Generate vCard
        vcard = generate_contact_vcard(contact)

        # Create QR code with transparency if shadow is enabled
        error_correction = data.get('errorCorrection', 'M')
        shadow_enabled = data.get('shadowEnabled', False)
        qr_img = create_qr_code(vcard, error_correction, transparent=shadow_enabled)

        # Apply pattern style
        pattern_style = data.get('patternStyle', 'standard')
        qr_img = apply_pattern_style(qr_img, pattern_style)

        # Apply effects
        if shadow_enabled:
            qr_img = add_shadow(qr_img, offset=6, blur=8, opacity=120)

        if data.get('colorTransition'):
            color1 = data.get('darkColor', '000000')
            color2 = data.get('lightColor', 'FFFFFF')
            qr_img = apply_color_transition(qr_img, color1, color2)

        if data.get('iconUrl') and data['iconUrl'].startswith('data:'):
            # Handle base64 icon
            try:
                icon_data = data['iconUrl'].split(',')[1]
                icon_bytes = base64.b64decode(icon_data)
                icon_file = io.BytesIO(icon_bytes)
                qr_img = add_icon_to_qr(qr_img, icon_file, icon_size_ratio=0.15)
            except:
                pass

        # Add contact name below QR code
        qr_img = add_contact_name(qr_img, contact.get('name', ''), contact.get('organization', ''))

        # Convert to base64
        img_io = io.BytesIO()
        qr_img.save(img_io, format='PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode()

        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}',
            'vcard': vcard
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/download', methods=['POST'])
def download_qr():
    try:
        data = request.json

        contact = {
            'name': data.get('name', ''),
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'organization': data.get('organization', ''),
            'url': data.get('url', ''),
            'address': data.get('address', ''),
        }

        vcard = generate_contact_vcard(contact)
        error_correction = data.get('errorCorrection', 'M')
        shadow_enabled = data.get('shadowEnabled', False)
        qr_img = create_qr_code(vcard, error_correction, transparent=shadow_enabled)

        # Apply pattern style
        pattern_style = data.get('patternStyle', 'standard')
        qr_img = apply_pattern_style(qr_img, pattern_style)

        if shadow_enabled:
            qr_img = add_shadow(qr_img, offset=6, blur=8, opacity=120)

        if data.get('colorTransition'):
            color1 = data.get('darkColor', '000000')
            color2 = data.get('lightColor', 'FFFFFF')
            qr_img = apply_color_transition(qr_img, color1, color2)

        # Add contact name below QR code
        qr_img = add_contact_name(qr_img, contact.get('name', ''), contact.get('organization', ''))

        # Save to bytes
        img_io = io.BytesIO()
        qr_img.save(img_io, format='PNG')
        img_io.seek(0)

        filename = f"{contact.get('name', 'contact').replace(' ', '_')}_contact.png"
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=8000)