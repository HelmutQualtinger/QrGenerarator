const generateBtn = document.getElementById('generateBtn');
const downloadBtn = document.getElementById('downloadBtn');
const previewContainer = document.getElementById('previewContainer');
const loadingIndicator = document.getElementById('loadingIndicator');
const colorTransitionCheckbox = document.getElementById('colorTransition');
const colorOptions = document.getElementById('colorOptions');

// Form inputs
const nameInput = document.getElementById('name');
const emailInput = document.getElementById('email');
const phoneInput = document.getElementById('phone');
const organizationInput = document.getElementById('organization');
const urlInput = document.getElementById('url');
const addressInput = document.getElementById('address');
const errorCorrectionSelect = document.getElementById('errorCorrection');
const darkColorInput = document.getElementById('darkColor');
const lightColorInput = document.getElementById('lightColor');
const shadowEnabledCheckbox = document.getElementById('shadowEnabled');
const patternStyleSelect = document.getElementById('patternStyle');

let currentQRData = null;

// Toggle color options visibility
colorTransitionCheckbox.addEventListener('change', (e) => {
    colorOptions.style.display = e.target.checked ? 'block' : 'none';
});

// Generate QR code
generateBtn.addEventListener('click', generateQRCode);

// Download QR code
downloadBtn.addEventListener('click', downloadQRCode);

// Auto-generate on input change (debounced)
let debounceTimer;
const formInputs = [nameInput, emailInput, phoneInput, organizationInput, urlInput, addressInput, patternStyleSelect, errorCorrectionSelect, darkColorInput, lightColorInput, shadowEnabledCheckbox, colorTransitionCheckbox];

formInputs.forEach(input => {
    input.addEventListener('change', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(generateQRCode, 500);
    });
});

async function generateQRCode() {
    const name = nameInput.value.trim();

    if (!name) {
        showPreviewPlaceholder();
        downloadBtn.disabled = true;
        return;
    }

    const formData = {
        name: name,
        email: emailInput.value.trim(),
        phone: phoneInput.value.trim(),
        organization: organizationInput.value.trim(),
        url: urlInput.value.trim(),
        address: addressInput.value.trim(),
        patternStyle: patternStyleSelect.value,
        errorCorrection: errorCorrectionSelect.value,
        shadowEnabled: shadowEnabledCheckbox.checked,
        colorTransition: colorTransitionCheckbox.checked,
        darkColor: darkColorInput.value.replace('#', ''),
        lightColor: lightColorInput.value.replace('#', ''),
    };

    // Show loading
    loadingIndicator.style.display = 'flex';
    previewContainer.innerHTML = '';

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });

        if (!response.ok) {
            throw new Error('Failed to generate QR code');
        }

        const result = await response.json();

        if (result.success) {
            currentQRData = formData;
            displayQRCode(result.image);
            downloadBtn.disabled = false;
        } else {
            showError(result.error);
            downloadBtn.disabled = true;
        }
    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
        downloadBtn.disabled = true;
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

function displayQRCode(imageDataUrl) {
    previewContainer.innerHTML = '';
    const img = document.createElement('img');
    img.id = 'previewImage';
    img.src = imageDataUrl;
    img.alt = 'Generated QR Code';
    previewContainer.appendChild(img);
}

function showPreviewPlaceholder() {
    previewContainer.innerHTML = `
        <div class="preview-placeholder">
            <p>Fill in the form and click "Generate QR Code" to see the preview</p>
        </div>
    `;
}

function showError(message) {
    previewContainer.innerHTML = `
        <div class="preview-placeholder">
            <p style="color: #ef4444;">❌ Error: ${message}</p>
        </div>
    `;
}

async function downloadQRCode() {
    if (!currentQRData) return;

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentQRData),
        });

        if (!response.ok) {
            throw new Error('Failed to download QR code');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentQRData.name.replace(/\s+/g, '_')}_contact.png`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Download error:', error);
        alert('Failed to download QR code');
    }
}

// Initialize preview placeholder
showPreviewPlaceholder();
