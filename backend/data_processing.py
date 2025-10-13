# backend/data_processing.py

import random

# --- Signature Database ---
# This dictionary holds the byte strings we'll search for.
SIGNATURES = {
    b'AES': {'primitive': 'AES', 'type': 'Symmetric Cipher'},
    b'RSA': {'primitive': 'RSA', 'type': 'Asymmetric Cipher'},
    b'SHA256': {'primitive': 'SHA-256', 'type': 'Hash Function'},
    b'OpenSSL': {'primitive': 'OpenSSL Library', 'type': 'Library'},
    b'mbed TLS': {'primitive': 'mbedTLS Library', 'type': 'Library'},
    b'libgcrypt': {'primitive': 'Libgcrypt Library', 'type': 'Library'},
    b'MD5': {'primitive': 'MD5', 'type': 'Hash Function'}, # Added for vulnerability check
}


def analyze_firmware_by_signature(file_content):
    """
    Scans the provided file content for known cryptographic signatures.

    Args:
        file_content (bytes): The raw byte content of the firmware file.

    Returns:
        list: A list of dictionaries, where each dictionary is a finding.
    """
    findings = []
    
    print("Starting signature scan...")
    # Scan the content for each signature in our database
    for signature, details in SIGNATURES.items():
        if signature in file_content:
            print(f"  [+] Signature found: {signature.decode()}")
            
            # Simulate finding a location (memory address)
            location = f"0x{random.randint(0x10000, 0x800000):08X}"
            
            # Simulate a confidence score
            confidence = round(random.uniform(85.0, 99.9), 1)

            # Check for known weak algorithms
            note = ""
            if details['primitive'] == 'MD5':
                note = "Weak Algorithm"

            findings.append({
                "location": location,
                "primitive": details['primitive'],
                "confidence": confidence,
                "notes": note
            })
            
    print(f"Scan complete. Found {len(findings)} signatures.")
    return findings