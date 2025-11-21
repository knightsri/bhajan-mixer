# Google Drive Album Player

A simple web-based MP3 player for Google Drive folders - **NO API KEY REQUIRED!**

Uses a lightweight Flask proxy server to scrape public Google Drive folders and extract MP3 file information.

## Quick Start

1. **Start the server:**
   ```bash
   cd utilities
   pip install -r requirements.txt
   python proxy.py
   ```

2. **Make your Google Drive folder public:**
   - Right-click folder → Share → "Anyone with the link can view"

3. **Open the player in your browser:**
   - Navigate to `http://localhost:5000`

4. **Enter your Google Drive folder ID or URL**

5. **Click "Load Album" and enjoy!**

## Setup Instructions

### 1. Install Dependencies

```bash
cd utilities
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- flask-cors (for browser CORS)
- requests (for HTTP requests)

### 2. Start the Server

```bash
python proxy.py
```

The server starts on `http://localhost:5000` by default and serves both the player interface and API endpoints.

**Environment variables:**
- `PORT`: Server port (default: 5000)
- `DEBUG`: Enable debug mode (default: False)

Example:
```bash
PORT=8080 DEBUG=true python proxy.py
```

### 3. Prepare Your Google Drive Folder

1. Create a folder in Google Drive with your MP3 files
2. Right-click the folder → **Share**
3. Change access to **"Anyone with the link can view"**
4. Copy the folder URL (looks like: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`)

### 4. Use the Player

1. Open `http://localhost:5000` in your browser
2. Enter your Google Drive folder ID or full URL
3. Click **Load Album**

**URL parameters for auto-load:**
```
http://localhost:5000?folder=YOUR_FOLDER_ID
```

## How It Works

1. **Flask Server** (`proxy.py`):
   - Serves the player interface at `/`
   - Provides API endpoint at `/api/drive-files/<folder_id>`
   - Fetches public Google Drive folder HTML
   - Scrapes HTML to extract MP3 file IDs and names
   - Returns clean JSON array to browser

2. **Player** (`player.html`):
   - Served directly by the Flask server
   - Calls `/api/drive-files/` endpoint with folder ID
   - Receives list of MP3 files
   - Plays files using Google Drive's public download URLs
   - Caches audio for offline playback

**No API key needed!** The server scrapes the public folder page, which doesn't require authentication.

## API Endpoints

### `GET /api/drive-files/<folder_id>`

Get MP3 files from a public Google Drive folder.

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

**Example:**
```bash
curl http://localhost:5000/api/drive-files/YOUR_FOLDER_ID
```

### `GET /api/health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "drive-proxy"
}
```

## Deployment

### Deploy to Heroku

1. Create `Procfile`:
   ```
   web: python utilities/proxy.py
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

3. Use your Heroku URL as the proxy: `https://your-app-name.herokuapp.com`

### Deploy to Vercel/Railway/Render

All support Python Flask apps. Follow their deployment guides and point to `proxy.py`.

### Deploy Locally on Network

To make the proxy accessible on your local network:

```bash
python proxy.py
# Server runs on http://0.0.0.0:5000
# Access from other devices: http://YOUR_LOCAL_IP:5000
```

## Features

- **No API key required** - Scrapes public folder HTML
- **Automatic file discovery** - No manual playlist creation
- **Works offline** - Caches audio files
- **Mobile-friendly** - Responsive design
- **PWA support** - Install as app
- **Auto-advance** - Plays next track automatically
- **Progress tracking** - Visual progress bar

## Troubleshooting

### "Failed to fetch folder"
- **Check server is running**: `curl http://localhost:5000/api/health`
- **Verify folder is public**: Open folder URL in incognito window
- **CORS errors**: Make sure flask-cors is installed

### "No MP3 files found"
- Folder must contain files with `.mp3` extension
- Files should be in the folder, not subfolders
- Check folder ID is correct

### Songs not playing
- Files must be shared as "Anyone with the link can view"
- Try opening the download URL directly in browser
- Check browser console for specific errors

### Server connection refused
- Make sure server is running (`python proxy.py`)
- Check firewall isn't blocking port 5000
- Verify you're accessing `http://localhost:5000` (http://, not https://)

## Development

### Running in Debug Mode

```bash
DEBUG=true python proxy.py
```

Shows detailed request logs and Flask debug output.

### Testing the Proxy

```bash
# Health check
curl http://localhost:5000/api/health

# Test with a folder ID
curl http://localhost:5000/api/drive-files/YOUR_FOLDER_ID

# Pretty print JSON
curl http://localhost:5000/api/drive-files/YOUR_FOLDER_ID | python -m json.tool
```

### Improving Scraping

The proxy uses regex patterns to extract file IDs from the Drive folder HTML. If Google changes their HTML structure, you may need to update the patterns in `proxy.py`:

```python
# Look for patterns in the HTML
pattern1 = r'\["([a-zA-Z0-9_-]{25,})","([^"]*\.mp3[^"]*)"'
```

## Security Notes

- Proxy only accesses public Google Drive folders
- No authentication or API keys stored
- No user data collected
- CORS enabled for browser requests
- Only returns MP3 files from specified folders

## Why This Approach?

**Alternative approaches:**
1. ❌ **Google Drive API** - Requires API key setup, quotas, complexity
2. ❌ **Manual JSON playlist** - Requires manually listing all file IDs
3. ✅ **Server-side scraping** - Simple, automatic, no auth required!

**Trade-offs:**
- ✅ No API key management
- ✅ Automatic file discovery
- ✅ Simple setup - just run one server
- ✅ Player and API served from same origin (no CORS issues)
- ⚠️ Requires running a Python server
- ⚠️ May break if Google changes HTML structure (rare)

For personal/small-scale use, this is the simplest solution!

## Example Folder Structure

```
Google Drive Folder (public)
├── 01 - Song Name.mp3
├── 02 - Another Song.mp3
├── 03 - Third Song.mp3
└── 04 - Final Track.mp3
```

The player will automatically discover and play all MP3 files in order.

## License

MIT License - Use freely for personal and commercial projects.

## Support

For issues or questions:
1. Check the browser console for errors
2. Test the proxy API directly with curl
3. Verify folder is publicly accessible
4. Check proxy server logs for detailed errors

Enjoy your music! 🎵
