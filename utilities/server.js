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
    res.status(500).send(`
      <h1>Error Loading Folder</h1>
      <p>${error.message}</p>
      <a href="/">Go Back</a>
    `);
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

  // Pattern to match file entries: ["fileId","filename.mp3",...]
  const pattern = /\["([a-zA-Z0-9_-]{25,})","([^"]*\.mp3[^"]*)"/gi;
  let match;

  while ((match = pattern.exec(html)) !== null) {
    const [, fileId, filename] = match;

    // Skip duplicates
    if (seen.has(fileId)) continue;
    seen.add(fileId);

    // Clean up filename
    const cleanName = filename.replace(/\.mp3$/i, '');

    files.push({
      id: fileId,
      name: cleanName,
      url: `https://drive.google.com/uc?export=download&id=${fileId}`
    });
  }

  return files;
}

/**
 * Landing page HTML with folder input
 */
function getLandingPage() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
