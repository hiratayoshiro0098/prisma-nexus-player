import sys
import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import subprocess
import webbrowser
import socket
from pathlib import Path

# Import custom modules
from utils.file_handler import FileHandler
from utils.ai_enhancer import AIEnhancer
from utils.network_manager import NetworkManager

class PrismaNexusPlayer:
    def __init__(self):
        self.app = Flask(__name__, 
                        static_folder='static',
                        template_folder='static')
        CORS(self.app)
        self.app.config['SECRET_KEY'] = 'prisma-nexus-secret-key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Initialize components
        self.file_handler = FileHandler()
        self.ai_enhancer = AIEnhancer()
        self.network_manager = NetworkManager()
        
        # VLC instance
        self.vlc_instance = None
        self.current_media = None
        
        # Audio settings
        self.volume = 100
        self.max_volume = 300
        
        # Setup routes
        self.setup_routes()
        self.setup_socket_events()
        
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/api/play', methods=['POST'])
        def play_media():
            data = request.json
            file_path = data.get('path')
            if file_path and os.path.exists(file_path):
                self.play_media_file(file_path)
                return jsonify({'status': 'success', 'file': os.path.basename(file_path)})
            return jsonify({'status': 'error', 'message': 'File not found'})
        
        @self.app.route('/api/volume', methods=['POST'])
        def set_volume():
            data = request.json
            volume = data.get('volume', 100)
            self.volume = min(volume, self.max_volume)
            return jsonify({'status': 'success', 'volume': self.volume})
        
        @self.app.route('/api/ai/enhance', methods=['POST'])
        def ai_enhance_audio():
            data = request.json
            effect = data.get('effect', 'clear')
            result = self.ai_enhancer.apply_effect(self.current_media, effect)
            return jsonify(result)
        
        @self.app.route('/api/files/scan', methods=['GET'])
        def scan_files():
            path = request.args.get('path', str(Path.home()))
            files = self.file_handler.scan_directory(path)
            return jsonify(files)
        
        @self.app.route('/api/network/status', methods=['GET'])
        def network_status():
            status = self.network_manager.get_status()
            return jsonify(status)
        
        @self.app.route('/api/network/discover', methods=['GET'])
        def discover_devices():
            devices = self.network_manager.discover_devices()
            return jsonify(devices)
        
        @self.app.route('/api/network/connect', methods=['POST'])
        def connect_device():
            data = request.json
            device_ip = data.get('ip')
            result = self.network_manager.connect_to_device(device_ip)
            return jsonify(result)
        
    def setup_socket_events(self):
        @self.socketio.on('connect')
        def handle_connect():
            emit('connected', {'status': 'connected'})
        
        @self.socketio.on('seek')
        def handle_seek(data):
            position = data.get('position', 0)
            if self.vlc_instance:
                self.vlc_instance.set_position(position)
        
        @self.socketio.on('sync_playback')
        def handle_sync(data):
            if self.network_manager.connected_devices:
                self.network_manager.sync_playback(data)
        
    def play_media_file(self, file_path):
        """Play media using VLC backend"""
        try:
            if self.vlc_instance:
                self.vlc_instance.stop()
            
            # Create VLC instance with enhanced settings
            vlc_args = [
                '--intf', 'dummy',
                '--vout', 'dummy',
                '--no-video-title-show',
                '--no-snapshot-preview',
                '--audio-resampler', 'soxr',
                '--volume-save'
            ]
            
            self.vlc_instance = subprocess.Popen(
                ['vlc', file_path] + vlc_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.current_media = file_path
            self.socketio.emit('media_playing', {
                'file': os.path.basename(file_path),
                'type': self.file_handler.get_media_type(file_path)
            })
            
        except Exception as e:
            print(f"Error playing media: {e}")
    
    def run(self, host='127.0.0.1', port=5000):
        """Run the application"""
        print(f"\n{'='*50}")
        print(f"  PrismaNexus Player (PNP)")
        print(f"  Running on http://{host}:{port}")
        print(f"  Press Ctrl+C to exit")
        print(f"{'='*50}\n")
        
        # Open browser automatically
        webbrowser.open(f'http://{host}:{port}')
        
        # Start Flask-SocketIO
        self.socketio.run(self.app, host=host, port=port, debug=False)

if __name__ == '__main__':
    player = PrismaNexusPlayer()
    player.run()