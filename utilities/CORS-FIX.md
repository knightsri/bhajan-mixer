# CORS Error Fix for Album Player

## Problem

When using the album player on `bhajans.shalusri.com`, you may encounter a CORS (Cross-Origin Resource Sharing) error:

```
A cross-origin resource sharing (CORS) request was blocked because of invalid or missing response headers
Access-Control-Allow-Origin: Missing Header
```

This happens because the `miniurl.shalusri.com` server doesn't send proper CORS headers when `bhajans.shalusri.com` tries to fetch album redirects.

## Solutions

### Option 1: Configure miniurl.shalusri.com Server (Recommended)

1. Copy the `miniurl-htaccess` file to your `miniurl.shalusri.com` server
2. Rename it to `.htaccess`
3. Place it in the root directory of the miniurl server

This will add the necessary CORS headers to allow cross-origin requests.

**For Apache servers:**
```bash
cp utilities/miniurl-htaccess /path/to/miniurl/server/.htaccess
```

**For Nginx servers:**
Add the following to your nginx configuration:

```nginx
location / {
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    add_header Access-Control-Max-Age 3600;

    if ($request_method = OPTIONS) {
        return 200;
    }
}
```

### Option 2: Use Google Drive URLs Directly

Instead of using album names, you can now use Google Drive folder URLs or IDs directly:

**Examples:**
- Full URL: `https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz`
- Folder ID only: `1AbCdEfGhIjKlMnOpQrStUvWxYz`
- Album name (requires CORS fix): `bhajanamala37`

**Usage:**
1. Open the player: `https://bhajans.shalusri.com/utilities/player.html`
2. Enter your Google Drive folder URL or ID
3. Click "Load Album"

**Query parameter:**
```
https://bhajans.shalusri.com/utilities/player.html?album=1AbCdEfGhIjKlMnOpQrStUvWxYz
```

## Testing the Fix

After applying the CORS configuration:

1. Clear your browser cache
2. Navigate to the player
3. Try loading an album using the album name
4. Check the browser console (F12) - you should not see CORS errors

## Verification

To verify CORS headers are working, check the response headers from miniurl.shalusri.com:

```bash
curl -I -H "Origin: https://bhajans.shalusri.com" https://miniurl.shalusri.com/bhajanamala37
```

You should see:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, OPTIONS
```

## Additional Notes

- The player now automatically detects if you're providing a Drive URL/ID and bypasses the miniurl step
- Error messages now provide helpful guidance when CORS errors occur
- All audio files are cached locally using IndexedDB for offline playback
