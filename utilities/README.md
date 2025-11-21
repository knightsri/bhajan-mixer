# Google Drive Album Player

A simple web-based MP3 player for Google Drive folders - **NO API KEY REQUIRED!**

Server-side caching architecture: fetches Google Drive folder contents once, caches them as JSON, and serves a fast player interface.

## Quick Start

1. **Install dependencies:**
   ```bash
   cd utilities
   npm install
   ```

2. **Start the server:**
   ```bash
   npm start
   ```

3. **Open in browser:**
   - Navigate to `http://localhost:3099`

4. **Enter your Google Drive folder URL or ID**

5. **Play your music!**

## How It Works

### Architecture

1. **User visits with folder ID**: `http://localhost:3099/?folder=<FOLDER_ID>`

2. **Server checks cache**:
   - If `cache/<folder_id>.json` exists → serve player instantly
   - If not → fetch Google Drive folder, extract MP3 files, save to cache

3. **Player loads cached JSON**: `GET /playlist/<folder_id>.json`

4. **MP3s stream directly from Google Drive**

### Benefits

- ✅ **Cached playlists** - Server fetches Drive folder only once
- ✅ **Fast loading** - Subsequent visits are instant
- ✅ **No API key** - Scrapes public folder HTML
- ✅ **Simple** - Just run one server
- ✅ **Efficient** - No repeated Drive requests

## Setup Instructions

### 1. Install Dependencies

```bash
cd utilities
npm install
```

This installs:
- `express` - Web server framework
- `node-fetch` - HTTP client for fetching Drive pages

### 2. Start the Server

```bash
npm start
```

Server runs on `http://localhost:3099` by default.

**Environment variables:**
- `PORT` - Server port (default: 3099)

Example:
```bash
PORT=8080 npm start
```

### 3. Prepare Your Google Drive Folder

1. Create a folder in Google Drive with your MP3 files
2. Right-click the folder → **Share**
3. Change access to **"Anyone with the link can view"**
4. Copy the folder URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`

### 4. Use the Player

**Option 1: Landing page**
1. Open `http://localhost:3099`
2. Paste folder URL or ID
3. Click "Load Player"

**Option 2: Direct link**
```
http://localhost:3099/?folder=YOUR_FOLDER_ID
```

## Features

- **Server-side caching** - Folders cached as JSON files
- **Instant loading** - Cached folders load immediately
- **No API key required** - Scrapes public folder HTML
- **Automatic file discovery** - No manual playlist creation
- **Offline playback** - Browser caches audio files
- **Mobile-friendly** - Responsive design
- **PWA support** - Install as app
- **Auto-advance** - Plays next track automatically
- **Progress tracking** - Visual progress bar

## API Endpoints

### `GET /?folder=<folder_id>`

Load player for a Google Drive folder. Server will cache the folder contents if not already cached.

### `GET /playlist/<folder_id>.json`

Get cached playlist JSON for a folder.

**Response:**
```json
[
  {
    "id": "1a2B3c4D5e6F7g8H9i0J",
    "name": "Song Title",
    "url": "https://drive.google.com/uc?export=download&id=1a2B3c4D5e6F7g8H9i0J"
  }
]
```

### `GET /refresh/<folder_id>`

Force refresh a folder's cache (re-fetch from Google Drive).

**Response:**
```json
{
  "success": true,
  "message": "Folder cache refreshed"
}
```

### `GET /debug/<folder_id>`

Debug endpoint for troubleshooting MP3 extraction issues. Fetches the folder HTML, saves it for inspection, and returns detailed extraction information.

**Response:**
```json
{
  "success": true,
  "folderId": "YOUR_FOLDER_ID",
  "htmlLength": 123456,
  "filesFound": 5,
  "files": [...],
  "debugHtmlSaved": "/path/to/cache/debug-FOLDER_ID.html",
  "mp3Occurrences": 10
}
```

**Usage:**
```bash
curl http://localhost:3099/debug/YOUR_FOLDER_ID
```

