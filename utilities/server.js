#!/usr/bin/env node
/**
 * Google Drive MP3 Player Server
 * Fetches and caches folder contents, serves player interface
 */

const express = require('express');
const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3099;
const CACHE_DIR = path.join(__dirname, 'cache');

// Ensure cache directory exists
if (!fs.existsSync(CACHE_DIR)) {
  fs.mkdirSync(CACHE_DIR, { recursive: true });
}

// Serve static files (icons, manifest, service worker)
app.use(express.static(__dirname));

/**
 * Main endpoint - serves player with folder ID
 * Usage: http://localhost:3000/?folder=<FOLDER_ID>
 */
app.get('/', async (req, res) => {
  const folderId = req.query.folder;

  if (!folderId) {
    // Show landing page with input form
    return res.send(getLandingPage());
  }

  try {
    // Ensure folder playlist is cached
    await ensureFolderCached(folderId);

    // Serve player page
    const playerHtml = fs.readFileSync(path.join(__dirname, 'player.html'), 'utf8');
    // Inject folder ID into player
    const modifiedHtml = playerHtml.replace(
      '<script>',
      `<script>\nconst FOLDER_ID = '${folderId}';\n`
    );
    res.send(modifiedHtml);
  } catch (error) {
    console.error('Error loading folder:', error);
    res.status(500).send(getErrorPage(error.message, folderId));
  }
});

/**
 * Serve cached playlist JSON
 */
app.get('/playlist/:folderId.json', (req, res) => {
  const { folderId } = req.params;
  const cachePath = path.join(CACHE_DIR, `${folderId}.json`);

  if (!fs.existsSync(cachePath)) {
    return res.status(404).json({ error: 'Playlist not found' });
  }

  res.sendFile(cachePath);
});

/**
 * Force refresh a folder's cache
 */
