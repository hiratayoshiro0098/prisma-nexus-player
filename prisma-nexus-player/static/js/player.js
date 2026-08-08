// PrismaNexus Player - Main Player Logic
const socket = io();

class PrismaNexusPlayer {
    constructor() {
        this.isPlaying = false;
        this.volume = 100;
        this.maxVolume = 300;
        this.currentFile = null;
        this.playlist = [];
        this.currentIndex = -1;
        
        this.initializeElements();
        this.initializeEvents();
        this.initializeSocket();
    }
    
    initializeElements() {
        this.btnPlay = document.getElementById('btnPlay');
        this.btnPrevious = document.getElementById('btnPrevious');
        this.btnNext = document.getElementById('btnNext');
        this.btnShuffle = document.getElementById('btnShuffle');
        this.btnRepeat = document.getElementById('btnRepeat');
        this.volumeSlider = document.getElementById('volumeSlider');
        this.volumeValue = document.getElementById('volumeValue');
        this.progressBar = document.getElementById('progressBar');
        this.progressFill = document.getElementById('progressFill');
        this.progressHandle = document.getElementById('progressHandle');
        this.fileList = document.getElementById('fileList');
        this.nowPlaying = document.getElementById('nowPlaying');
        this.visualizer = document.getElementById('visualizer');
    }
    
    initializeEvents() {
        // Play/Pause
        this.btnPlay.addEventListener('click', () => this.togglePlay());
        
        // Navigation
        this.btnPrevious.addEventListener('click', () => this.playPrevious());
        this.btnNext.addEventListener('click', () => this.playNext());
        
        // Volume control
        this.volumeSlider.addEventListener('input', (e) => this.setVolume(e.target.value));
        
        // Progress bar
        this.progressBar.addEventListener('click', (e) => this.seek(e));
        
        // File drag and drop
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => {
            e.preventDefault();
            const files = e.dataTransfer.files;
            this.handleDroppedFiles(files);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        
        // Window controls
        document.getElementById('btnClose').addEventListener('click', () => window.close());
        document.getElementById('btnMinimize').addEventListener('click', () => {
            // Implement minimize logic
        });
        document.getElementById('btnMaximize').addEventListener('click', () => {
            // Implement maximize logic
        });
    }
    
    initializeSocket() {
        socket.on('connected', (data) => {
            console.log('Connected to server:', data);
        });
        
        socket.on('media_playing', (data) => {
            this.updateNowPlaying(data);
        });
    }
    
    togglePlay() {
        if (!this.currentFile) {
            this.openFileDialog();
            return;
        }
        
        this.isPlaying = !this.isPlaying;
        this.btnPlay.innerHTML = this.isPlaying ? '⏸' : '▶';
        
        if (this.isPlaying) {
            this.startVisualizer();
        } else {
            this.stopVisualizer();
        }
    }
    
    async openFileDialog() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'audio/*,video/*,image/*';
        input.multiple = true;
        
        input.onchange = (e) => {
            const files = Array.from(e.target.files);
            this.addFilesToPlaylist(files);
            if (files.length > 0) {
                this.playFile(files[0]);
            }
        };
        
        input.click();
    }
    
    addFilesToPlaylist(files) {
        files.forEach(file => {
            this.playlist.push({
                name: file.name,
                path: URL.createObjectURL(file),
                type: this.getMediaType(file.name)
            });
        });
        
        this.updatePlaylistUI();
    }
    
    getMediaType(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const audioExts = ['mp3', 'wav', 'flac', 'aac', 'ogg'];
        const videoExts = ['mp4', 'avi', 'mkv', 'mov', 'webm'];
        const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
        
        if (audioExts.includes(ext)) return 'audio';
        if (videoExts.includes(ext)) return 'video';
        if (imageExts.includes(ext)) return 'image';
        return 'unknown';
    }
    
