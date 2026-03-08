from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

COOKIES_FILE = "cookies.txt"

@app.route('/')
def home():
    return jsonify({
        'name': 'YouTube API Server',
        'version': '3.0',
        'status': 'running',
        'port': os.environ.get('PORT', 8080),
        'cookies_exists': os.path.exists(COOKIES_FILE),
        'endpoints': {
            '/': 'This info',
            '/health': 'Health check',
            '/title': 'Get video title - ?url=YOUTUBE_URL'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    cookies_exists = os.path.exists(COOKIES_FILE)
    cookies_size = os.path.getsize(COOKIES_FILE) if cookies_exists else 0
    
    return jsonify({
        'status': 'ok',
        'cookies': {
            'exists': cookies_exists,
            'size': cookies_size
        },
        'time': datetime.now().isoformat()
    })

@app.route('/title', methods=['GET'])
def get_title():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    logger.info(f"Fetching: {url}")
    
    # Check cookies first
    if not os.path.exists(COOKIES_FILE):
        return jsonify({'error': 'Cookies file not found on server'}), 500
    
    # Advanced yt-dlp options
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'cookiefile': COOKIES_FILE,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'format': 'best[height<=720]',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({'error': 'No info found'}), 404
            
            # Extract all possible title fields
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
                'duration': info.get('duration', 0),
                'cookies_used': os.path.exists(COOKIES_FILE)
            })
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        logger.error(f"DownloadError: {error_msg}")
        
        if 'Sign in' in error_msg:
            return jsonify({'error': 'Login required - cookies expired'}), 403
        elif 'Video unavailable' in error_msg:
            return jsonify({'error': 'Video unavailable'}), 404
        else:
            return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("="*50)
    print("🚀 YouTube API Server v3.0")
    print("="*50)
    print(f"📡 Port: {port}")
    print(f"🍪 Cookies: {'✅ Found' if os.path.exists(COOKIES_FILE) else '❌ Not found'}")
    if os.path.exists(COOKIES_FILE):
        print(f"📦 Size: {os.path.getsize(COOKIES_FILE)} bytes")
    print("="*50)
    app.run(host='0.0.0.0', port=port)
