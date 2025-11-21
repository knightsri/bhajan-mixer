#!/usr/bin/env python3
"""
Simple Flask server to serve the player and proxy Google Drive folder requests.
Scrapes public Google Drive folders to extract MP3 file IDs without requiring API keys.
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import requests
import re
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for browser requests

# Get the directory where this script is located
UTILITIES_DIR = os.path.dirname(os.path.abspath(__file__))

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
    """Serve the player HTML"""
    return send_file(os.path.join(UTILITIES_DIR, 'player.html'))

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (manifest.json, icons, service worker, etc.)"""
    return send_from_directory(UTILITIES_DIR, filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    print(f'Starting server on http://0.0.0.0:{port}')
    print(f'Open http://localhost:{port} in your browser to access the player')
    app.run(host='0.0.0.0', port=port, debug=debug)
