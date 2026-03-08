from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

COOKIES_FILE = "cookies.txt"

@app.route('/')
def home():
    return jsonify({
        'name': 'YouTube API',
        'version': '1.0',
        'status': 'running'
    })

@app.route('/health', methods=['GET'])
def health():
    cookies_exists = os.path.exists(COOKIES_FILE)
    return jsonify({
        'status': 'ok',
        'cookies': cookies_exists
    })

@app.route('/title', methods=['GET'])
def get_title():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    logger.info(f"Fetching: {url}")
    
    # CRITICAL FIX - Simple options, no format specification
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,  # Sirf basic info, formats nahi
        'ignoreerrors': True,
        'nocheckcertificate': True,
    }
    
    # Add cookies if exists
    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE
        logger.info(f"Using cookies: {os.path.getsize(COOKIES_FILE)} bytes")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({'error': 'No info found'}), 404
            
            # Extract title safely
            title = info.get('title') or info.get('fulltitle') or 'Unknown'
            uploader = info.get('uploader') or info.get('channel') or 'Unknown'
            
            return jsonify({
                'success': True,
                'title': title,
                'uploader': uploader
            })
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Server starting on port {port}")
    print(f"🍪 Cookies: {'✅ Found' if os.path.exists(COOKIES_FILE) else '❌ Not found'}")
    app.run(host='0.0.0.0', port=port)