This endpoint is useful when the regular extraction fails, as it provides:
- How many `.mp3` occurrences exist in the HTML
- Which regex patterns successfully matched files
- Debug logs showing extraction details
- Saved HTML file for manual inspection

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "cache_dir": "/path/to/cache"
}
```

## Cache Management

### Cache Location

Cached playlists are stored in `utilities/cache/`

### Cache Files

Each folder gets a JSON file: `cache/<folder_id>.json`

### Refresh Cache

To refresh a folder's cache:
```bash
curl http://localhost:3099/refresh/YOUR_FOLDER_ID
```

Or delete the cache file and reload:
```bash
rm cache/YOUR_FOLDER_ID.json
```

### Clear All Cache

```bash
rm cache/*.json
```

## Deployment

### Deploy to Heroku

1. Create `Procfile`:
   ```
   web: node utilities/server.js
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

3. Your app will be at: `https://your-app-name.herokuapp.com`

### Deploy to Vercel/Railway/Render

All support Node.js apps. Configure to run `node utilities/server.js`

### Deploy Locally on Network

To make accessible on your local network:

```bash
npm start
# Server runs on http://0.0.0.0:3099
# Access from other devices: http://YOUR_LOCAL_IP:3000
```

## Troubleshooting

### "Failed to load folder"
- **Check folder is public**: Open folder URL in incognito window
- **Verify folder ID**: Make sure you copied the correct ID
- **Check server logs**: Look for error messages in terminal
- **Use debug endpoint**: `GET /debug/<folder_id>` to see detailed extraction info

### "No MP3 files found"
- Folder must contain files with `.mp3` extension (case-insensitive)
- Files should be directly in the folder (not subfolders)
- Folder must be publicly accessible ("Anyone with the link can view")
- **Use debug endpoint** to see how many .mp3 occurrences were found:
  ```bash
  curl http://localhost:3099/debug/YOUR_FOLDER_ID
  ```
- Check server logs for pattern matching results
- The app now tries multiple regex patterns to handle different Google Drive HTML formats

### Improved Error Handling (v2.0)

The app now includes:
- **Styled error pages** with helpful troubleshooting tips
- **Multiple regex patterns** for better compatibility with Google Drive HTML changes
- **Debug logging** showing which patterns matched and how many files found
- **Debug endpoint** (`/debug/<folder_id>`) for deep troubleshooting
- **Helpful error messages** with specific solutions for common issues

### "Failed to load playlist"
- Server may not have cached the folder yet
- Visit `http://localhost:3099/?folder=YOUR_FOLDER_ID` first
- Check cache directory exists: `ls utilities/cache/`

### Songs not playing
- Files must be shared as "Anyone with the link can view"
- Try opening the download URL directly in browser
- Check browser console for specific errors

### Server won't start
- Make sure dependencies are installed: `npm install`
- Check port 3099 isn't already in use
- Try a different port: `PORT=8080 npm start`

### Advanced Debugging

If extraction is failing:

1. **Check debug endpoint**:
   ```bash
   curl http://localhost:3099/debug/YOUR_FOLDER_ID | jq
   ```

2. **Inspect saved HTML**:
   ```bash
   cat utilities/cache/debug-YOUR_FOLDER_ID.html | grep -i "\.mp3"
   ```

3. **Check server logs** - The app now logs:
   - Which regex patterns found matches
   - Total .mp3 occurrences in HTML
   - Sample lines containing .mp3 references
   - Potential file IDs found

4. **Try force refresh**:
   ```bash
   curl http://localhost:3099/refresh/YOUR_FOLDER_ID
   ```

## Development

### File Structure

```
utilities/
├── server.js          # Node.js server
├── player.html        # Player interface
├── package.json       # Dependencies
├── cache/            # Cached playlists
│   └── .gitkeep
├── manifest.json      # PWA manifest
├── icon-192.png      # PWA icon (small)
├── icon-512.png      # PWA icon (large)
└── sw.js             # Service worker
```

### Running in Development

```bash
npm start
```

Server will log:
- When folders are fetched and cached
- When cached playlists are served
- Any errors that occur

### Testing with curl

```bash
# Health check
curl http://localhost:3099/health

# Load and cache a folder
curl http://localhost:3099/?folder=YOUR_FOLDER_ID

# Get cached playlist
curl http://localhost:3099/playlist/YOUR_FOLDER_ID.json

# Refresh cache
curl http://localhost:3099/refresh/YOUR_FOLDER_ID
```

### Improving Scraping

The server uses **multiple regex patterns** to extract file IDs from Drive HTML, making it more resilient to Google Drive HTML structure changes. Current patterns in `server.js`:

```javascript
const patterns = [
  // Pattern 1: Original format ["fileId","filename.mp3",...]
  /\["([a-zA-Z0-9_-]{25,})","([^"]*\.mp3[^"]*)"/gi,
  // Pattern 2: Single quotes variant ['fileId','filename.mp3',...]
  /\['([a-zA-Z0-9_-]{25,})','([^']*\.mp3[^']*)'/gi,
  // Pattern 3: With escaped quotes [\"fileId\",\"filename.mp3\",...]
  /\[\\?"([a-zA-Z0-9_-]{25,})\\?",\\?"([^"]*\.mp3[^"]*)\\?"/gi,
  // Pattern 4: Data structure format (33-char IDs)
  /["']([a-zA-Z0-9_-]{33})["'][,\s]*["']([^"']*\.mp3[^"']*)["']/gi
];
```

If extraction fails, use the `/debug/<folder_id>` endpoint to:
1. See which patterns matched
2. Inspect the raw HTML structure
3. Add new patterns if needed

## Security Notes

- Server only accesses public Google Drive folders
- No authentication or API keys required
- No user data collected or stored
- Only returns MP3 files from specified folders
- Cache files are stored locally on server

## Why This Approach?

**Alternative approaches:**
1. ❌ **Google Drive API** - Requires API key, quotas, OAuth complexity
2. ❌ **Manual JSON playlist** - Tedious, must update manually
3. ❌ **Real-time scraping** - Slow, rate-limited, inefficient
4. ✅ **Server-side caching** - Fast, simple, efficient!

**Trade-offs:**
- ✅ No API key management
- ✅ Automatic file discovery
- ✅ Fast loading (cached)
- ✅ Efficient (scrape once, serve many)
- ✅ Simple deployment
- ⚠️ Requires Node.js server
- ⚠️ Cache must be refreshed manually for folder updates
- ⚠️ May break if Google changes HTML structure (rare)

For personal/small-scale use, this is the optimal solution!

## Example Folder Structure

```
Google Drive Folder (public)
├── 01 - Song Name.mp3
├── 02 - Another Song.mp3
├── 03 - Third Song.mp3
└── 04 - Final Track.mp3
```

The server will automatically discover and cache all MP3 files.

## License

MIT License - Use freely for personal and commercial projects.

## Support

For issues or questions:
1. Check the server logs for errors
2. Verify folder is publicly accessible
3. Try refreshing the cache: `/refresh/<folder_id>`
4. Check browser console for client-side errors

Enjoy your music! 🎵
