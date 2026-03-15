#!/usr/bin/env python
"""Test PDF generation in all three languages"""
import requests
import sys
import re

# Test if server is running
try:
    # Scan returns HTML, extract domain from result.html after scan
    r = requests.post('http://localhost:8000/scan', data={'domain': 'google.com'}, timeout=60)
    if r.status_code != 200:
        print(f"Scan failed: {r.status_code}")
        sys.exit(1)
    
    # Extract risk_score from HTML response
    risk_score_match = re.search(r'Risk Score.*?(\d+)\s*/\s*100', r.text)
    risk_label_match = re.search(r'Risk Indicator.*?<span[^>]*>([^<]+)</span>', r.text)
    
    print(f"✓ Scan completed")
    if risk_score_match:
        print(f"  Risk Score: {risk_score_match.group(1)}")
    if risk_label_match:
        print(f"  Risk Label: {risk_label_match.group(1)}")
    print()
    
    # Test PDF exports in all languages
    for lang, lang_name in [("en", "English"), ("az", "Azərbaycanca"), ("ru", "Русский")]:
        r = requests.post('http://localhost:8000/export-pdf', 
                         data={'domain': 'google.com', 'export_lang': lang}, 
                         timeout=30)
        if r.status_code == 200 and r.headers.get('content-type') == 'application/pdf':
            print(f"✓ PDF Export ({lang_name}): {len(r.content)} bytes")
        else:
            print(f"✗ PDF Export ({lang_name}): Failed ({r.status_code})")
            print(f"  Response: {r.text[:200] if r.headers.get('content-type') != 'application/pdf' else 'PDF corrupted'}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
