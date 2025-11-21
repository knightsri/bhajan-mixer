#!/usr/bin/env python3
"""
Simple Flask proxy to get MP3 files from public Google Drive folders
without requiring API keys. Scrapes the folder HTML to extract file IDs.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import re
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for browser requests

@app.route('/api/drive-files/<folder_id>')
def get_drive_files(folder_id):
    """
    Fetch files from a public Google Drive folder by scraping the HTML.
    Returns JSON array of files with id, name, and download URL.
    """
    try:
        # Fetch the public folder page
        url = f'https://drive.google.com/drive/folders/{folder_id}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        html = response.text

        # Extract file data from the HTML
        # Google Drive embeds file info in JavaScript data structures
        files = []

        # Try multiple patterns to extract file information
        # Pattern 1: Look for file entries in the format ["fileId","filename.mp3",...]
        pattern1 = r'\["([a-zA-Z0-9_-]{25,})","([^"]*\.mp3[^"]*)"'
        matches1 = re.findall(pattern1, html, re.IGNORECASE)

        for file_id, filename in matches1:
            # Clean up the filename
            clean_name = filename.replace('.mp3', '').replace('.MP3', '')

            files.append({
                'id': file_id,
                'name': clean_name,
                'url': f'https://drive.google.com/uc?export=download&id={file_id}'
            })

        # Remove duplicates (same file ID)
        seen_ids = set()
        unique_files = []
        for file in files:
            if file['id'] not in seen_ids:
                seen_ids.add(file['id'])
                unique_files.append(file)

        if not unique_files:
            return jsonify({
                'error': 'No MP3 files found in this folder',
                'folder_id': folder_id,
                'help': 'Make sure the folder is publicly accessible and contains MP3 files'
            }), 404

        return jsonify(unique_files)

    except requests.RequestException as e:
        return jsonify({
            'error': 'Failed to fetch folder',
            'message': str(e),
            'folder_id': folder_id
        }), 500
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'drive-proxy'})

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'service': 'Google Drive Folder Proxy',
        'version': '1.0',
        'endpoints': {
            '/api/drive-files/<folder_id>': 'Get MP3 files from a public Drive folder',
            '/api/health': 'Health check'
        },
        'usage': 'GET /api/drive-files/YOUR_FOLDER_ID',
        'note': 'Folder must be publicly accessible'
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
