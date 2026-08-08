import os
import sys
import json
import time
import threading
import subprocess
import socket
import mimetypes
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Create Flask app
app = Flask(__name__, static_folder='static', template_folder='static')
CORS(app)

# Global state
is_playing = False
current_file_path = None
current_file_type = None
playlist = []
current_index = -1
current_volume = 100

# Get the user's home directory
HOME_DIR = str(Path.home())
MUSIC_DIR = os.path.join(HOME_DIR, 'Music')
VIDEOS_DIR = os.path.join(HOME_DIR, 'Videos')
DOWNLOADS_DIR = os.path.join(HOME_DIR, 'Downloads')
DESKTOP_DIR = os.path.join(HOME_DIR, 'Desktop')

# Create temp directory for thumbnails if needed
os.makedirs('static', exist_ok=True)

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/status')
def status():
    """Return current player status"""
    global is_playing, current_file_path, playlist, current_index, current_file_type, current_volume
    return jsonify({
        'playing': is_playing,
        'current_file': os.path.basename(current_file_path) if current_file_path else None,
        'current_path': current_file_path,
        'current_type': current_file_type,
        'playlist_length': len(playlist),
        'current_index': current_index,
        'volume': current_volume
    })

@app.route('/api/play-file', methods=['POST'])
def play_file():
    """Mark a file for playback (actual playback happens in browser)"""
    global is_playing, current_file_path, current_file_type
    
    try:
        data = request.json
        file_path = data.get('path', '')
        
        print(f"🎵 Request to play: {file_path}")
        
        # Check if file exists
        if not file_path or not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return jsonify({
                'status': 'error',
                'message': f'File not found: {file_path}'
            })
        
        # Determine file type
        file_type = get_file_type(file_path)
        current_file_type = file_type
        current_file_path = file_path
        is_playing = True
        
        return jsonify({
            'status': 'success',
            'file': os.path.basename(file_path),
            'path': file_path,
            'type': file_type,
            'size': os.path.getsize(file_path),
            'playing': True
        })
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/media/<path:encoded_path>')
def serve_media(encoded_path):
    """Serve media files for browser playback"""
    try:
        # Decode the path
        file_path = encoded_path
        if not os.path.isabs(file_path):
            file_path = '/' + file_path
        
        # Handle Windows drive letters
        if len(file_path) > 2 and file_path[1] == ':':
            file_path = file_path[0].upper() + ':' + file_path[2:]
        
        print(f"📁 Serving media: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return jsonify({'error': 'File not found'}), 404
        
        # Get file size for range requests
        file_size = os.path.getsize(file_path)
        range_header = request.headers.get('Range', None)
        
        if range_header:
            # Handle range requests for video seeking
            byte1, byte2 = 0, None
            range_match = range_header.replace('bytes=', '').split('-')
            byte1 = int(range_match[0])
            if range_match[1]:
                byte2 = int(range_match[1])
            
            if byte2 is None:
                byte2 = file_size - 1
            
            length = byte2 - byte1 + 1
            
            with open(file_path, 'rb') as f:
                f.seek(byte1)
                data = f.read(length)
            
            rv = Response(data, 
                         206,
                         mimetype=get_mime_type(file_path),
                         direct_passthrough=True)
            rv.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{file_size}')
            rv.headers.add('Accept-Ranges', 'bytes')
            rv.headers.add('Content-Length', str(length))
            return rv
        else:
            # Send entire file
            return send_file(
                file_path,
                mimetype=get_mime_type(file_path),
                as_attachment=False,
                conditional=True
            )
            
    except Exception as e:
        print(f"❌ Error serving media: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_playback():
    """Stop current playback"""
    global is_playing, current_file_path, current_file_type
    
    is_playing = False
    current_file_path = None
    current_file_type = None
    
    return jsonify({
        'status': 'success',
        'message': 'Playback stopped'
    })

@app.route('/api/volume', methods=['POST'])
def set_volume():
    """Set volume level"""
    global current_volume
    
    try:
        data = request.json
        volume = int(data.get('volume', 100))
        current_volume = volume
        
        return jsonify({
            'status': 'success',
            'volume': volume
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/scan-directory', methods=['POST'])
def scan_directory():
    """Scan a directory for media files"""
    global playlist
    
    try:
        data = request.json
        directory = data.get('path', HOME_DIR)
        
        if not os.path.exists(directory):
            return jsonify({
                'status': 'error',
                'message': 'Directory not found'
            })
        
        files = []
        extensions = {
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.webm', '.flv',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'
        }
        
        for root, dirs, filenames in os.walk(directory):
            depth = root[len(directory):].count(os.sep)
            if depth > 2:
                continue
            
            for filename in filenames:
                if Path(filename).suffix.lower() in extensions:
                    filepath = os.path.join(root, filename)
                    try:
                        stat = os.stat(filepath)
                        files.append({
                            'name': filename,
                            'path': filepath,
                            'size': stat.st_size,
                            'type': get_file_type(filename),
                            'modified': stat.st_mtime
                        })
                    except:
                        pass
            
            if len(files) >= 200:
                break
        
        files.sort(key=lambda x: x['name'].lower())
        playlist = files
        
        return jsonify({
            'status': 'success',
            'files': files[:200],
            'total': len(files),
            'directory': directory
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/get-playlist', methods=['GET'])
def get_playlist():
    """Get current playlist"""
    global playlist, current_index
    return jsonify({
        'status': 'success',
        'playlist': playlist,
        'current_index': current_index
    })

@app.route('/api/get-common-dirs', methods=['GET'])
def get_common_dirs():
    """Get common directories"""
    dirs = [
        {'name': 'Music', 'path': MUSIC_DIR, 'exists': os.path.exists(MUSIC_DIR)},
        {'name': 'Videos', 'path': VIDEOS_DIR, 'exists': os.path.exists(VIDEOS_DIR)},
        {'name': 'Downloads', 'path': DOWNLOADS_DIR, 'exists': os.path.exists(DOWNLOADS_DIR)},
        {'name': 'Desktop', 'path': DESKTOP_DIR, 'exists': os.path.exists(DESKTOP_DIR)},
        {'name': 'Home', 'path': HOME_DIR, 'exists': os.path.exists(HOME_DIR)}
    ]
    
    return jsonify({
        'status': 'success',
        'directories': dirs
    })

def get_file_type(filename):
    """Determine file type from extension"""
    ext = Path(filename).suffix.lower()
    
    audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
    video_exts = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.webm', '.flv'}
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
    
    if ext in audio_exts:
        return 'audio'
    elif ext in video_exts:
        return 'video'
    elif ext in image_exts:
        return 'image'
    return 'unknown'

def get_mime_type(filepath):
    """Get MIME type for a file"""
    ext = Path(filepath).suffix.lower()
    mime_types = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.avi': 'video/x-msvideo',
        '.mkv': 'video/x-matroska',
        '.mov': 'video/quicktime',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.flac': 'audio/flac',
        '.ogg': 'audio/ogg',
        '.aac': 'audio/aac',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'application/octet-stream')

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    
    local_ip = get_local_ip()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         🔮 PrismaNexus Player (PNP) v2.0 🔮                 ║
║         Built-in Video & Audio Player                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"✅ Server starting...")
    print(f"📡 Local:    http://127.0.0.1:5000")
    print(f"🌐 Network:  http://{local_ip}:5000")
    print(f"\n✨ Opening browser...")
    print(f"🛑 Press Ctrl+C to stop\n")
    
    def open_browser():
        time.sleep(1.5)
        import webbrowser
        webbrowser.open('http://127.0.0.1:5000')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")