app.get('/refresh/:folderId', async (req, res) => {
  const { folderId } = req.params;

  try {
    await fetchAndCacheFolder(folderId, true);
    res.json({ success: true, message: 'Folder cache refreshed' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * Debug endpoint - saves raw HTML for troubleshooting
 */
app.get('/debug/:folderId', async (req, res) => {
  const { folderId } = req.params;

  try {
    const url = `https://drive.google.com/drive/folders/${folderId}`;
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    if (!response.ok) {
      return res.status(response.status).json({
        error: `Failed to fetch folder: ${response.status}`,
        folderId
      });
    }

    const html = await response.text();

    // Save HTML for inspection
    const debugPath = path.join(CACHE_DIR, `debug-${folderId}.html`);
    fs.writeFileSync(debugPath, html);

    // Try extraction
    const files = extractMp3Files(html);

    res.json({
      success: true,
      folderId,
      htmlLength: html.length,
      filesFound: files.length,
      files: files,
      debugHtmlSaved: debugPath,
      mp3Occurrences: (html.match(/\.mp3/gi) || []).length
    });
  } catch (error) {
    res.status(500).json({ error: error.message, folderId });
  }
});

/**
 * Health check
 */
app.get('/health', (req, res) => {
  res.json({ status: 'ok', cache_dir: CACHE_DIR });
});

/**
 * Ensure folder is cached, fetch if not
 */
async function ensureFolderCached(folderId) {
  const cachePath = path.join(CACHE_DIR, `${folderId}.json`);

  // Check if cache exists
  if (fs.existsSync(cachePath)) {
    console.log(`✓ Using cached playlist for folder: ${folderId}`);
    return;
  }

  // Cache doesn't exist, fetch and save
  console.log(`⟳ Fetching folder contents for: ${folderId}`);
  await fetchAndCacheFolder(folderId);
}

/**
 * Fetch Google Drive folder and save as JSON
 */
async function fetchAndCacheFolder(folderId, force = false) {
  const cachePath = path.join(CACHE_DIR, `${folderId}.json`);

  // Skip if cached and not forcing refresh
  if (!force && fs.existsSync(cachePath)) {
    return;
  }

  try {
    // Fetch the public folder page
    const url = `https://drive.google.com/drive/folders/${folderId}`;
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch folder: ${response.status}`);
    }

    const html = await response.text();

    // Extract MP3 files from HTML
    const files = extractMp3Files(html);

    if (files.length === 0) {
      throw new Error('No MP3 files found in folder. Make sure folder is public and contains MP3 files.');
    }

    // Save to cache
    fs.writeFileSync(cachePath, JSON.stringify(files, null, 2));
    console.log(`✓ Cached ${files.length} files for folder: ${folderId}`);

    return files;
  } catch (error) {
    console.error(`Error fetching folder ${folderId}:`, error.message);
    throw error;
  }
}

/**
 * Extract MP3 file information from Drive folder HTML
 */
function extractMp3Files(html) {
  const files = [];
  const seen = new Set();

  console.log('Attempting to extract MP3 files with multiple patterns...');

  // Strategy 1: Try old regex patterns for backwards compatibility
  const oldPatterns = [
    // Pattern 1: Original format ["fileId","filename.mp3",...]
    /\["([a-zA-Z0-9_-]{25,})","([^"]*\.mp3[^"]*)"/gi,
    // Pattern 2: Single quotes variant ['fileId','filename.mp3',...]
    /\['([a-zA-Z0-9_-]{25,})','([^']*\.mp3[^']*)'/gi,
    // Pattern 3: With escaped quotes [\"fileId\",\"filename.mp3\",...]
    /\[\\?"([a-zA-Z0-9_-]{25,})\\?",\\?"([^"]*\.mp3[^"]*)\\?"/gi,
    // Pattern 4: Data structure format with file IDs and names separately
    /["']([a-zA-Z0-9_-]{33})["'][,\s]*["']([^"']*\.mp3[^"']*)["']/gi
  ];

  // Try old patterns first
  oldPatterns.forEach((pattern, index) => {
    pattern.lastIndex = 0;
    let match;
    let patternMatches = 0;

    while ((match = pattern.exec(html)) !== null) {
      const [, fileId, filename] = match;
      if (seen.has(fileId)) continue;
      seen.add(fileId);

      const cleanName = filename.replace(/\.mp3$/i, '');
      files.push({
        id: fileId,
        name: cleanName,
        url: `https://drive.usercontent.google.com/download?id=${fileId}&export=download`
      });
      patternMatches++;
    }

    if (patternMatches > 0) {
      console.log(`✓ Old pattern ${index + 1} found ${patternMatches} files`);
    }
  });

  // Strategy 2: New format - two-pass extraction for current Google Drive HTML
  // Current format uses data-id="FILE_ID" with filenames in separate elements
  if (files.length === 0) {
    console.log('Trying two-pass extraction strategy for current Google Drive format...');

    // Pass 1: Find all data-id attributes for documents
    const dataIdPattern = /data-id="([a-zA-Z0-9_-]{25,})"[^>]*data-target="doc"/g;
    const fileIds = [];
    let match;

    while ((match = dataIdPattern.exec(html)) !== null) {
      const fileId = match[1];
      if (!seen.has(fileId)) {
        seen.add(fileId);
        fileIds.push({id: fileId, index: match.index});
      }
    }

    console.log(`  Found ${fileIds.length} unique file IDs`);

    // Pass 2: For each file ID, find the corresponding .mp3 filename nearby
    const filenamePatterns = [
      />([^<]*\.mp3)</i,
      /aria-label="[^"]*?([^"]*\.mp3)"/i,
      /data-tooltip="[^"]*?([^"]*\.mp3)"/i
    ];

    for (const {id, index} of fileIds) {
      // Look within 5000 characters after the data-id
      const snippet = html.substring(index, index + 5000);

      // Try to find .mp3 filename in this snippet
      let filename = null;
      for (const pattern of filenamePatterns) {
        const m = snippet.match(pattern);
        if (m) {
          filename = m[1].replace(/^Audio:\s*/i, '').trim();
          break;
        }
      }

      if (filename) {
        const cleanName = filename.replace(/\.mp3$/i, '');
        files.push({
          id: id,
          name: cleanName,
          url: `https://drive.usercontent.google.com/download?id=${id}&export=download`
        });
      }
    }

    if (files.length > 0) {
      console.log(`✓ Two-pass extraction found ${files.length} files`);
    }
  }

  // Log total found
  console.log(`Total unique MP3 files found: ${files.length}`);

  // If still no files found, debug
  if (files.length === 0) {
    const mp3Count = (html.match(/\.mp3/gi) || []).length;
    console.log(`Debug: Found ${mp3Count} .mp3 occurrences in HTML`);

    // Check for common file ID patterns
    const fileIdPattern = /\[\[null,"([a-zA-Z0-9_-]{25,})"\]/g;
    const potentialIds = new Set();
    let match;
    while ((match = fileIdPattern.exec(html)) !== null) {
      potentialIds.add(match[1]);
    }
    console.log(`Debug: Found ${potentialIds.size} potential file IDs with [[null,"ID"]] pattern`);

    // Sample some .mp3 references
    const lines = html.split('\n').filter(line => line.toLowerCase().includes('.mp3')).slice(0, 3);
    if (lines.length > 0) {
      console.log('Debug: Sample lines with .mp3:');
      lines.forEach((line, i) => {
        console.log(`  ${i+1}. ${line.substring(0, 200).trim()}...`);
      });
    }
  }

  return files;
}

/**
 * Error page HTML with styling
 */
function getErrorPage(errorMessage, folderId) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#667eea">
    <link rel="manifest" href="./manifest.json">
    <link rel="apple-touch-icon" href="./icon-192.png">
    <title>Error Loading Folder - Google Drive MP3 Player</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        .error-icon {
            font-size: 64px;
            text-align: center;
            margin-bottom: 20px;
        }
        h1 {
            color: #d32f2f;
            margin-bottom: 20px;
            font-size: 28px;
            text-align: center;
        }
        .error-message {
            background: #ffebee;
            border-left: 4px solid #d32f2f;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            color: #c62828;
            line-height: 1.6;
        }
        .folder-id {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            margin-bottom: 20px;
            word-break: break-all;
            font-size: 14px;
        }
        .folder-id strong {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .help {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 14px;
            line-height: 1.6;
            color: #1565c0;
        }
        .help strong {
            display: block;
            margin-bottom: 10px;
            color: #0d47a1;
        }
        .help ul {
            margin-left: 20px;
            margin-top: 10px;
        }
        .help li {
            margin-bottom: 8px;
        }
        .buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .btn {
            flex: 1;
            min-width: 140px;
            padding: 15px 20px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, opacity 0.2s;
            text-decoration: none;
            text-align: center;
            display: inline-block;
        }
        .btn:hover {
            transform: translateY(-2px);
            opacity: 0.9;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-secondary {
            background: #f5f5f5;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="error-icon">⚠️</div>
        <h1>Error Loading Folder</h1>

        <div class="error-message">
            ${errorMessage}
        </div>

        ${folderId ? `
        <div class="folder-id">
            <strong>Folder ID attempted:</strong>
            ${folderId}
        </div>
        ` : ''}

        <div class="help">
            <strong>💡 Common issues and solutions:</strong>
            <ul>
                <li><strong>Folder not public:</strong> Right-click the folder in Google Drive → Share → Change to "Anyone with the link"</li>
                <li><strong>No MP3 files:</strong> Make sure the folder contains files with .mp3 extension (case-insensitive)</li>
                <li><strong>Files in subfolders:</strong> MP3 files must be directly in the folder, not in nested subfolders</li>
                <li><strong>Invalid folder ID:</strong> Check that you copied the complete folder ID from the URL</li>
            </ul>
        </div>

        <div class="buttons">
            <a href="/" class="btn btn-primary">← Try Another Folder</a>
            ${folderId ? `<a href="/refresh/${folderId}" class="btn btn-secondary">🔄 Retry</a>` : ''}
        </div>
    </div>

    <script>
        // Register service worker for PWA support
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('./sw.js')
                .then(reg => console.log('SW registered', reg))
                .catch(err => console.log('SW registration failed', err));
        }
    </script>
</body>
</html>`;
}

/**
 * Landing page HTML with folder input
 */
function getLandingPage() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#667eea">
    <link rel="manifest" href="./manifest.json">
    <link rel="apple-touch-icon" href="./icon-192.png">
    <title>Google Drive MP3 Player</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        p {
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        input {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            margin-bottom: 15px;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .help {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            font-size: 14px;
            color: #555;
        }
        .help strong { display: block; margin-bottom: 5px; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Google Drive MP3 Player</h1>
        <p>Play MP3 files from any public Google Drive folder - no API key required!</p>

        <form onsubmit="event.preventDefault(); loadFolder();">
            <input
                type="text"
                id="folderInput"
                placeholder="Paste Google Drive folder URL or ID"
                required
            >
            <button type="submit">Load Player</button>
        </form>

        <div class="help">
            <strong>How to use:</strong>
            1. Make your Google Drive folder public<br>
            2. Copy the folder URL or ID<br>
            3. Paste it above and click "Load Player"<br>
            <br>
            <strong>Example URL:</strong><br>
            https://drive.google.com/drive/folders/<em>FOLDER_ID</em>
        </div>
    </div>

    <script>
        function loadFolder() {
            const input = document.getElementById('folderInput').value.trim();
            let folderId = input;

            // Extract folder ID from URL if needed
            if (input.includes('drive.google.com')) {
                const match = input.match(/\\/folders\\/([a-zA-Z0-9_-]+)/);
                if (match) folderId = match[1];
            }

            if (folderId) {
                window.location.href = '/?folder=' + folderId;
            }
        }

        // Register service worker for PWA support
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('./sw.js')
                .then(reg => console.log('SW registered', reg))
                .catch(err => console.log('SW registration failed', err));
        }
    </script>
</body>
</html>`;
}

// Start server
app.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════╗
║  Google Drive MP3 Player Server            ║
╚════════════════════════════════════════════╝

✓ Server running at: http://localhost:${PORT}
✓ Cache directory: ${CACHE_DIR}

Open http://localhost:${PORT} in your browser to get started!
  `);
});
