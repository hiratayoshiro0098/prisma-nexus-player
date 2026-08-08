import sys
import os
import vlc
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
from scipy import signal
import librosa
import soundfile as sf

class PrismaNexusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrismaNexus Player (PNP)")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(self.get_stylesheet())
        
        # Initialize VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.media_player = self.instance.media_player_new()
        
        # Audio enhancement settings
        self.volume = 100
        self.max_volume = 300
        self.equalizer_enabled = False
        self.ai_enhancement = False
        
        self.setup_ui()
        self.setup_connections()
        
    def get_stylesheet(self):
        return """
        QMainWindow {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        QPushButton {
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            padding: 10px;
            color: white;
            font-weight: bold;
        }
        QPushButton:hover {
            background: rgba(255, 255, 255, 0.2);
            border-color: rgba(255, 255, 255, 0.4);
        }
        QSlider::groove:horizontal {
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: white;
            width: 18px;
            height: 18px;
            margin: -5px 0;
            border-radius: 9px;
        }
        """
    
    def setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("PrismaNexus Player")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; color: white; font-weight: bold;")
        layout.addWidget(title)
        
        # Video frame
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("""
            QFrame {
                background: black;
                border-radius: 15px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)
        self.video_frame.setMinimumHeight(400)
        layout.addWidget(self.video_frame)
        
        # Controls
        controls = QVBoxLayout()
        
        # Progress bar
        self.progress = QSlider(Qt.Horizontal)
        self.progress.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 10px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #FF6B6B;
                width: 20px;
                height: 20px;
                margin: -5px 0;
                border-radius: 10px;
            }
        """)
        controls.addWidget(self.progress)
        
        # Playback buttons
        btn_layout = QHBoxLayout()
        
        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶")
        self.btn_next = QPushButton("⏭")
        self.btn_stop = QPushButton("⏹")
        
        for btn in [self.btn_prev, self.btn_play, self.btn_next, self.btn_stop]:
            btn.setFixedSize(60, 60)
            btn_layout.addWidget(btn)
        
        controls.addLayout(btn_layout)
        
        # Volume control
        vol_layout = QHBoxLayout()
        vol_label = QLabel("🔊")
        vol_label.setStyleSheet("color: white; font-size: 20px;")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMaximum(300)
        self.volume_slider.setValue(100)
        self.volume_label = QLabel("100%")
        self.volume_label.setStyleSheet("color: white; font-weight: bold;")
        
        vol_layout.addWidget(vol_label)
        vol_layout.addWidget(self.volume_slider)
        vol_layout.addWidget(self.volume_label)
        controls.addLayout(vol_layout)
        
        # Enhancement buttons
        enhance_layout = QHBoxLayout()
        self.btn_ai_enhance = QPushButton("🧠 AI Enhance")
        self.btn_equalizer = QPushButton("🎚 Equalizer")
        self.btn_3d_audio = QPushButton("🔊 3D Audio")
        self.btn_network = QPushButton("📱 Network")
        
        for btn in [self.btn_ai_enhance, self.btn_equalizer, self.btn_3d_audio, self.btn_network]:
            enhance_layout.addWidget(btn)
        
        controls.addLayout(enhance_layout)
        layout.addLayout(controls)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - PrismaNexus Player")
        
    def setup_connections(self):
        self.btn_play.clicked.connect(self.play_pause)
        self.btn_stop.clicked.connect(self.stop)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.progress.sliderMoved.connect(self.set_position)
        self.btn_ai_enhance.clicked.connect(self.toggle_ai_enhancement)
        self.btn_network.clicked.connect(self.show_network_panel)
        
    def play_pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.btn_play.setText("▶")
        else:
            self.player.play()
            self.btn_play.setText("⏸")
    
    def stop(self):
        self.player.stop()
        self.btn_play.setText("▶")
    
    def change_volume(self, value):
        self.volume = value
        self.volume_label.setText(f"{value}%")
        self.player.audio_set_volume(value)
    
    def set_position(self, position):
        self.player.set_position(position / 1000.0)
    
    def toggle_ai_enhancement(self):
        self.ai_enhancement = not self.ai_enhancement
        if self.ai_enhancement:
            self.btn_ai_enhance.setStyleSheet("background: #4CAF50;")
            self.status_bar.showMessage("AI Enhancement ON")
        else:
            self.btn_ai_enhance.setStyleSheet("")
            self.status_bar.showMessage("AI Enhancement OFF")
    
    def show_network_panel(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Network Devices")
        dialog.setGeometry(200, 200, 400, 300)
        dialog.setStyleSheet("background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);")
        
        layout = QVBoxLayout()
        label = QLabel("Connected Devices")
        label.setStyleSheet("color: white; font-size: 18px;")
        layout.addWidget(label)
        
        list_widget = QListWidget()
        list_widget.setStyleSheet("background: rgba(255,255,255,0.1); color: white;")
        layout.addWidget(list_widget)
        
        btn_scan = QPushButton("Scan Network")
        btn_connect = QPushButton("Connect")
        layout.addWidget(btn_scan)
        layout.addWidget(btn_connect)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Media File",
            "",
            "All Supported Files (*.mp3 *.mp4 *.avi *.mkv *.flac *.wav *.jpg *.png *.gif);;"
            "Audio Files (*.mp3 *.flac *.wav);;"
            "Video Files (*.mp4 *.avi *.mkv);;"
            "Image Files (*.jpg *.png *.gif)"
        )
        
        if file_path:
            self.play_media(file_path)
    
    def play_media(self, file_path):
        media = self.instance.media_new(file_path)
        self.player.set_media(media)
        self.player.play()
        self.status_bar.showMessage(f"Playing: {os.path.basename(file_path)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PrismaNexusWindow()
    window.show()
    sys.exit(app.exec_())