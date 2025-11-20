# Google Drive Album Player

A simple, single-page web app for playing MP3 files from Google Drive - **NO API KEY REQUIRED!**

## Quick Start

1. Upload your MP3 files to Google Drive
2. Make each file publicly accessible ("Anyone with the link can view")
3. Create a `playlist.json` file with your file IDs and song names
4. Open `player.html` and paste your `playlist.json` URL
5. Enjoy your music!

## Setup Instructions

### Step 1: Upload MP3s to Google Drive

1. Go to [Google Drive](https://drive.google.com/)
2. Create a new folder for your album (optional but recommended)
3. Upload your MP3 files

### Step 2: Share Your Files Publicly

For **each MP3 file**:
1. Right-click the file → **Get link** (or **Share**)
2. Change access to **"Anyone with the link"** with **Viewer** permissions
3. Click **Copy link**
4. Save the link - you'll need the file ID from it

### Step 3: Extract File IDs

From each share link, extract the file ID:
- Link format: `https://drive.google.com/file/d/FILE_ID_HERE/view?usp=sharing`
- The FILE_ID is the long string between `/d/` and `/view`

Example:
```
https://drive.google.com/file/d/1a2B3c4D5e6F7g8H9i0J/view?usp=sharing
                               ^^^^^^^^^^^^^^^^^^^
                               This is the file ID
```

### Step 4: Create Your Playlist JSON

Create a file named `playlist.json` with the following format:

```json
[
  {
    "id": "1a2B3c4D5e6F7g8H9i0J",
    "name": "Song Title 1"
  },
  {
    "id": "2b3C4d5E6f7G8h9I0j1K",
    "name": "Song Title 2"
  },
  {
    "id": "3c4D5e6F7g8H9i0J1k2L",
    "name": "Song Title 3"
  }
]
```

**Important:**
- Each song needs an `id` (the Google Drive file ID)
- Each song needs a `name` (what will display in the player)
- See `playlist.example.json` for a template

### Step 5: Host Your Playlist JSON

You need to make your `playlist.json` file accessible via URL. Options:

**Option A: Upload to Google Drive** (simplest)
1. Upload `playlist.json` to Google Drive
2. Right-click → Get link → Anyone with the link
3. Get the file ID from the share link
4. Use this URL format: `https://drive.google.com/uc?export=download&id=YOUR_PLAYLIST_FILE_ID`

**Option B: GitHub** (recommended for version control)
1. Create a GitHub repository or use an existing one
2. Upload `playlist.json`
3. Use the raw file URL: `https://raw.githubusercontent.com/username/repo/branch/playlist.json`

**Option C: Any other public hosting**
- Dropbox public link
- Your own website
- Any service that provides a direct URL to the JSON file

### Step 6: Use the Player

1. Open `player.html` in your browser
2. Paste your `playlist.json` URL in the input field
3. Click **Load Album**
4. Press play and enjoy!

**Pro tip:** You can also use URL parameters to auto-load a playlist:
```
player.html?playlist=https://example.com/playlist.json
```

## Features

- **No API key required!** - Simple JSON-based playlist
- **Works offline** - Caches songs for offline playback
- **Mobile-friendly** - Responsive design works on all devices
- **PWA support** - Install as an app on mobile
- **Auto-advance** - Automatically plays next track
- **Progress tracking** - Visual progress bar
- **Playlist management** - Click any song to jump to it

## Troubleshooting

### "Failed to fetch playlist"
- Make sure your `playlist.json` URL is publicly accessible
- Try opening the URL directly in your browser - it should download/display the JSON
- Check for CORS issues - some hosts may block cross-origin requests

### "Failed to load playlist: Invalid playlist format"
- Verify your JSON syntax is valid (use [JSONLint](https://jsonlint.com/))
- Make sure it's an array `[ ]` of objects `{ }`
- Each object must have an `id` property

### Songs not playing
- Verify each MP3 file is shared as "Anyone with the link can view"
- Make sure the file IDs are correct (extract them from the share links)
- Check browser console for specific errors
- Some browsers may block autoplay - click the play button manually

### CORS errors
- If hosting `playlist.json` on your own server, ensure CORS headers are set
- Google Drive links work well for both the playlist and audio files
- GitHub raw URLs also work well

## Updating Your Playlist

To add/remove/reorder songs:
1. Edit your `playlist.json` file
2. Upload the updated version (replace the old file)
3. Reload the player page (you may need to clear cache)

## Advanced Usage

### Multiple Playlists

Create different playlists for different albums:
- `bhajans-morning.json`
- `bhajans-evening.json`
- `bhajans-special.json`

Then link to them with different URLs:
- `player.html?playlist=...bhajans-morning.json`
- `player.html?playlist=...bhajans-evening.json`

### Sharing Your Playlists

Share the player with a pre-loaded playlist by sharing this URL format:
```
https://yoursite.com/utilities/player.html?playlist=https://example.com/yourplaylist.json
```

## Why No API Key?

Previous versions of this player required a Google Drive API key, which was complicated for users to set up. The new approach:

- Uses a simple JSON playlist file (no API)
- Leverages Google Drive's public download URLs
- No authentication or API quotas to worry about
- Works entirely in the browser
- Simpler and more reliable!

The only trade-off is that you need to manually create the playlist JSON file, but for personal music collections, this is actually quite manageable.

## Example Playlist

See `playlist.example.json` for a working example of the playlist format.

## Support

If you encounter issues:
1. Check the browser console for error messages
2. Verify all URLs are publicly accessible
3. Ensure JSON formatting is valid
4. Make sure Google Drive files are shared correctly

Enjoy your music! 🎵
