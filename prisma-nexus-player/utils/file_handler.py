import os
import json
from pathlib import Path
import mimetypes

class FileHandler:
    def __init__(self):
        self.supported_formats = {
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'],
            'playlist': ['.m3u', '.m3u8', '.pls']
        }
        
    def scan_directory(self, directory_path):
        """Scan directory for media files"""
        media_files = []
        try:
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    media_type = self.get_media_type(file)
                    if media_type:
                        file_path = os.path.join(root, file)
                        media_files.append({
                            'name': file,
                            'path': file_path,
                            'type': media_type,
                            'size': os.path.getsize(file_path),
                            'extension': ext
                        })
        except Exception as e:
            print(f"Error scanning directory: {e}")
        
        return {'files': media_files, 'total': len(media_files)}
    
    def get_media_type(self, filename):
        """Determine media type from filename"""
        ext = os.path.splitext(filename)[1].lower()
        for media_type, extensions in self.supported_formats.items():
            if ext in extensions:
                return media_type
        return None
    
    def is_supported(self, filename):
        """Check if file is supported"""
        return self.get_media_type(filename) is not None
    
    def get_metadata(self, file_path):
        """Extract metadata from media file"""
        metadata = {
            'filename': os.path.basename(file_path),
            'size': os.path.getsize(file_path),
            'type': self.get_media_type(file_path)
        }
        
        try:
            if metadata['type'] == 'audio':
                from mutagen import File
                audio = File(file_path)
                if audio:
                    metadata['duration'] = audio.info.length if hasattr(audio.info, 'length') else 0
                    metadata['bitrate'] = audio.info.bitrate if hasattr(audio.info, 'bitrate') else 0
        except:
            pass
        
        return metadata