    playFile(file) {
        this.currentFile = file;
        this.isPlaying = true;
        this.btnPlay.innerHTML = '⏸';
        
        this.updateNowPlaying({
            file: file.name,
            type: file.type || this.getMediaType(file.name)
        });
        
        // Send to backend
        fetch('/api/play', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: file.path })
        });
        
        this.startVisualizer();
    }
    
    updateNowPlaying(data) {
        this.nowPlaying.innerHTML = `
            <div class="playing-info">
                <div class="file-icon">${this.getFileIcon(data.type)}</div>
                <div class="file-details">
                    <h3>${data.file}</h3>
                    <span class="file-type">${data.type}</span>
                </div>
            </div>
        `;
    }
    
    getFileIcon(type) {
        const icons = {
            'audio': '🎵',
            'video': '🎬',
            'image': '🖼️',
            'unknown': '📄'
        };
        return icons[type] || icons.unknown;
    }
    
    setVolume(value) {
        this.volume = value;
        this.volumeValue.textContent = `${value}%`;
        
        fetch('/api/volume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ volume: value })
        });
    }
    
    playPrevious() {
        if (this.playlist.length === 0) return;
        this.currentIndex = (this.currentIndex - 1 + this.playlist.length) % this.playlist.length;
        this.playFile(this.playlist[this.currentIndex]);
    }
    
    playNext() {
        if (this.playlist.length === 0) return;
        this.currentIndex = (this.currentIndex + 1) % this.playlist.length;
        this.playFile(this.playlist[this.currentIndex]);
    }
    
    seek(event) {
        const rect = this.progressBar.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const width = rect.width;
        const percentage = (x / width) * 100;
        
        this.progressFill.style.width = `${percentage}%`;
        this.progressHandle.style.left = `${percentage}%`;
        
        socket.emit('seek', { position: percentage / 100 });
    }
    
    handleDroppedFiles(files) {
        const mediaFiles = Array.from(files).filter(file => {
            const type = this.getMediaType(file.name);
            return type !== 'unknown';
        });
        
        this.addFilesToPlaylist(mediaFiles);
        if (mediaFiles.length > 0 && !this.currentFile) {
            this.playFile(mediaFiles[0]);
        }
    }
    
    handleKeyboardShortcuts(event) {
        switch(event.code) {
            case 'Space':
                event.preventDefault();
                this.togglePlay();
                break;
            case 'ArrowLeft':
                event.preventDefault();
                this.seek({ clientX: this.progressBar.getBoundingClientRect().left });
                break;
            case 'ArrowRight':
                event.preventDefault();
                this.seek({ clientX: this.progressBar.getBoundingClientRect().right });
                break;
            case 'ArrowUp':
                event.preventDefault();
                this.setVolume(Math.min(this.maxVolume, this.volume + 5));
                break;
            case 'ArrowDown':
                event.preventDefault();
                this.setVolume(Math.max(0, this.volume - 5));
                break;
        }
    }
    
    updatePlaylistUI() {
        const playlist = document.getElementById('playlist');
        playlist.innerHTML = this.playlist.map((file, index) => `
            <div class="playlist-item ${index === this.currentIndex ? 'active' : ''}" 
                 onclick="player.playFileFromPlaylist(${index})">
                <span class="playlist-icon">${this.getFileIcon(file.type)}</span>
                <span class="playlist-name">${file.name}</span>
                <span class="playlist-type">${file.type}</span>
            </div>
        `).join('');
    }
    
    playFileFromPlaylist(index) {
        this.currentIndex = index;
        this.playFile(this.playlist[index]);
    }
    
    startVisualizer() {
        // Audio visualizer animation
        const visualizer = this.visualizer;
        visualizer.innerHTML = '';
        
        for (let i = 0; i < 20; i++) {
            const bar = document.createElement('div');
            bar.className = 'visualizer-bar';
            bar.style.cssText = `
                width: 3px;
                background: linear-gradient(to top, var(--accent), var(--accent2));
                border-radius: 2px;
                position: absolute;
                bottom: 0;
                left: ${5 + i * 5}%;
                animation: equalizer ${0.5 + Math.random()}s ease infinite alternate;
            `;
            visualizer.appendChild(bar);
        }
    }
    
    stopVisualizer() {
        this.visualizer.innerHTML = '';
    }
    
    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('hidden', content.id !== `tab-${tabName}`);
        });
    }
}

// Initialize player
const player = new PrismaNexusPlayer();