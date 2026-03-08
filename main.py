from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import logging
import subprocess
import sys

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

COOKIES_FILE = "cookies.txt"

# Ensure yt-dlp is updated
def ensure_ytdlp_updated():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        logger.info("✅ yt-dlp updated successfully")
    except Exception as e:
        logger.error(f"Failed to update yt-dlp: {e}")

# Call this when app starts
ensure_ytdlp_updated()

@app.route('/')
def home():
    return jsonify({
        'name': 'YouTube API',
        'version': '2.0',
        'status': 'running'
    })

@app.route('/health', methods=['GET'])
def health():
    cookies_exists = os.path.exists(COOKIES_FILE)
    cookies_size = os.path.getsize(COOKIES_FILE) if cookies_exists else 0
    
    # Get yt-dlp version
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
        yt_version = result.stdout.strip()
    except:
        yt_version = "unknown"
    
    return jsonify({
        'status': 'ok',
        'cookies': {
            'exists': cookies_exists,
            'size': cookies_size
        },
        'yt_dlp_version': yt_version
    })

@app.route('/title', methods=['GET'])
def get_title():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    logger.info(f"Fetching: {url}")
    
    if os.path.exists(COOKIES_FILE):
        logger.info(f"Using cookies: {os.path.getsize(COOKIES_FILE)} bytes")
    
    # CRITICAL FIX - Simple options, no format specification
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',  # This only gets basic info
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Try with extract_flat first
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({'error': 'No info found'}), 404
            
            # Extract title - try multiple fields
            title = (info.get('title') or 
                    info.get('fulltitle') or 
                    info.get('alt_title') or 
                    'Unknown')
            
            uploader = (info.get('uploader') or 
                       info.get('channel') or 
                       info.get('creator') or 
                       'Unknown')
            
            return jsonify({
                'success': True,
                'title': title,
                'uploader': uploader,
                'video_id': info.get('id', ''),
                'view_count': info.get('view_count', 0)
            })
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error: {error_msg}")
        
        # If format error, try with different approach
        if 'format is not available' in error_msg:
            try:
                # Fallback method - use yt-dlp command line
                import subprocess
                import json
                
                cmd = ['yt-dlp', '--dump-json', '--no-playlist', url]
                if os.path.exists(COOKIES_FILE):
                    cmd.extend(['--cookies', COOKIES_FILE])
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout:
                    data = json.loads(result.stdout)
                    return jsonify({
                        'success': True,
                        'title': data.get('title', 'Unknown'),
                        'uploader': data.get('uploader', 'Unknown'),
                        'video_id': data.get('id', '')
                    })
            except:
                pass
        
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("="*50)
    print("🚀 YouTube API Server v2.0")
    print("="*50)
    print(f"📡 Port: {port}")
    print(f"🍪 Cookies: {'✅ Found' if os.path.exists(COOKIES_FILE) else '❌ Not found'}")
    if os.path.exists(COOKIES_FILE):
        print(f"📦 Size: {os.path.getsize(COOKIES_FILE)} bytes")
    
    # Get yt-dlp version
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
        print(f"📦 yt-dlp version: {result.stdout.strip()}")
    except:
        print("📦 yt-dlp version: unknown")
    
    print("="*50)
    app.run(host='0.0.0.0', port=port)
