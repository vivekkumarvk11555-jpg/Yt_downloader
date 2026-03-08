from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

COOKIES_FILE = "cookies.txt"

@app.route('/')
def home():
    return jsonify({'status': 'running'})

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'cookies': os.path.exists(COOKIES_FILE)
    })

@app.route('/title')
def get_title():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        # Simple yt-dlp options
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'Unknown'),
                'uploader': info.get('uploader', 'Unknown')
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Server on port {port}")
    app.run(host='0.0.0.0', port=port)
