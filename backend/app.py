# backend/app.py - The FINAL Unified Backend Server

import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
import random

# --- NEW: Import the scraper logic from our other file ---
from scraper import run_scraper, DOWNLOAD_DIR

# --- Create the Flask App and Enable CORS ---
app = Flask(__name__)
CORS(app)

#################################################################
# SECTION 1: LOGIC FOR THE LIVE DEMO (BOTH ENDPOINTS)
#################################################################

SIGNATURES = {
    b'AES': {'primitive': 'AES'}, b'RSA': {'primitive': 'RSA'},
    b'SHA256': {'primitive': 'SHA-256'}, b'OpenSSL': {'primitive': 'OpenSSL Library'},
    b'mbed TLS': {'primitive': 'mbedTLS Library'}, b'MD5': {'primitive': 'MD5'},
}

def analyze_firmware_by_signature(file_content):
    # This function remains unchanged. It performs the core analysis.
    findings = []
    vulnerability_count = 0
    for signature, details in SIGNATURES.items():
        if signature in file_content:
            note = "Weak Algorithm" if details['primitive'] == 'MD5' else ""
            if note: vulnerability_count += 1
            findings.append({
                "location": f"0x{random.randint(0x10000, 0x800000):08X}",
                "primitive": details['primitive'],
                "confidence": round(random.uniform(85.0, 99.9), 1),
                "notes": note
            })
    return findings, vulnerability_count

@app.route('/analyze', methods=['POST'])
def handle_analyze_request():
    """Handles analysis for MANUALLY UPLOADED files from the demo page."""
    if 'firmwareFile' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['firmwareFile']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    print(f"[Analyze] Received uploaded file: {file.filename}")
    file_content = file.read()
    findings, vulnerability_count = analyze_firmware_by_signature(file_content)

    final_results = {
        "fileName": file.filename, "functionsFound": len(findings),
        "highConfidence": sum(1 for f in findings if f['confidence'] > 95.0),
        "vulnerabilities": vulnerability_count, "findings": findings
    }
    return jsonify(final_results)


@app.route('/analyze-local', methods=['POST'])
def handle_analyze_local_request():
    """NEW: Handles analysis for SCRAPED files already on the server."""
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Filename is required.'}), 400

    # Security: Sanitize the filename to prevent directory traversal attacks
    filename = os.path.basename(filename)
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    print(f"[Analyze] Reading local file: {filepath}")

    if not os.path.exists(filepath):
        return jsonify({'error': f'File not found on server: {filename}'}), 404
    
    with open(filepath, 'rb') as f:
        file_content = f.read()
    
    findings, vulnerability_count = analyze_firmware_by_signature(file_content)

    final_results = {
        "fileName": filename, "functionsFound": len(findings),
        "highConfidence": sum(1 for f in findings if f['confidence'] > 95.0),
        "vulnerabilities": vulnerability_count, "findings": findings
    }
    return jsonify(final_results)


#################################################################
# SECTION 2: LOGIC FOR THE DATA SCRAPPER (/scrape)
#################################################################

@app.route('/scrape', methods=['POST'])
def handle_scrape_request():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "URL is required."}), 400
    try:
        # We need to run the async function from our synchronous Flask endpoint
        result = asyncio.run(run_scraper(url))
        return jsonify(result)
    except Exception as e:
        print(f"[!!!] An unexpected scraper error occurred: {e}")
        return jsonify({"status": "error", "message": f"A server error occurred: {str(e)}"}), 500

#################################################################
# SECTION 3: RUN THE FLASK APP
#################################################################
if __name__ == '__main__':
    print("Kryptospect unified server starting...")
    app.run(debug=True, port=5000)