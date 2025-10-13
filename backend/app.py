# backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS

# Import our custom analysis function from the other file
from data_processing import analyze_firmware_by_signature

app = Flask(__name__)
CORS(app)

print("Kryptospect analysis engine is ready.")


@app.route('/analyze', methods=['POST'])
def analyze_firmware():
    if 'firmwareFile' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['firmwareFile']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    print(f"Received file for analysis: {file.filename}")

    # Read the file content
    file_content = file.read()
    
    # Call our analysis function from the data_processing module
    findings = analyze_firmware_by_signature(file_content)

    # Calculate summary stats from the findings
    vulnerability_count = sum(1 for f in findings if f['notes'])
    high_confidence_count = sum(1 for f in findings if f['confidence'] > 95.0)

    # Format the final results for the frontend
    final_results = {
        "fileName": file.filename,
        "functionsFound": len(findings),
        "highConfidence": high_confidence_count,
        "vulnerabilities": vulnerability_count,
        "findings": findings
    }
    
    if not findings:
         final_results['findings'].append({
            "location": "N/A",
            "primitive": "No known crypto signatures found.",
            "confidence": 100.0,
            "notes": ""
        })

    return jsonify(final_results)


if __name__ == '__main__':
    app.run(debug=True, port=5000)