import os
import sys
import subprocess
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import webbrowser
import threading
import socket

# Try to import optional dependencies
try:
    import vlc
    VLC_AVAILABLE = True
except:
    VLC_AVAILABLE = False
    print("Warning: python-vlc not available. Using system VLC player.")

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except:
    PILLOW_AVAILABLE = False

class PrismaNexusPlayer:
    def __init__(self):
        self.app = Flask(__name__, 
                        static_folder='static',
                        template_folder='static')
        CORS(self.app)
        self.app.config['SECRET_KEY'] = 'prisma-nexus-secret-key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Player state
        self.current_file = None
        self.is_playing = False
        self.volume = 100
        self.max_volume = 300
        self.vlc_process = None
        
        # Supported formats
        self.supported_audio = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
        self.supported_video = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
        self.supported_image = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        
        # Setup routes
        self.setup_routes()
        self.setup_socket_events()
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return send_from_directory('static', 'index.html')
        
        @self.app.route('/api/play', methods=['POST'])
        def play_media():
            try:
                data = request.json
                file_path = data.get('path', '')
                
                if file_path and os.path.exists(file_path):
                    self.current_file = file_path
                    self.play_with_vlc(file_path)
                    self.is_playing = True
                    
                    return jsonify({
                        'status': 'success',
                        'file': os.path.basename(file_path),
                        'type': self.get_media_type(file_path)
                    })
                
                return jsonify({'status': 'error', 'message': 'File not found'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)})
        
        @self.app.route('/api/stop', methods=['POST'])
        def stop_media():
            self.stop_playback()
            return jsonify({'status': 'success'})
        
        @self.app.route('/api/volume', methods=['POST'])
        def set_volume():
            data = request.json
            self.volume = min(int(data.get('volume', 100)), self.max_volume)
            
            # Adjust VLC volume if running
            if self.vlc_process and self.vlc_process.poll() is None:
                # Send volume command to VLC
                pass
            
            return jsonify({'status': 'success', 'volume': self.volume})
        
        @self.app.route('/api/scan', methods=['GET'])
        def scan_files():
            directory = request.args.get('path', str(Path.home() / 'Music'))
            return jsonify(self.scan_directory(directory))
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            return jsonify({
                'playing': self.is_playing,
                'current_file': os.path.basename(self.current_file) if self.current_file else None,
                'volume': self.volume,
                'supported_formats': {
                    'audio': list(self.supported_audio),
                    'video': list(self.supported_video),
                    'image': list(self.supported_image)
                }
            })
        
        @self.app.route('/static/<path:filename>')
        def serve_static(filename):
            return send_from_directory('static', filename)
    
    def setup_socket_events(self):
        @self.socketio.on('connect')
        def handle_connect():
            emit('status', {
                'connected': True,
                'playing': self.is_playing,
                'volume': self.volume
            })
        
        @self.socketio.on('control')
        def handle_control(data):
            action = data.get('action')
            
            if action == 'play_pause':
                self.toggle_play_pause()
            elif action == 'stop':
                self.stop_playback()
            elif action == 'volume':
                self.volume = min(int(data.get('value', 100)), self.max_volume)
                self.adjust_vlc_volume()
            
            emit('status', {
                'playing': self.is_playing,
                'volume': self.volume
            })
    
    def play_with_vlc(self, file_path):
        """Play media using system VLC player"""
        try:
            # Stop any existing playback
            self.stop_playback()
            
            # Start VLC with specific parameters
            vlc_path = self.find_vlc()
            if not vlc_path:
                # Try using python-vlc if available
                if VLC_AVAILABLE:
                    self.play_with_python_vlc(file_path)
                else:
                    raise Exception("VLC not found. Please install VLC Media Player.")
                return
            
            # Launch VLC process
            cmd = [
                vlc_path,
                file_path,
                '--play-and-exit',
                '--volume', str(int(self.volume * 1.28)),  # VLC uses 0-128 scale
                '--no-video-title-show',
                '--intf', 'qt',  # Use Qt interface
            ]
            
            self.vlc_process = subprocess.Popen(cmd)
            self.is_playing = True
            
        except Exception as e:
            print(f"Error playing media: {e}")
            self.is_playing = False
    
    def find_vlc(self):
        """Find VLC executable path"""
        possible_paths = [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
            "/usr/bin/vlc",
            "/usr/local/bin/vlc",
            "/Applications/VLC.app/Contents/MacOS/VLC"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Try to find vlc in PATH
        try:
            result = subprocess.run(['where', 'vlc'] if sys.platform == 'win32' else ['which', 'vlc'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return None
    
    def play_with_python_vlc(self, file_path):
        """Alternative playback using python-vlc library"""
        try:
            import vlc
            instance = vlc.Instance()
            player = instance.media_player_new()
            media = instance.media_new(file_path)
            player.set_media(media)
            player.play()
            
            # Store player reference
            self.python_vlc_player = player
            self.is_playing = True
            
        except Exception as e:
            print(f"Error with python-vlc: {e}")
    
    def stop_playback(self):
        """Stop current playback"""
        self.is_playing = False
        
        if self.vlc_process:
            try:
                self.vlc_process.terminate()
                self.vlc_process.wait(timeout=5)
            except:
                try:
                    self.vlc_process.kill()
                except:
                    pass
            self.vlc_process = None
    
    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if self.vlc_process:
            # Send space key to VLC window (simplified)
            pass
        self.is_playing = not self.is_playing
    
    def adjust_vlc_volume(self):
        """Adjust VLC volume"""
        # This would need platform-specific implementation
        pass
    
    def get_media_type(self, file_path):
        """Determine media type from file extension"""
        ext = Path(file_path).suffix.lower()
        
        if ext in self.supported_audio:
            return 'audio'
        elif ext in self.supported_video:
            return 'video'
        elif ext in self.supported_image:
            return 'image'
        return 'unknown'
    
    def scan_directory(self, directory):
        """Scan directory for media files"""
        media_files = []
        
        try:
            for root, dirs, files in os.walk(directory):
                # Limit depth
                depth = root[len(directory):].count(os.sep)
                if depth > 3:
                    continue
                
                for file in files:
                    ext = Path(file).suffix.lower()
                    all_supported = self.supported_audio | self.supported_video | self.supported_image
                    
                    if ext in all_supported:
                        file_path = os.path.join(root, file)
                        media_type = self.get_media_type(file_path)
                        
                        try:
                            size = os.path.getsize(file_path)
                        except:
                            size = 0
                        
                        media_files.append({
                            'name': file,
                            'path': file_path,
                            'type': media_type,
                            'size': size,
                            'extension': ext
                        })
            
            # Sort by name
            media_files.sort(key=lambda x: x['name'].lower())
            
        except Exception as e:
            print(f"Error scanning directory: {e}")
        
        return {
            'files': media_files,
            'total': len(media_files),
            'directory': directory
        }
    
    def run(self, host='127.0.0.1', port=5000):
        """Run the application"""
        print(f"""
{'='*60}
  PrismaNexus Player (PNP) v1.0
  Running on http://{host}:{port}
  Press Ctrl+C to exit
{'='*60}
        """)
        
        # Open browser automatically
        threading.Timer(1.5, lambda: webbrowser.open(f'http://{host}:{port}')).start()
        
        # Start Flask-SocketIO
        self.socketio.run(self.app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    player = PrismaNexusPlayer()
    player.run()