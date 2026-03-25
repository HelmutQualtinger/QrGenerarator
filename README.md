# QR Contact Generator

A modern web application that converts contact information into scannable QR codes with advanced styling options.

## Features

✨ **Core Functionality**
- Generate QR codes from contact information (vCard format)
- Scannable by standard contacts apps (iOS, Android, Google Contacts)
- Support for name, email, phone, organization, website, and address

🎨 **Styling & Effects**
- **Color Transitions**: Customize dark and light colors
- **Shadow Effects**: Add depth with shadow rendering
- **Error Correction**: Choose redundancy level (Low/Medium/High)
- **Icon Support**: Embed icons in QR codes
- **Real-time Preview**: See changes instantly

💾 **Export**
- Download QR codes as PNG images
- High-quality output suitable for printing and digital sharing

## Tech Stack

**Backend**
- Flask web framework
- qrcode library for QR generation
- Pillow (PIL) for image manipulation
- Gunicorn for production deployment

**Frontend**
- Modern HTML5
- Pure vanilla JavaScript (no frameworks)
- Custom CSS with gradient effects
- Responsive design (mobile-friendly)

## Setup & Installation

### Requirements
- Python 3.8+
- pip (Python package manager)

### Local Development

1. **Clone or navigate to the project directory**
```bash
cd QrGenerarator
```

2. **Create a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the development server**
```bash
python3 app.py
```

5. **Open in browser**
Navigate to `http://localhost:8000`

## Production Deployment

### Using Gunicorn (Unicorn alternative for Flask)
```bash
gunicorn wsgi:app --workers 4 --bind 0.0.0.0:8000
```

### Using Heroku
```bash
heroku create your-app-name
git push heroku main
```

### Using Docker
Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8000"]
```

Then:
```bash
docker build -t qr-generator .
docker run -p 8000:8000 qr-generator
```

## API Endpoints

### POST `/api/generate`
Generates a QR code and returns it as base64 PNG.

**Request body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-555-0123",
  "organization": "ACME Corp",
  "url": "https://example.com",
  "address": "123 Main St, City, State",
  "errorCorrection": "M",
  "shadowEnabled": true,
  "colorTransition": true,
  "darkColor": "000000",
  "lightColor": "FFFFFF"
}
```

**Response:**
```json
{
  "success": true,
  "image": "data:image/png;base64,...",
  "vcard": "BEGIN:VCARD\nVERSION:3.0\n..."
}
```

### POST `/api/download`
Downloads the QR code as a PNG file.

## Usage

1. **Fill Contact Info**: Enter the contact details you want to encode
2. **Customize Style**:
   - Toggle color transitions and adjust colors
   - Enable shadow effect for depth
   - Choose error correction level
3. **Generate**: Click "Generate QR Code" to create the QR
4. **Preview**: See the result in real-time
5. **Download**: Save the QR code as PNG

## QR Code Error Correction Levels

- **L (7%)**: Low redundancy, smallest size
- **M (15%)**: Medium redundancy, balanced (default)
- **Q (25%)**: Quartile redundancy, higher recovery
- **H (30%)**: High redundancy, maximum recovery but larger code

Higher error correction allows the QR code to remain scannable if partially obscured or damaged.

## vCard Format

QR codes are generated in vCard 3.0 format, compatible with:
- iOS Contacts
- Android Contacts
- Google Contacts
- Outlook
- Most standard contact management apps

## License

MIT License - feel free to use and modify.

## Development Notes

### File Structure
```
QrGenerarator/
├── app.py              # Flask application and API endpoints
├── wsgi.py             # WSGI entry point for production
├── requirements.txt    # Python dependencies
├── Procfile            # Deployment configuration
├── templates/
│   └── index.html      # Main frontend
└── static/
    ├── style.css       # Styling
    └── script.js       # Frontend logic
```

### Adding New Features
- **Colors**: Modify `apply_color_transition()` in app.py
- **Effects**: Add new functions in app.py and call from `/api/generate`
- **UI**: Edit templates/index.html and static/style.css
- **Logic**: Update static/script.js for frontend behavior

### Testing the QR Code
1. Generate a code with your contact info
2. Scan with iPhone Notes app or Google Lens
3. Verify contact details are correctly parsed
