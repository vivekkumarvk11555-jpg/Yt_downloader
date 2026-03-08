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
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            '/': 'API Info',
            '/health': 'Health check',
            '/title': 'Get video title - ?url=YOUTUBE_URL'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    cookies_exists = os.path.exists(COOKIES_FILE)
    return jsonify({
        'status': 'ok',
        'cookies': cookies_exists,
        'time': datetime.now().isoformat()
    })

@app.route('/title', methods=['GET'])
def get_title():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    logger.info(f"Fetching: {url}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({'error': 'No info found'}), 404
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'Unknown'),
                'uploader': info.get('uploader', 'Unknown')
            })
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
