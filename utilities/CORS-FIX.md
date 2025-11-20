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

**Your miniurl server is running Nginx**, so use the nginx configuration below.

#### For Nginx (Your Current Setup):

1. Edit your nginx configuration file (usually `/etc/nginx/sites-available/miniurl.shalusri.com`)
2. Add the CORS headers to your location block as shown in `miniurl-nginx.conf`
3. Reload nginx: `sudo nginx -t && sudo systemctl reload nginx`

**Key configuration** (see `miniurl-nginx.conf` for full details):
```nginx
location / {
    # The 'always' parameter is CRITICAL for redirects!
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Origin, Content-Type, Accept' always;

    if ($request_method = 'OPTIONS') {
        return 204;
    }

    # Your existing redirect configuration
}
```

**Why 'always' is required:** Without the `always` parameter, nginx only adds headers to 200 responses. The `always` parameter ensures CORS headers are included in redirect responses (307, 302, etc.), which is essential for JavaScript fetch() to work.

#### For Apache servers (Alternative):

If you were using Apache, you would use the `miniurl-htaccess` file:
```bash
cp utilities/miniurl-htaccess /path/to/miniurl/server/.htaccess
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

To verify CORS headers are working after applying the nginx configuration:

```bash
curl -I -H "Origin: https://bhajans.shalusri.com" https://miniurl.shalusri.com/bhajanamala37
```

**Before the fix**, you'll see:
```
HTTP/2 307
server: nginx
location: https://drive.google.com/drive/...
(NO Access-Control headers)
```

**After the fix**, you should see:
```
HTTP/2 307
server: nginx
access-control-allow-origin: *
access-control-allow-methods: GET, OPTIONS
location: https://drive.google.com/drive/...
```

The key is that `access-control-allow-origin` appears in the 307 redirect response.

## Additional Notes

- The player now automatically detects if you're providing a Drive URL/ID and bypasses the miniurl step
- Error messages now provide helpful guidance when CORS errors occur
- All audio files are cached locally using IndexedDB for offline playback
